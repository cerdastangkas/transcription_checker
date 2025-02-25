import pandas as pd
from pathlib import Path

def add_check_action_column(video_id=None):
    """
    Add or update check_action column in unusual cases CSV files.
    If video_id is provided, only process that video's CSV files.
    Otherwise, process all videos' CSV files.
    
    Args:
        video_id (str, optional): Specific video ID to process
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
        
    updated_count = 0
    for video_dir in video_dirs:
        # Find unusual cases CSV files
        csv_files = list(video_dir.glob('unusual_cases_*.csv'))
        if not csv_files:
            print(f"No unusual cases CSV files found for {video_dir.name}")
            continue
            
        # Process each CSV file
        for csv_file in csv_files:
            print(f"\nProcessing {csv_file.name}")
            df = pd.read_csv(csv_file)
            
            # Check if column exists
            if 'check_action' not in df.columns:
                print("Adding check_action column")
                df['check_action'] = 'keep'
                updated_count += 1
            else:
                # Update any null or empty values to 'keep'
                mask = df['check_action'].isna() | (df['check_action'] == '')
                if mask.any():
                    print("Updating empty check_action values to 'keep'")
                    df.loc[mask, 'check_action'] = 'keep'
                    updated_count += 1
            
            # Save changes
            df.to_csv(csv_file, index=False)
            print(f"Updated {csv_file.name}")
    
    print(f"\nCompleted: Updated {updated_count} files")
