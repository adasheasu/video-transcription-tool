# Video Transcription Tool

A Flask-based web application for transcribing videos and audio files using OpenAI Whisper, with support for YouTube downloads and transcript format conversion. Features ASU-branded HTML output.

## Features

- **Video/Audio Transcription**: Upload video or audio files for AI-powered transcription using OpenAI Whisper
- **YouTube Support**: Intelligently tries YouTube captions first (instant), falls back to Whisper transcription if unavailable
- **In-Browser Transcript Editing**: Edit transcripts after generation and regenerate all formats with your changes
- **Transcript Conversion**: Upload existing transcripts (TXT, SRT, VTT) with optional video metadata and convert to accessible HTML
- **Multiple Output Formats**: TXT, SRT, VTT, and ASU-branded HTML
- **Multiple Model Sizes**: Choose from tiny, base, small, medium, or large models (trade-off between speed and accuracy)
- **Multi-language Support**: Auto-detect or specify the language of your video
- **Enhanced Search**: Search functionality works on both full transcript text and timestamped segments with highlighting
- **WCAG 2.2 AA Compliant**: Fully accessible HTML with skip links, ARIA labels, keyboard navigation, and proper color contrast
- **ASU Branding**: HTML transcripts use official ASU brand colors (Maroon #8C1D40, Gold #FFC627)

## Requirements

- Python 3.8 or higher
- ffmpeg (for audio/video processing)
- 4-8GB RAM (depending on model size)
- Internet connection (for YouTube downloads)

## Installation

### 1. Install ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 2. Set up Python environment

```bash
# Navigate to the project directory
cd /Users/alejandradashe/video_transcription_tool

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. First-time setup

The first time you run the application, Whisper will download the selected model (ranging from ~75MB for tiny to ~2.9GB for large).

## Usage

### Start the application

```bash
# Make sure you're in the project directory with virtual environment activated
python app.py
```

The application will start on `http://localhost:5001`

### Web Interface

Open your browser and navigate to `http://localhost:5001`

#### Upload Video Tab
1. Select a video or audio file (MP4, AVI, MOV, MP3, WAV, etc.)
2. Choose transcription model (base recommended for balance)
3. Select language (auto-detect works well)
4. Click "Transcribe Video"
5. Wait for processing (time varies by file size and model)
6. Download transcripts in your preferred format

#### YouTube URL Tab
1. Paste a YouTube video URL
2. Choose transcription model
3. Select language
4. Click "Transcribe YouTube Video"
5. The tool will download audio and transcribe automatically
6. Download transcripts in your preferred format

#### Convert Transcript Tab
1. Upload an existing transcript file (TXT, SRT, or VTT)
2. Optionally add video metadata (title, URL, author)
3. Click "Convert to HTML"
4. Download or view the ASU-branded HTML transcript

#### Edit Transcript Feature
After any transcription or conversion:
1. Click "Edit Transcript" button in the results
2. Make your changes in the text editor
3. Click "Save & Regenerate" to create updated files
4. All formats (TXT, SRT, VTT, HTML) are regenerated with your edits

### Command Line Usage

You can also use the modules directly from the command line:

**Transcribe a video:**
```bash
python transcription_processor.py path/to/video.mp4
```

**Download from YouTube:**
```bash
python youtube_downloader.py "https://www.youtube.com/watch?v=..."
```

**Convert transcript to HTML:**
```bash
python transcript_converter.py path/to/transcript.srt
```

## Model Sizes

| Model  | Size | Speed | Accuracy | Use Case |
|--------|------|-------|----------|----------|
| Tiny   | ~75MB | Very Fast | Basic | Quick drafts, testing |
| Base   | ~150MB | Fast | Good | Recommended for most uses |
| Small  | ~500MB | Medium | Better | Higher quality needed |
| Medium | ~1.5GB | Slow | High | Professional transcripts |
| Large  | ~2.9GB | Very Slow | Best | Maximum accuracy |

## Output Formats

- **TXT**: Plain text transcript
- **SRT**: SubRip subtitle format (with timestamps)
- **VTT**: WebVTT subtitle format (for web video)
- **HTML**: Accessible, searchable HTML with ASU branding

## ASU Brand Compliance & Accessibility

HTML transcripts use official ASU brand guidelines and meet accessibility standards:

**ASU Branding:**
- Colors: ASU Maroon (#8C1D40) and ASU Gold (#FFC627)
- Typography: Arial font family
- Professional, consistent design

**WCAG 2.2 AA Compliance:**
- Skip navigation links for keyboard users
- ARIA labels and semantic HTML
- Proper color contrast ratios (7.39:1 for maroon/white)
- 3px focus indicators with 2px offset
- Screen reader support
- Responsive and print-friendly design

**Enhanced Search:**
- Search both full transcript and timestamped segments
- Real-time highlighting of matching text
- Filter segments by search term

Source: [ASU Brand Guide](https://brandguide.asu.edu/)

## Troubleshooting

**"ffmpeg not found" error:**
- Make sure ffmpeg is installed and in your PATH
- Test by running `ffmpeg -version` in terminal

**Out of memory errors:**
- Try a smaller model size (tiny or base)
- Close other applications
- Process shorter video segments

**YouTube download fails:**
- Check internet connection
- Verify the URL is correct and video is public
- Some videos may be restricted by region or copyright

**Slow transcription:**
- Normal for longer videos and larger models
- Base model on a 10-minute video takes ~2-5 minutes
- Consider using GPU acceleration for faster processing

## Project Structure

```
video_transcription_tool/
├── app.py                      # Flask web application
├── transcription_processor.py  # Whisper transcription engine
├── youtube_downloader.py       # YouTube video downloader
├── transcript_converter.py     # Transcript format converter
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   └── index.html             # Web interface
├── static/                     # (empty - styles inline)
├── uploads/                    # Temporary upload storage
└── transcripts/               # Generated transcripts

```

## Credits

- **OpenAI Whisper**: AI transcription model
- **yt-dlp**: YouTube video downloader
- **Flask**: Web framework
- **ASU Brand Guidelines**: Design specifications

## License

This tool is provided as-is for educational and internal use at Arizona State University.

## Support

For issues or questions, please contact the development team or submit an issue to the project repository.
