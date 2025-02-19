import streamlit as st
import subprocess
import os
import sys
from datetime import datetime

def main():
    st.set_page_config(
        page_title="Batch Analyzer",
        page_icon="🔄",
        layout="wide"
    )

    st.title("Batch Transcription Analyzer")
    st.markdown("""
    This page runs the analyzer on all transcription files in the `data/original` directory.
    The analyzer will:
    1. Process all unanalyzed folders
    2. Generate reports for each folder
    3. Move analyzed folders to archive
    """)

    # Initialize session state for logs
    if 'batch_logs' not in st.session_state:
        st.session_state.batch_logs = []

    # Get current directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    analyzer_path = os.path.join(current_dir, 'src', 'core', 'csv_transcription_analyzer.py')

    # Run button
    if st.button("Run Batch Analysis"):
        try:
            # Add start log
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{start_time}] Starting batch analysis..."
            st.session_state.batch_logs.append(log_entry)

            # Run the analyzer script
            process = subprocess.Popen(
                [sys.executable, analyzer_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=current_dir
            )

            # Get output
            stdout, stderr = process.communicate()

            # Add output to logs
            if stdout:
                for line in stdout.split('\n'):
                    if line.strip():
                        st.session_state.batch_logs.append(line)

            # Add error to logs if any
            if stderr:
                for line in stderr.split('\n'):
                    if line.strip():
                        st.session_state.batch_logs.append(f"Error: {line}")

            # Add completion log
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{end_time}] Batch analysis completed!"
            st.session_state.batch_logs.append(log_entry)

            # Show success message
            st.success("Batch analysis completed! Check the logs below for details.")

        except Exception as e:
            # Add error log
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{error_time}] Error: {str(e)}"
            st.session_state.batch_logs.append(log_entry)
            st.error(f"Error running batch analysis: {str(e)}")

    # Display logs
    if st.session_state.batch_logs:
        st.markdown("### Processing Logs")
        logs_text = "\n".join(st.session_state.batch_logs)
        st.code(logs_text, language="text")
        
        # Clear logs button
        if st.button("Clear Logs"):
            st.session_state.batch_logs = []
            st.experimental_rerun()

if __name__ == "__main__":
    main()
