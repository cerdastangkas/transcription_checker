import streamlit as st
import os
from pathlib import Path
import base64
import re
import shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

def get_html_reports(reports_dir=None):
    if reports_dir is None:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(current_dir, 'data', 'reports')
    """Get all analysis report HTML files recursively"""
    html_files = []
    print(f"Searching for reports in: {os.path.abspath(reports_dir)}")
    for root, _, files in os.walk(reports_dir):
        for file in files:
            if file.startswith('analysis_report_') and file.endswith('.html'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, reports_dir)
                # Get the immediate parent folder name
                rel_dir = os.path.dirname(rel_path)
                folder_name = rel_dir.split(os.sep)[0] if os.sep in rel_dir else rel_dir
                print(f"Found report: {full_path} in folder: {folder_name}")
                html_files.append({
                    'path': os.path.join(root, file),
                    'rel_path': rel_path,
                    'folder': folder_name,
                    'filename': file
                })
    return sorted(html_files, key=lambda x: (x['folder'], x['filename']))

def read_html_file(file_path):
    """Read HTML file content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_html_download_link(html_content, filename):
    """Generate a download link for HTML content"""
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">Download {filename}</a>'

def get_free_port():
    """Get a free port on localhost"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

class ReportsHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

def start_server(port, directory):
    """Start HTTP server in the background"""
    handler = lambda *args, **kwargs: ReportsHTTPRequestHandler(*args, directory=directory, **kwargs)
    server = HTTPServer(('localhost', port), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server

def main():
    st.set_page_config(
        page_title="Report Viewer",
        page_icon="📊",
        layout="wide"
    )
    
    # Get absolute path to reports directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(current_dir, 'data', 'reports')
    
    # Initialize HTTP server for serving reports
    if 'server' not in st.session_state:
        port = get_free_port()
        st.session_state.port = port
        st.session_state.server = start_server(port, reports_dir)
        st.session_state.server_url = f'http://localhost:{port}'

    st.title("Report Viewer")
    
    # Initialize video_id in session state
    if 'video_id' not in st.session_state:
        st.session_state.video_id = None

    # Get list of HTML reports
    reports = get_html_reports()

    if not reports:
        st.warning("No analysis reports found in data/reports directory")
        return

    # Create report selection with folder info in sidebar
    with st.sidebar:
        selected_report = st.selectbox(
            "Select Report",
            reports,
            format_func=lambda x: f"{x['filename']} ({x['folder']})"
        )

    # Display selected report
    if selected_report:
        # Update video ID
        video_id = selected_report['folder']
        st.session_state.video_id = video_id
        
        # Display video ID as header
        st.header(f"Video ID: {video_id}")
        # Read and display HTML content
        html_content = read_html_file(selected_report['path'])
        
        # Add download button
        st.markdown(
            get_html_download_link(html_content, selected_report['filename']),
            unsafe_allow_html=True
        )
        
        # Create iframe URL for the report
        report_url = f"{st.session_state.server_url}/{selected_report['rel_path']}"
        
        # Display the report in an iframe with generous height
        st.components.v1.iframe(report_url, height=5000, scrolling=True)

if __name__ == "__main__":
    main()
