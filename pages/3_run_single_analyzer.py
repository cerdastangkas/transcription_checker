import streamlit as st
import os
import sys
import subprocess
from datetime import datetime
import pandas as pd

# Add parent directory to path to import analyzer
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(current_dir, 'src', 'core'))

from csv_transcription_analyzer import analyze_transcriptions, generate_report, save_reports

def main():
    st.set_page_config(
        page_title="Run Single ID Analyzer",
        page_icon="🔄",
        layout="wide"
    )

    st.title("Run Transcription Analyzer")

    # Get list of transcript CSV files from data/original
    original_dir = os.path.join(current_dir, 'data', 'original')
    csv_files = []
    for root, _, files in os.walk(original_dir):
        for file in files:
            if file.endswith('_transcripts.csv'):
                rel_path = os.path.relpath(os.path.join(root, file), original_dir)
                csv_files.append(rel_path)

    if not csv_files:
        st.warning("No transcript CSV files found in data/original directory")
        return

    # File selection
    selected_file = st.selectbox(
        "Select CSV File to Analyze",
        sorted(csv_files)
    )

    # Initialize session state for logs
    if 'logs' not in st.session_state:
        st.session_state.logs = []

    # Run button
    if st.button("Run Analysis"):
        if selected_file:
            try:
                file_path = os.path.join(original_dir, selected_file)
                
                # Add start log
                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{start_time}] Starting analysis of {selected_file}..."
                st.session_state.logs.append(log_entry)
                
                # Run analysis
                df = analyze_transcriptions(file_path)
                
                # Generate report data
                report_data = generate_report(df)
                
                # Add acceptance stats if available
                if 'accepted_by_asix' in df.columns:
                    # Convert to boolean
                    df['accepted_by_asix'] = df['accepted_by_asix'].fillna(False)
                    df['accepted_by_asix'] = df['accepted_by_asix'].astype(str).str.lower()
                    df['accepted_by_asix'] = df['accepted_by_asix'].map({'true': True, 'false': False, '1': True, '0': False})
                    
                    # Count accepted/rejected segments
                    accepted_count = int(df['accepted_by_asix'].sum())
                    total_count = len(df)
                    
                    # Get rejection reasons
                    rejection_reasons = {}
                    if 'rejected_reason' in df.columns:
                        rejection_reasons = df[df['accepted_by_asix'] == False]['rejected_reason'].value_counts().to_dict()
                    
                    # Update report with acceptance stats
                    report_data.update({
                        'accepted_segments': accepted_count,
                        'rejected_segments': total_count - accepted_count,
                        'rejection_reasons': rejection_reasons
                    })
                
                # Save reports
                save_reports(df, report_data, file_path)
                
                # Add completion log
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{end_time}] Analysis completed successfully! Reports saved in data/reports directory."
                st.session_state.logs.append(log_entry)
                
                # Show success message with analysis results
                st.success(f"Analysis completed! Found {report_data['unusual_cases_count']} unusual cases out of {report_data['total_segments_analyzed']} segments.")
                
                # Show stats
                st.markdown("### Analysis Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Speech Stats:**")
                    st.write(f"- Average words/sec: {report_data['average_words_per_second']:.2f}")
                    st.write(f"- Standard deviation: {report_data['standard_deviation']:.2f}")
                    st.write(f"- Total segments: {report_data['total_segments_analyzed']}")
                
                with col2:
                    if 'accepted_segments' in report_data:
                        st.markdown("**Acceptance Stats:**")
                        st.write(f"- Accepted: {report_data['accepted_segments']}")
                        st.write(f"- Rejected: {report_data['rejected_segments']}")
                        
                        if report_data['rejection_reasons']:
                            st.markdown("\n**Rejection Reasons:**")
                            for reason, count in report_data['rejection_reasons'].items():
                                st.write(f"- {reason}: {count}")
                
            except Exception as e:
                # Add error log
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{error_time}] Error: {str(e)}"
                st.session_state.logs.append(log_entry)
                st.error(f"Error running analysis: {str(e)}")

    # Display logs
    if st.session_state.logs:
        st.markdown("### Processing Logs")
        logs_text = "\n".join(st.session_state.logs)
        st.code(logs_text, language="text")
        
        # Clear logs button
        if st.button("Clear Logs"):
            st.session_state.logs = []
            st.experimental_rerun()

if __name__ == "__main__":
    main()
