#!/usr/bin/env python3

import os
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime

def move_report_folders(excel_path, new_folder_name=None):
    """
    Move existing folders from data/reports that match IDs in Excel file
    into a new consolidated folder.
    
    Args:
        excel_path (str): Path to the Excel file containing the 'id' column
        new_folder_name (str, optional): Name for the new folder. If None, uses timestamp
    """
    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path)
        
        # Check if 'id' column exists
        if 'id' not in df.columns:
            raise ValueError("Excel file must contain an 'id' column")
        
        # Setup paths
        reports_dir = Path("data/reports")
        if not reports_dir.exists():
            raise ValueError(f"Reports directory not found: {reports_dir}")
            
        # Create new folder name if not provided
        if not new_folder_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_folder_name = f"consolidated_{timestamp}"
            
        # Create new consolidated folder
        new_folder_path = reports_dir / new_folder_name
        new_folder_path.mkdir(exist_ok=True)
        print(f"\nCreated new folder: {new_folder_path}")
        
        # Get list of IDs from Excel
        folder_ids = [str(id_).strip() for id_ in df['id'].unique()]
        
        # Track moved and not found folders
        moved_folders = []
        not_found = []
        
        # Move matching folders
        for folder_id in folder_ids:
            source_path = reports_dir / folder_id
            if source_path.exists() and source_path.is_dir():
                dest_path = new_folder_path / folder_id
                shutil.move(str(source_path), str(dest_path))
                moved_folders.append(folder_id)
            else:
                not_found.append(folder_id)
        
        # Print summary
        print("\nFolder Movement Summary:")
        print(f"Total IDs in Excel: {len(folder_ids)}")
        print(f"Folders moved: {len(moved_folders)}")
        print(f"Folders not found: {len(not_found)}")
        
        if moved_folders:
            print("\nMoved folders:")
            for folder in moved_folders:
                print(f"- {folder}")
        
        if not_found:
            print("\nFolders not found:")
            for folder in not_found:
                print(f"- {folder}")
                
        print(f"\nAll moved folders are now in: data/reports/{new_folder_name}/")
                
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

if __name__ == "__main__":
    # Get Excel file path from user
    excel_path = input("Enter the path to your Excel file: ")
    new_folder = input("Enter name for the new folder (press Enter for automatic naming): ").strip()
    
    # Validate file exists and has .xlsx extension
    if not os.path.exists(excel_path):
        print(f"Error: File not found: {excel_path}")
    elif not excel_path.endswith(('.xlsx', '.xls')):
        print("Error: File must be an Excel file (.xlsx or .xls)")
    else:
        move_report_folders(excel_path, new_folder if new_folder else None)
