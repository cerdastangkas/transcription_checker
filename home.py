import streamlit as st

def main():
    st.set_page_config(
        page_title="Transcription Checker",
        page_icon="🏠",
        layout="centered"
    )

    st.title("Transcription Checker")
    st.markdown("### Welcome to the Transcription Checker App!")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        ### 📝 CSV Editor
        Edit and manage transcription CSV files
        
        Features:
        - View and edit CSV files
        - Sort by audio file
        - Save changes instantly
        """)

    with col2:
        st.markdown("""
        ### 🔄 Run Single Analyzer
        Process transcription CSV files
        
        Features:
        - Select CSV files to analyze
        - View processing logs
        - Track analysis progress
        """)

    with col3:
        st.markdown("""
        ### 📊 Report Viewer
        View and analyze transcription reports
        
        Features:
        - Browse all reports
        - Play audio samples
        - Download reports
        """)
        
    with col4:
        st.markdown("""
        ### 🔁 Batch Analyzer
        Process all transcription files
        
        Features:
        - Analyze all unprocessed files
        - View batch processing logs
        - Auto-archive analyzed files
        """)
    
    st.markdown("""---
    #### 👈 Use the sidebar to navigate between pages
    
    The sidebar contains links to both the CSV Editor and Report Viewer.
    Each tool will open in the same window, maintaining your session state.
    """)

if __name__ == "__main__":
    main()
