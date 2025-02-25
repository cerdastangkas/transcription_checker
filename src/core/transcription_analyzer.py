import pandas as pd
from pathlib import Path
import numpy as np
import re

def analyze_text_duration_ratio(video_id=None, min_words_per_second=0.5):
    """
    Analyze text length to duration ratio in transcriptions.
    Identifies segments that have too little text for their duration.
    
    Args:
        video_id (str, optional): Specific video ID to analyze. If None, analyzes all videos.
        min_words_per_second (float): Minimum expected words per second (default: 0.5)
    """
    reports_dir = Path('data/reports')
    if not reports_dir.exists():
        print(f"Error: Reports directory not found at {reports_dir}")
        return
        
    # Get list of video directories to process
    if video_id:
        video_dirs = [reports_dir / video_id]
        if not video_dirs[0].exists():
            print(f"Error: Video directory not found for {video_id}")
            return
    else:
        video_dirs = [d for d in reports_dir.iterdir() if d.is_dir()]
        
    def count_words(text):
        if not isinstance(text, str):
            return 0
        # Split by whitespace and filter out empty strings
        words = [w for w in re.split(r'\s+', text.strip()) if w]
        return len(words)
        
    def analyze_csv(csv_file):
        print(f"\nAnalyzing {csv_file.name}")
        df = pd.read_csv(csv_file)
        
        # Check required columns
        required_columns = ['text', 'end_time_seconds', 'start_time_seconds']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Skipping file: Missing required columns: {missing_columns}")
            return 0
            
        # Convert duration columns to numeric, replacing errors with NaN
        df['end_time_seconds'] = pd.to_numeric(df['end_time_seconds'], errors='coerce')
        df['start_time_seconds'] = pd.to_numeric(df['start_time_seconds'], errors='coerce')
        
        # Drop rows where duration calculation would be invalid
        valid_duration = df['end_time_seconds'].notna() & df['start_time_seconds'].notna()
        if not valid_duration.any():
            print("No valid duration data found in file")
            return 0
            
        # Calculate metrics only for valid rows
        df['word_count'] = df['text'].apply(count_words)
        df['duration'] = df['end_time_seconds'] - df['start_time_seconds']
        df['words_per_second'] = df['word_count'] / df['duration'].where(df['duration'] > 0)
        
        # Drop rows with invalid calculations
        df = df.dropna(subset=['words_per_second'])
        if len(df) == 0:
            print("No valid rows after calculating metrics")
            return 0
        
        # Calculate statistics
        avg_wps = df['words_per_second'].mean()
        std_wps = df['words_per_second'].std()
        
        # Identify suspicious segments
        suspicious = df[
            (df['words_per_second'] < min_words_per_second) & 
            (df['duration'] > 3)  # Only consider segments longer than 3 seconds
        ].copy()
        
        if len(suspicious) > 0:
            print(f"\nFound {len(suspicious)} suspicious segments:")
            print("\nTop 10 most suspicious segments (lowest words/second):")
            suspicious['suspicion_score'] = (min_words_per_second - suspicious['words_per_second']) * suspicious['duration']
            suspicious = suspicious.sort_values('suspicion_score', ascending=False)
            
            for _, row in suspicious.head(10).iterrows():
                print(f"\nTimestamp: {row['start_time_seconds']:.1f}s - {row['end_time_seconds']:.1f}s")
                print(f"Duration: {row['duration']:.1f}s")
                print(f"Words: {row['word_count']} ({row['words_per_second']:.2f} words/sec)")
                print(f"Text: {row['text']}")
                
            # Get indices of suspicious segments
            mask = suspicious.index
            
            # Initialize check_action column
            if 'check_action' not in df.columns:
                df['check_action'] = None
                print("Added check_action column")
                
            # Show current state
            print("\nBefore update:")
            current_state = df.iloc[mask][['text', 'words_per_second', 'duration']]
            current_state.insert(1, 'check_action', df.iloc[mask]['check_action'])
            print(current_state)
            
            # Update suspicious segments
            updates = 0
            for idx in mask:
                df.at[idx, 'check_action'] = 'delete'
                updates += 1
                
            # Save changes
            df.to_csv(csv_file, index=False)
            
            # Show final state
            print("\nAfter update:")
            final_state = df.iloc[mask][['text', 'words_per_second', 'duration']]
            final_state.insert(1, 'check_action', df.iloc[mask]['check_action'])
            print(final_state)
            print(f"\nMarked {updates} suspicious segments with check_action='delete'")
        else:
            print("No suspicious segments found")
            
        return len(suspicious)
        
    total_suspicious = 0
    for video_dir in video_dirs:
        csv_files = list(video_dir.glob('unusual_cases_*.csv'))
        if not csv_files:
            print(f"No unusual cases CSV files found for {video_dir.name}")
            continue
            
        # Process each CSV file
        for csv_file in csv_files:
            total_suspicious += analyze_csv(csv_file)
            
    print(f"\nAnalysis complete. Found {total_suspicious} total suspicious segments")
