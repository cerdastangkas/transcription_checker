import os
import pandas as pd
import logging
from pathlib import Path

def process_video(video_id):
    """
    Process a video's unusual cases:
    1. Remove rows marked for deletion and their audio files
    2. Update text content for rows marked as keep
    
    Args:
        video_id (str): ID of the video to process
    """
    try:
        # Setup paths
        base_dir = Path(__file__).resolve().parent.parent.parent
        reports_dir = base_dir / 'data' / 'reports' / video_id
        archive_dir = base_dir / 'data' / 'archive' / video_id
        
        # Check if files exist
        unusual_cases_file = list(reports_dir.glob('unusual_cases_*.csv'))
        if not unusual_cases_file:
            logging.error(f"No unusual cases file found for {video_id}")
            return
            
        transcript_file = archive_dir / f'{video_id}_transcripts.csv'
        if not transcript_file.exists():
            logging.error(f"No transcript file found for {video_id}")
            return
            
        split_dir = archive_dir / 'split'
        if not split_dir.exists():
            logging.error(f"No split directory found for {video_id}")
            return
        
        # Read the files
        unusual_df = pd.read_csv(unusual_cases_file[0])
        transcript_df = pd.read_csv(transcript_file)
        
        # Process deletions
        files_to_delete = unusual_df[unusual_df['check_action'] == 'delete']['audio_file'].tolist()
        if files_to_delete:
            # Remove rows from transcript
            transcript_df = transcript_df[~transcript_df['audio_file'].isin(files_to_delete)]
            
            # Delete audio files
            deleted_count = 0
            for audio_file in files_to_delete:
                # Extract just the filename from the audio_file path
                audio_filename = os.path.basename(audio_file)
                audio_path = split_dir / audio_filename
                if audio_path.exists():
                    os.remove(audio_path)
                    deleted_count += 1
                else:
                    logging.warning(f"Audio file not found: {audio_filename}")
            logging.info(f"Deleted {len(files_to_delete)} rows and {deleted_count} audio files from {video_id}")
        
        # Process kept cases
        kept_cases = unusual_df[unusual_df['check_action'] == 'keep']
        if not kept_cases.empty:
            # Update text for kept cases
            for _, case in kept_cases.iterrows():
                audio_file = case['audio_file']
                new_text = case['text']
                
                # Update text in transcript
                transcript_df.loc[transcript_df['audio_file'] == audio_file, 'text'] = new_text
            
            logging.info(f"Updated text for {len(kept_cases)} kept cases in {video_id}")
        
        # Save updated transcript
        transcript_df.to_csv(transcript_file, index=False)
        logging.info(f"Saved updated transcript for {video_id}")
        
    except Exception as e:
        logging.error(f"Error processing {video_id}: {str(e)}")

def process_all_videos():
    """
    Process all videos that have unusual cases files.
    """
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Get base directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        reports_dir = base_dir / 'data' / 'reports'
        
        # Get all video IDs with unusual cases
        video_ids = [d.name for d in reports_dir.iterdir() if d.is_dir()]
        
        if not video_ids:
            logging.info("No videos to process")
            return
            
        # Process each video
        total_deleted = 0
        total_updated = 0
        
        for video_id in video_ids:
            process_video(video_id)
            
        logging.info(f"Completed processing {len(video_ids)} videos")
            
    except Exception as e:
        logging.error(f"Error in batch processing: {str(e)}")

if __name__ == "__main__":
    process_all_videos()
