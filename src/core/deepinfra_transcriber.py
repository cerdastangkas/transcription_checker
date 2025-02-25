import os
import time
import pandas as pd
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEEPINFRA_API_KEY = "nkSa4J45veOVqf9S9AqUTlDkRqqWPZCk"

# Configure session with retry logic
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=5,  # wait 20s, 40s, 80s between retries
        status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.headers.update({
        'Authorization': f'Bearer {DEEPINFRA_API_KEY}'
    })
    return session

def has_meaningful_content(text, duration_seconds=None):
    """Check if text contains actual words, not just punctuation or spaces.
    Also filters out segments that have less than 2 words AND duration > 2 seconds.
    
    Args:
        text (str): The text to check
        duration_seconds (float, optional): Duration of the audio segment in seconds
    
    Returns:
        bool: True if text has meaningful content, False otherwise
    """
    # Remove common punctuation and whitespace
    import re
    cleaned_text = re.sub(r'[.,!?;:\-\s]+', '', text.strip())
    
    # Basic check for non-empty content
    if len(cleaned_text) == 0:
        return False
        
    # Count words (split by whitespace after stripping punctuation)
    words = [w for w in re.sub(r'[.,!?;:\-]+', '', text.strip()).split() if w]
    word_count = len(words)
    
    # Check if text has actual words
    if word_count == 0:
        return False
    
    # If duration is provided, check for segments with few words but long duration
    if duration_seconds and duration_seconds > 2 and word_count <= 2:
        return False
        
    return True

def transcribe_audio_with_session(args):
    """Transcribe a single audio file using DeepInfra API with session."""
    session, file_path, model = args
    try:
        url = 'https://api.deepinfra.com/v1/openai/audio/transcriptions'
        
        if not os.path.exists(file_path):
            return False, file_path, f"File not found: {file_path}", 0.0
            
        # Print file info for debugging
        file_size = os.path.getsize(file_path)
        print(f"Transcribing {file_path} (size: {file_size} bytes)")
        
        with open(file_path, 'rb') as f:
            # Properly format multipart form data
            files = {
                'file': ('audio.wav', f, 'audio/wav'),
                'model': (None, model),
                'language': (None, 'id')
            }
            
            print(f"Making API request to {url}")
            response = session.post(url, files=files)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    text = json_response.get('text', '')
                    duration_seconds = json_response.get('duration', None)
                    print(f"Successfully got response: {json_response}")
                    
                    # Check if text has meaningful content
                    if not has_meaningful_content(text, duration_seconds):
                        return False, file_path, "Empty or meaningless text", 0.0
                        
                    return True, file_path, text, duration_seconds
                except Exception as e:
                    print(f"Error parsing JSON response: {str(e)}")
                    print(f"Raw response: {response.text}")
                    return False, file_path, f"Error parsing response: {str(e)}", 0.0
            elif response.status_code == 429:  # Rate limit
                print("Rate limit exceeded, waiting 5 seconds...")
                time.sleep(5)  # Wait 5 seconds before retry
                return False, file_path, "Rate limit exceeded", 0.0
            else:
                print(f"Error response: {response.text}")
                return False, file_path, f"Error {response.status_code}: {response.text}", 0.0
    except Exception as e:
        print(f"Exception in transcribe_audio_with_session: {str(e)}")
        return False, file_path, str(e)

def transcribe_unusual_cases(video_id, model='openai/whisper-large-v3', batch_size=3):
    """
    Transcribe audio files referenced in unusual cases CSV and update the text column.
    
    Args:
        video_id (str): ID of the video to process
        model (str): Model to use for transcription (default: openai/whisper-large-v3)
        batch_size (int): Number of concurrent transcription requests (default: 3)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Construct path to reports directory
        reports_dir = Path('data/reports') / video_id
        if not reports_dir.exists():
            print(f"Error: Reports directory not found for video {video_id}")
            return False
            
        # Find the most recent unusual cases CSV file
        csv_files = list(reports_dir.glob('unusual_cases_*.csv'))
        if not csv_files:
            print(f"Error: No unusual cases CSV files found for video {video_id}")
            return False
            
        latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
        
        # Read the CSV file
        df = pd.read_csv(latest_csv)
        if 'audio_file' not in df.columns:
            print("Error: CSV file does not contain 'audio_file' column")
            return False
            
        # Initialize check_action column if it doesn't exist
        if 'check_action' not in df.columns:
            df['check_action'] = None
            print("Added check_action column")
            
        # Create session for API calls
        session = create_session()
        
        # Collect files to transcribe
        to_transcribe = []
        skipped = 0
        for idx, row in df.iterrows():
            audio_file = row['audio_file']
            if not audio_file:
                continue
                
            # Skip if already marked as keep
            check_action = row.get('check_action')
            if check_action == 'keep':
                skipped += 1
                continue
                
            # Construct path to audio file in the audio directory
            if isinstance(audio_file, str):
                if audio_file.startswith('split/'):
                    audio_file = audio_file[6:]  # Remove 'split/' prefix
                audio_path = reports_dir / 'audio' / audio_file
                if not audio_path.exists():
                    print(f"Warning: Audio file not found: {audio_path}")
                    continue
                to_transcribe.append((idx, str(audio_path)))
                
        if skipped > 0:
            print(f"Skipped {skipped} files already marked as 'keep'")
        
        if not to_transcribe:
            print("No files to transcribe")
            return False
            
        print(f"Found {len(to_transcribe)} files to transcribe")
        updated_rows = 0
        
        # Process in batches
        from concurrent.futures import ThreadPoolExecutor
        
        for i in range(0, len(to_transcribe), batch_size):
            batch = to_transcribe[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1} of {(len(to_transcribe) + batch_size - 1)//batch_size}")
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = []
                for idx, audio_path in batch:
                    futures.append(executor.submit(transcribe_audio_with_session, (session, audio_path, model)))
                
                # Wait for all futures to complete
                for (idx, _), future in zip(batch, futures):
                    success, _, text, _ = future.result()
                    if success and has_meaningful_content(text):
                        # Update both text and check_action
                        df.at[idx, 'text'] = text
                        df.at[idx, 'check_action'] = 'keep'
                        updated_rows += 1
                        print(f"Successfully transcribed file {idx + 1} and marked as 'keep'")
                    else:
                        print(f"Warning: Failed to transcribe file {idx + 1}")
            
            # Save progress after each batch
            if updated_rows > 0:
                df.to_csv(latest_csv, index=False)
                print(f"Saved progress: {updated_rows} transcriptions so far")
                
            # # Wait between batches to avoid rate limits
            # if i + batch_size < len(to_transcribe):
            #     print("Waiting 10 seconds before next batch...")
            #     time.sleep(10)
        
        if updated_rows > 0:
            print(f"Successfully completed all transcriptions: {updated_rows} total")
            return True
        else:
            print("No transcriptions were updated")
            return False
            
    except Exception as e:
        print(f"Error processing unusual cases: {str(e)}")
        return False