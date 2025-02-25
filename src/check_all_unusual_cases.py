#!/usr/bin/env python3

import os
from pathlib import Path
import pandas as pd
from core.deepinfra_transcriber import transcribe_unusual_cases

def check_all_unusual_cases():
    """
    Find and process all unusual cases CSV files in the data/reports directory.
    For each video directory, find the most recent unusual_cases CSV and process it.
    """
    # Get the reports directory
    reports_dir = Path('data/reports')
    if not reports_dir.exists():
        print(f"Error: Reports directory not found at {reports_dir}")
        return
        
    # Find all video directories (immediate subdirectories of reports)
    video_dirs = [d for d in reports_dir.iterdir() if d.is_dir()]
    if not video_dirs:
        print("No video directories found in reports directory")
        return
        
    print(f"Found {len(video_dirs)} video directories")
    
    # Process each video directory
    for video_dir in sorted(video_dirs):
        video_id = video_dir.name
        print(f"\nProcessing video: {video_id}")
        
        # Find unusual cases CSV files
        csv_files = list(video_dir.glob('unusual_cases_*.csv'))
        if not csv_files:
            print(f"No unusual cases CSV files found for {video_id}")
            continue
            
        # Get the most recent CSV file
        latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
        print(f"Found CSV file: {latest_csv.name}")

        transcribe_unusual_cases(video_id)
        
        # # Read the CSV to check current transcription status
        # df = pd.read_csv(latest_csv)
        # total_segments = len(df)
        # empty_transcripts = df['text'].isna().sum()
        # print(f"Total segments: {total_segments}")
        # print(f"Empty transcripts: {empty_transcripts}")
        
        # if empty_transcripts > 0:
        #     print("Running transcription for empty segments...")
        #     transcribe_unusual_cases(video_id)
        # else:
        #     print("All segments already have transcriptions")

if __name__ == '__main__':
    check_all_unusual_cases()
