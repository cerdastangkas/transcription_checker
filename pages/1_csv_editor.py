import streamlit as st
import pandas as pd
import os
from pathlib import Path

def main():
    st.set_page_config(
        page_title="CSV Editor",
        page_icon="📝",
        layout="wide"
    )

    st.title("Unusual Cases Editor")
    
    # Initialize video_id in session state
    if 'video_id' not in st.session_state:
        st.session_state.video_id = None

    # Get absolute path to reports directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(current_dir, 'data', 'reports')

    # Get list of unusual cases CSV files
    csv_files = []
    for root, _, files in os.walk(reports_dir):
        for file in files:
            if file.startswith('unusual_cases_') and file.endswith('.csv'):
                rel_path = os.path.relpath(os.path.join(root, file), reports_dir)
                csv_files.append(rel_path)

    if not csv_files:
        st.warning("No unusual cases files found in data/reports directory")
        return

    # Create file selection in sidebar
    selected_file = st.selectbox(
        "Select Unusual Cases File",
        sorted(csv_files)
    )

    if selected_file:
        file_path = os.path.join(reports_dir, selected_file)
        
        # Update video ID
        video_id = os.path.basename(os.path.dirname(file_path))
        st.session_state.video_id = video_id
        
        # Display video ID as header
        st.header(f"Video ID: {video_id}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Sort by audio_file if it exists
            if 'audio_file' in df.columns:
                df = df.sort_values('audio_file')
            
            # Add check_action column if it doesn't exist
            if 'check_action' not in df.columns:
                df['check_action'] = ''
            
            # Define check action options
            check_action_options = [
                'keep',
                'delete'
            ]
            
            # Create a copy for comparison
            if 'df_original' not in st.session_state:
                st.session_state.df_original = df.copy()
            
            # Display each row with audio player and text editor
            edited_rows = []
            for idx, row in df.iterrows():
                col1, col2, col3 = st.columns([2, 4, 1])
                
                with col1:
                    if 'audio_file' in row:
                        # Replace 'split/' with 'audio/' in the audio file path
                        audio_path = os.path.join(os.path.dirname(file_path), row['audio_file'].replace('split/', 'audio/'))
                        if os.path.exists(audio_path):
                            st.audio(audio_path)
                            st.text(os.path.basename(row['audio_file']))
                        else:
                            st.error(f"Audio file not found: {audio_path}")
                
                with col2:
                    if 'text' in row:
                        new_text = st.text_area(
                            f"Text {idx}",
                            value=row['text'],
                            height=100,
                            key=f"text_{idx}"
                        )
                        row['text'] = new_text
                
                with col3:
                    action = st.selectbox(
                        f"Action {idx}",
                        ['', 'keep', 'delete'],
                        index=['', 'keep', 'delete'].index(row['check_action']) if row['check_action'] in ['keep', 'delete'] else 0,
                        key=f"action_{idx}"
                    )
                    row['check_action'] = action
                
                edited_rows.append(row)
                st.markdown("---")
            
            # Create DataFrame from edited rows
            edited_df = pd.DataFrame(edited_rows)
            
            # Add save button
            if st.button("Save Changes"):
                if not edited_df.equals(st.session_state.df_original):
                    edited_df.to_csv(file_path, index=False)
                    st.success("Changes saved successfully!")
                    st.session_state.df_original = edited_df.copy()
                else:
                    st.info("No changes to save")
                    
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")

if __name__ == "__main__":
    main()
