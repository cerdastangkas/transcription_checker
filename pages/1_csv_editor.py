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

    # Create file selection
    selected_file = st.selectbox(
        "Select Unusual Cases File",
        sorted(csv_files)
    )

    if selected_file:
        file_path = os.path.join(reports_dir, selected_file)
        
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
            
            # Select only needed columns
            display_columns = ['audio_file', 'text', 'check_action']
            df = df[display_columns]
            
            # Configure column settings
            column_config = {
                'audio_file': st.column_config.TextColumn(
                    'Audio File',
                    width='medium'
                ),
                'text': st.column_config.TextColumn(
                    'Text',
                    width='large'
                ),
                'check_action': st.column_config.SelectboxColumn(
                    'Check Action',
                    help='Select whether to keep or delete this case',
                    width='small',
                    options=check_action_options
                )
            }
            
            # Create a copy for comparison
            if 'df_original' not in st.session_state:
                st.session_state.df_original = df.copy()
            
            # Display editable dataframe
            edited_df = st.data_editor(
                df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True
            )
            
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
