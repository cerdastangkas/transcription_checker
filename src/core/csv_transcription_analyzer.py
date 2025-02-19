import pandas as pd
import numpy as np
import os
import shutil
from datetime import datetime
import json

def analyze_transcriptions(csv_path):
    """
    Analyze transcriptions from CSV file containing text and duration_seconds columns.
    
    Args:
        csv_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Analysis results with statistical measures
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Calculate word counts for each transcription (simple split by spaces)
    df['word_count'] = df['text'].apply(lambda x: len(str(x).split()))
    
    # Calculate words per second
    df['words_per_second'] = df['word_count'] / df['duration_seconds']
    
    # Add audio file name if it exists in the CSV, otherwise create from index
    if 'audio_file' not in df.columns:
        # Create audio file names based on the folder name and index
        folder_name = os.path.basename(os.path.dirname(csv_path))
        df['audio_file'] = df.index.map(lambda x: f"{folder_name}_segment_{x:03d}")
    
    # Calculate statistical measures using robust statistics
    median_wps = df['words_per_second'].median()
    q1 = df['words_per_second'].quantile(0.25)
    q3 = df['words_per_second'].quantile(0.75)
    iqr = q3 - q1
    
    # Calculate word density (words per second) percentiles
    df['wps_percentile'] = df['words_per_second'].rank(pct=True)
    
    # Calculate text-duration ratio score
    df['text_duration_ratio'] = df['word_count'] / df['duration_seconds']
    df['ratio_percentile'] = df['text_duration_ratio'].rank(pct=True)
    
    # Calculate core metrics
    df['avg_words_per_second'] = df['word_count'].mean() / df['duration_seconds'].mean()
    
    # 1. Word density ratio (comparing to local context)
    window_size = 10
    df['local_avg_wps'] = df['words_per_second'].rolling(window=window_size, center=True, min_periods=1).mean()
    df['word_density_ratio'] = df['words_per_second'] / df['local_avg_wps']
    
    # 2. Duration-based expected words
    df['expected_words'] = df['duration_seconds'] * df['avg_words_per_second']
    df['word_deviation'] = abs(df['word_count'] - df['expected_words']) / df['expected_words']
    
    # 3. Short segment analysis (different threshold for very short segments)
    df['is_short'] = df['duration_seconds'] < 3.0
    df['short_segment_ratio'] = df.apply(
        lambda x: x['word_count'] / (x['duration_seconds'] * 3.0) if x['is_short'] else 1.0, 
        axis=1
    )
    
    # 4. Silence detection
    min_wps_threshold = 0.3
    df['silence_score'] = df.apply(
        lambda x: 1.0 if x['words_per_second'] < min_wps_threshold and x['duration_seconds'] > 2.0 else 0.0,
        axis=1
    )
    
    # Calculate percentile ranks for each metric
    df['density_rank'] = df['word_density_ratio'].rank(pct=True)
    df['deviation_rank'] = df['word_deviation'].rank(pct=True)
    df['short_rank'] = df['short_segment_ratio'].rank(pct=True)
    
    # Calculate deviation score with enhanced detection
    df['deviation_score'] = df.apply(lambda row: 
        # Tier 1: Extreme repeated words (>15 w/s)
        20.0 if row['words_per_second'] > 15.0 else
        # Tier 2: Very slow speech
        10.0 if (row['words_per_second'] < 0.85 and 
                row['duration_seconds'] > 4.0) else
        # Tier 3: Few words with long duration
        8.0 if (row['word_count'] <= 6 and 
               row['duration_seconds'] > 3.0 and
               row['words_per_second'] < 1.4) else
        # Tier 4: Normal speech range
        0.5 if (1.5 <= row['words_per_second'] <= 4.5 and 
               row['duration_seconds'] < 6.0 and
               row['word_count'] > 6) else
        # Tier 5: Default calculation
        np.abs(row['words_per_second'] - median_wps) / iqr * 2.0,
        axis=1
    )
    
    # Refined thresholds based on all examples
    extreme_wps_high = 15.0     # Repeated words threshold
    extreme_wps_low = 0.85      # Increased to catch more slow speech
    extreme_duration = 3.0      # Lowered to catch shorter segments
    min_word_density = 1.4      # Words per second minimum for normal speech
    extreme_deviation_threshold = 7.0  # Adjusted based on examples

    # Enhanced unusual case detection
    is_unusual = (
        # Extreme high words/second (repeated words)
        (df['words_per_second'] > extreme_wps_high) |
        
        # Very slow speech (multiple conditions)
        ((df['words_per_second'] < extreme_wps_low) & 
         (df['duration_seconds'] > extreme_duration)) |
        
        # Few words with longer duration
        ((df['word_count'] <= 6) & 
         (df['duration_seconds'] > 3.0) & 
         (df['words_per_second'] < min_word_density)) |
        
        # Long duration with few words
        ((df['duration_seconds'] > 4.5) & 
         (df['word_count'] < 8) & 
         (df['words_per_second'] < 1.2)) |
        
        # High deviation score
        (df['deviation_score'] > extreme_deviation_threshold)
    )
    
    # Calculate unusual score using weighted components
    df['unusual_score'] = (
        3.0 * df['word_deviation'] +
        2.0 * np.abs(df['word_density_ratio'] - 1.0) +
        1.5 * df['silence_score'] +
        1.0 * df['short_segment_ratio'] * df['is_short'].astype(int)
    )
    
    # Mark cases as unusual and sort by unusual_score
    df['is_unusual'] = is_unusual
    df = df.sort_values('unusual_score', ascending=False)
    
    return df

def generate_report(df):
    """
    Generate a summary report of the analysis.
    
    Args:
        df (pd.DataFrame): Analysis results
        
    Returns:
        dict: Summary statistics and unusual cases
    """
    if df.empty:
        return {"error": "No data to analyze"}
    
    unusual_cases = df[df['is_unusual']].to_dict('records')
    
    report = {
        "total_segments_analyzed": len(df),
        "average_words_per_second": df['words_per_second'].mean(),
        "standard_deviation": df['words_per_second'].std(),
        "unusual_cases_count": len(unusual_cases),
        "unusual_cases": unusual_cases
    }
    
    return report

def copy_audio_files(df, report_dir, data_dir):
    """
    Copy audio files for unusual cases to the report directory.
    """
    audio_dir = os.path.join(report_dir, 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    
    # Get list of audio files for unusual cases
    unusual_files = df[df['is_unusual']]['audio_file'].tolist()
    
    # Copy each audio file
    for audio_file in unusual_files:
        src_path = os.path.join(data_dir, audio_file)
        dst_path = os.path.join(audio_dir, os.path.basename(audio_file))
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
    
    return audio_dir

def create_html_report(df, report_data, output_path, audio_dir=None):
    """
    Create an enhanced HTML report with interactive features and visualizations.
    """
    # Calculate some additional statistics for visualization
    avg_wps = report_data['average_words_per_second']
    std_wps = report_data['standard_deviation']
    
    # Prepare data for the histogram
    hist_data = df['words_per_second'].tolist()
    hist_data_json = json.dumps(hist_data)
    
    html_content = f"""
    <html>
    <head>
        <title>Transcription Analysis Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            .audio-player {{
                margin: 10px 0;
                width: 100%;
                max-width: 400px;
            }}
            .audio-container {{
                margin: 15px 0;
                padding: 10px;
                background: #f0f0f0;
                border-radius: 5px;
            }}
            .audio-label {{
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }}
        </style>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                background: linear-gradient(135deg, #6c5ce7, #a8a4e6);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                text-align: center;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #6c5ce7;
                margin: 10px 0;
            }}
            .stat-label {{
                color: #666;
                font-size: 14px;
            }}
            .chart-container {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                margin-bottom: 30px;
            }}
            .unusual-cases {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .case-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                transition: transform 0.2s;
            }}
            .case-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            .severity-high {{
                border-left: 4px solid #ff4757;
            }}
            .severity-medium {{
                border-left: 4px solid #ffa502;
            }}
            .severity-low {{
                border-left: 4px solid #2ed573;
            }}
            .metric {{
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
                font-size: 14px;
            }}
            .metric-value {{
                font-weight: bold;
            }}
            .text-content {{
                margin-top: 10px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Transcription Analysis Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Segments</div>
                    <div class="stat-value">{report_data['total_segments_analyzed']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Average Words/Second</div>
                    <div class="stat-value">{avg_wps:.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Standard Deviation</div>
                    <div class="stat-value">{std_wps:.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Unusual Cases</div>
                    <div class="stat-value">{report_data['unusual_cases_count']}</div>
                </div>
            </div>

            <div class="chart-container">
                <h2>Distribution of Words per Second</h2>
                <div id="histogram"></div>
            </div>

            <h2>Unusual Cases Analysis</h2>
            <div class="unusual-cases">
    """

    for case in report_data['unusual_cases']:
        # Determine severity based on deviation score
        if case['deviation_score'] > 3:
            severity = 'high'
        elif case['deviation_score'] > 2.5:
            severity = 'medium'
        else:
            severity = 'low'
            
        html_content += f"""
        <div class="case-card severity-{severity}">
            <h3>Audio: {case.get('audio_file', 'Unknown')}</h3>
            <div class="metric">
                <span>Duration</span>
                <span class="metric-value">{case['duration_seconds']:.2f}s</span>
            </div>
            <div class="metric">
                <span>Word Count</span>
                <span class="metric-value">{case['word_count']}</span>
            </div>
            <div class="metric">
                <span>Words/Second</span>
                <span class="metric-value">{case['words_per_second']:.2f}</span>
            </div>
            <div class="metric">
                <span>Deviation Score</span>
                <span class="metric-value">{case['deviation_score']:.2f}</span>
            </div>
            <div class="text-content">
                {case['text']}
            </div>
            <div class="audio-container">
                <div class="audio-label">Audio File: {case['audio_file']}</div>
                <audio class="audio-player" controls>
                    <source src="audio/{os.path.basename(case['audio_file'])}" type="audio/wav">
                    Your browser does not support the audio element.
                </audio>
            </div>
        </div>
        """

    html_content += f"""
            </div>
        </div>
        
        <script>
            // Create histogram of words per second
            const histData = {hist_data_json};
            const trace = {{
                x: histData,
                type: 'histogram',
                nbinsx: 30,
                marker: {{
                    color: '#6c5ce7',
                    opacity: 0.7
                }}
            }};
            
            const layout = {{
                title: 'Distribution of Words per Second',
                xaxis: {{title: 'Words per Second'}},
                yaxis: {{title: 'Frequency'}},
                bargap: 0.05,
                showlegend: false
            }};
            
            Plotly.newPlot('histogram', [trace], layout);
        </script>
    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def save_reports(df, report_data, input_csv_path):
    """
    Save analysis reports in various formats in a folder structure matching the input data.
    
    Args:
        df: DataFrame with analysis results
        report_data: Dictionary containing the analysis report
        input_csv_path: Path to the input CSV file
    """
    # Extract the folder name from the input path
    folder_name = os.path.basename(os.path.dirname(input_csv_path))
    
    # Create reports directory with the same folder name
    base_dir = os.path.join("data/reports", folder_name)
    os.makedirs(base_dir, exist_ok=True)
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save unusual cases to CSV
    unusual_df = df[df['is_unusual']].copy()
    unusual_cases_path = os.path.join(base_dir, f"unusual_cases_{timestamp}.csv")
    unusual_df.to_csv(unusual_cases_path, index=False)
    
    # Save full analysis results to CSV
    full_analysis_path = os.path.join(base_dir, f"full_analysis_{timestamp}.csv")
    df.to_csv(full_analysis_path, index=False)
    
    # Create audio directory and copy audio files
    data_dir = os.path.dirname(input_csv_path)
    audio_dir = copy_audio_files(df, base_dir, data_dir)
    
    # Save HTML report
    html_report_path = os.path.join(base_dir, f"analysis_report_{timestamp}.html")
    create_html_report(df, report_data, html_report_path, audio_dir)
    
    # Save summary report as JSON
    summary_path = os.path.join(base_dir, f"summary_{timestamp}.json")
    with open(summary_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return {
        'unusual_cases': unusual_cases_path,
        'full_analysis': full_analysis_path,
        'html_report': html_report_path,
        'summary': summary_path,
        'report_directory': base_dir
    }

def analyze_folder(folder_name):
    """
    Analyze a specific folder's transcriptions.
    """
    csv_path = f"data/original/{folder_name}/{folder_name}_transcripts.csv"
    
    # Analyze the transcriptions
    results_df = analyze_transcriptions(csv_path)
    
    # Generate the report
    report = generate_report(results_df)
    
    # Save reports to files
    report_files = save_reports(results_df, report, csv_path)
    
    print(f"\nAnalysis Summary for {folder_name}:")
    print(f"Total segments analyzed: {report['total_segments_analyzed']}")
    print(f"Average words per second: {report['average_words_per_second']:.2f}")
    print(f"Standard deviation: {report['standard_deviation']:.2f}")
    print(f"\nUnusual cases found: {report['unusual_cases_count']}")
    
    print("\nReport files generated in:", report_files['report_directory'])
    print(f"- Unusual cases CSV: {os.path.basename(report_files['unusual_cases'])}")
    print(f"- Full analysis CSV: {os.path.basename(report_files['full_analysis'])}")
    print(f"- HTML report: {os.path.basename(report_files['html_report'])}")
    print(f"- Summary JSON: {os.path.basename(report_files['summary'])}")
    
    return results_df, report

def get_folders_to_analyze(data_dir="data/original"):
    """
    Get list of folders in the data/original directory that contain transcription data.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        return []
        
    folders = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            # Check if folder contains required files
            csv_file = f"{item}_transcripts.csv"
            if os.path.exists(os.path.join(item_path, csv_file)):
                folders.append(item)
    return folders

def archive_folder(folder_name, data_dir="data", archive_dir="data/archive"):
    """
    Move analyzed folder to archive directory.
    """
    # Create archive directory if it doesn't exist
    os.makedirs(archive_dir, exist_ok=True)
    
    # Get source and destination paths
    source_path = os.path.join(data_dir, 'original', folder_name)
    dest_path = os.path.join(archive_dir, folder_name)
    
    # Add timestamp to folder name if it already exists in archive
    if os.path.exists(dest_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_path = f"{dest_path}_{timestamp}"
    
    # Move the folder
    print(f"Moving {folder_name} to archive...")
    os.rename(source_path, dest_path)
    print(f"Moved to: {dest_path}")

if __name__ == "__main__":
    # Get list of folders to analyze
    folders = get_folders_to_analyze()
    
    if not folders:
        print("No folders found for analysis in the data directory.")
        exit(0)
    
    print(f"Found {len(folders)} folders to analyze: {', '.join(folders)}")
    
    for folder in folders:
        try:
            print(f"\nAnalyzing folder: {folder}")
            analyze_folder(folder)
            
            # Move to archive after successful analysis
            archive_folder(folder)
            
        except Exception as e:
            print(f"Error analyzing folder {folder}: {str(e)}")
            continue
    
    print("\nAnalysis complete. All processed folders have been moved to archive.")
