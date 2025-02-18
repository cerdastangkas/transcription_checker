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

### Output
- Creates detailed reports showing:
  - All unusual parts found
  - Audio clips of these parts for listening
  - Charts and tables showing findings
  - Interactive audio player for the weird parts

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
