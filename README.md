# Transcription Checker

## Overview
This tool analyzes speech transcriptions and audio recordings to identify unusual speaking patterns. Think of it as a smart assistant that listens to recorded conversations and flags parts that sound unusual.

## Requirements
- Python 3.7+
- Required packages are listed in `requirements.txt`

## Installation
1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## How It Works

### Organization
Everything is kept in three main folders:
- `data/original`: Where your recordings and text files live
- `data/reports`: Where it puts its findings
- `data/archive`: Where it stores stuff it's already checked

### What It's Looking For
It flags speech that sounds odd, like:
- Someone talking super fast (like repeating "blah blah blah" really quickly)
- Someone talking very slowly with long pauses
- Very short phrases that take too long to say
- Parts where the speaking pattern just doesn't sound natural

### Process
1. **Analysis**
   - Counts words in each segment
   - Measures how long each segment takes
   - Calculates speaking speed
   
2. **Detection**
   It asks questions like:
   - "Is this person speaking way too fast?" (like more than 15 words per second)
   - "Is this person speaking unusually slow?" (like taking 4 seconds to say 3 words)
   - "Does this sound like normal conversation?"

### Output Reports
The tool generates several types of reports in `data/reports/<folder_name>/`:

1. **Interactive HTML Report** (`report_<timestamp>.html`)
   - **Overview Section**
     - Total segments analyzed
     - Number of unusual segments found
     - Average speaking rate (words per second)
     - Distribution of speech patterns
   
   - **Interactive Data Table**
     - Sortable columns for easy analysis
     - Audio player embedded for each segment
     - Color-coded rows for unusual segments
     - Columns showing:
       - Duration in seconds
       - Word count
       - Words per second
       - Deviation score
       - Full transcription text

   - **Visualizations**
     - Speaking rate distribution chart
     - Word count vs duration scatter plot
     - Unusual segments highlighted

2. **CSV Report** (`report_<timestamp>.csv`)
   - Detailed data for further analysis
   - All metrics and calculations included
   - Easy to import into other tools
   - Columns include:
     - Segment ID
     - Audio file path
     - Duration metrics
     - Word count statistics
     - Deviation scores
     - Unusual flags

3. **Audio Clips**
   - Stored in `audio/` subfolder
   - Contains only the unusual segments
   - Original audio quality preserved
   - Named for easy reference to report data

4. **Summary Statistics**
   - Overall dataset metrics
   - Unusual pattern categories found
   - Speaking rate ranges
   - Common deviation patterns

## Usage

1. **Setup Directory Structure**
   ```bash
   mkdir -p data/original data/reports data/archive
   ```

2. **Prepare Your Data**
   - Place your audio recordings in `data/original/<folder_name>/split/`
   - Put the transcription CSV in `data/original/<folder_name>/<folder_name>_transcripts.csv`
   - CSV format should have columns for text and duration_seconds

3. **Run Analysis**
   ```bash
   python csv_transcription_analyzer.py
   ```

4. **Check Results**
   - Open the generated HTML report in `data/reports/<folder_name>/`
   - Review the flagged segments
   - Listen to the audio clips of unusual parts

## Real-World Example
Imagine you're checking a 1-hour interview recording. This script would:
- Find parts where someone stuttered a lot
- Catch sections where there were awkward long pauses
- Spot parts where someone spoke unusually fast
- Help you quickly find these parts without listening to the whole thing

## Benefits
It's like having an assistant who:
- Listens to all your recordings
- Takes notes about weird parts
- Makes it easy for you to check those parts
- Keeps everything neatly organized

The goal is to help you find unusual parts in recordings without having to listen to everything yourself. It's particularly useful when you have lots of recordings to check and want to focus on the parts that might need attention.
