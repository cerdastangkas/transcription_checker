from pathlib import Path

from datetime import datetime

def find_unarchived_folders(save_to_file=True):
    """
    Compare folders in reports and archive directories.
    Lists folders that exist in reports but not in archive.
    Only compares folder names, ignoring full paths.
    
    Args:
        save_to_file (bool): If True, saves results to a timestamped file
    """
    # Define paths
    reports_dir = Path('data/reports')
    archive_dir = Path('data/archive')
    
    # Check if directories exist
    if not reports_dir.exists():
        print(f"Error: Reports directory not found at {reports_dir}")
        return
    if not archive_dir.exists():
        print(f"Error: Archive directory not found at {archive_dir}")
        return
        
    # Get folder names (just the last part of the path)
    report_folders = {d.name for d in reports_dir.iterdir() if d.is_dir()}
    archive_folders = {d.name for d in archive_dir.iterdir() if d.is_dir()}
    
    # Find folders in reports that aren't in archive
    unarchived_folders = report_folders - archive_folders
    
    if unarchived_folders:
        print(f"\nFound {len(unarchived_folders)} folders in reports that are not archived:")
        for folder in sorted(unarchived_folders):
            report_path = reports_dir / folder
            # Get folder size and file count
            file_count = sum(1 for _ in report_path.rglob('*') if _.is_file())
            folder_size = sum(f.stat().st_size for f in report_path.rglob('*') if f.is_file())
            print(f"\n{folder}:")
            print(f"  Path: {report_path}")
            print(f"  Files: {file_count}")
            print(f"  Size: {folder_size / (1024*1024):.2f} MB")
    else:
        print("\nAll folders in reports are already archived")
        
    # Prepare summary
    summary = [
        f"\nSummary:",
        f"Total folders in reports: {len(report_folders)}",
        f"Total folders in archive: {len(archive_folders)}",
        f"Unarchived folders: {len(unarchived_folders)}"
    ]
    
    # Print results
    if unarchived_folders:
        print(f"\nFound {len(unarchived_folders)} folders in reports that are not archived:")
    else:
        print("\nAll folders in reports are already archived")
    
    # Print and optionally save detailed results
    output_lines = []
    if unarchived_folders:
        for folder in sorted(unarchived_folders):
            report_path = reports_dir / folder
            # Get folder size and file count
            file_count = sum(1 for _ in report_path.rglob('*') if _.is_file())
            folder_size = sum(f.stat().st_size for f in report_path.rglob('*') if f.is_file())
            
            folder_info = [
                f"\n{folder}:",
                f"  Path: {report_path}",
                f"  Files: {file_count}",
                f"  Size: {folder_size / (1024*1024):.2f} MB"
            ]
            
            # Print and collect output
            print('\n'.join(folder_info))
            output_lines.extend(folder_info)
    
    # Print summary
    print('\n'.join(summary))
    
    # Save to file if requested
    if save_to_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('data/reports')
        output_file = output_dir / f'unarchived_folders_{timestamp}.txt'
        
        # Combine all output
        all_output = ['Unarchived Folders Report', f'Generated: {datetime.now()}']
        if output_lines:
            all_output.extend(['\nDetailed Results:'] + output_lines)
        all_output.extend([''] + summary)
        
        # Write to file
        output_file.write_text('\n'.join(all_output))
        print(f"\nResults saved to: {output_file}")
    
if __name__ == '__main__':
    find_unarchived_folders()
