"""
Video Transcription Tool - Flask Web Application
Uses OpenAI Whisper for local video transcription
Supports: video files, YouTube URLs, existing transcripts (TXT/SRT/VTT)
"""
import os
import re
import unicodedata
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
from transcription_processor import VideoTranscriber
from youtube_downloader import YouTubeDownloader
from transcript_converter import TranscriptConverter
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TRANSCRIPT_FOLDER'] = 'transcripts'

ALLOWED_VIDEO_EXTENSIONS = {
    'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm',
    'mp3', 'wav', 'aac', 'm4a', 'flac', 'ogg'
}

ALLOWED_TRANSCRIPT_EXTENSIONS = {
    'txt', 'srt', 'vtt'
}

def allowed_video_file(filename):
    """Check if file is a video/audio file"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_transcript_file(filename):
    """Check if file is a transcript file"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TRANSCRIPT_EXTENSIONS

def is_youtube_url(url):
    """Check if URL is a valid YouTube URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
    return re.match(youtube_regex, url) is not None

def sanitize_filename(filename):
    """
    Sanitize filename to remove problematic characters
    Converts Unicode to ASCII and removes special characters
    """
    # Normalize Unicode characters to ASCII equivalents
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')

    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)

    # Trim whitespace
    filename = filename.strip()

    return filename

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle video file upload and transcription"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_video_file(file.filename):
            return jsonify({'error': 'Invalid file type. Supported formats: ' + ', '.join(ALLOWED_VIDEO_EXTENSIONS)}), 400

        # Get transcription options
        model_size = request.form.get('model_size', 'base')
        language = request.form.get('language', 'auto')

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Initialize transcriber
        transcriber = VideoTranscriber(
            model_size=model_size,
            language=None if language == 'auto' else language
        )

        # Transcribe video
        result = transcriber.transcribe(upload_path)

        # Get base filename without extension and sanitize it
        base_filename = os.path.splitext(filename)[0]
        base_filename = sanitize_filename(base_filename)

        # Generate all output formats
        output_files = transcriber.save_all_formats(
            result,
            base_filename,
            app.config['TRANSCRIPT_FOLDER']
        )

        # Clean up uploaded file
        os.remove(upload_path)

        return jsonify({
            'success': True,
            'files': output_files,
            'text': result['text'][:500] + '...' if len(result['text']) > 500 else result['text'],
            'full_text': result['text']
        })

    except Exception as e:
        app.logger.error(f"Transcription error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

@app.route('/youtube', methods=['POST'])
def transcribe_youtube():
    """Handle YouTube URL transcription"""
    try:
        data = request.get_json()
        youtube_url = data.get('url', '').strip()

        if not youtube_url:
            return jsonify({'error': 'No YouTube URL provided'}), 400

        if not is_youtube_url(youtube_url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Get transcription options
        model_size = data.get('model_size', 'base')
        language = data.get('language', 'auto')

        # Try to download captions first
        downloader = YouTubeDownloader(app.config['UPLOAD_FOLDER'])
        caption_result = downloader.download_captions(youtube_url)

        if caption_result:
            # Captions found! Use transcript converter
            print("Using existing captions")

            # Parse the VTT file
            converter = TranscriptConverter()
            result = converter.parse_vtt(caption_result['file_path'])

            # Get base filename without extension and sanitize it
            base_filename = os.path.splitext(os.path.basename(caption_result['file_path']))[0]
            # Remove the .en suffix from the filename
            base_filename = base_filename.replace('.en', '')
            base_filename = sanitize_filename(base_filename)

            # Convert to HTML (this will use camelCase filename internally)
            html_path = converter.convert_to_html(
                result,
                base_filename,
                app.config['TRANSCRIPT_FOLDER']
            )

            # Convert filename to camelCase for other formats
            from transcription_processor import VideoTranscriber
            camel_case_filename = VideoTranscriber._to_camel_case(base_filename)

            # Also save as TXT and SRT for completeness
            txt_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], f"{camel_case_filename}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])

            # Copy the VTT file to transcripts folder
            import shutil
            vtt_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], f"{camel_case_filename}.vtt")
            shutil.copy(caption_result['file_path'], vtt_path)

            # Create SRT from VTT
            srt_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], f"{camel_case_filename}.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result['segments'], start=1):
                    start_time = VideoTranscriber._format_srt_time(segment['start'])
                    end_time = VideoTranscriber._format_srt_time(segment['end'])
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text'].strip()}\n\n")

            output_files = {
                'txt': os.path.basename(txt_path),
                'srt': os.path.basename(srt_path),
                'vtt': os.path.basename(vtt_path),
                'html': os.path.basename(html_path)
            }

            # Clean up downloaded caption file
            os.remove(caption_result['file_path'])

            return jsonify({
                'success': True,
                'files': output_files,
                'title': caption_result['title'],
                'text': result['text'][:500] + '...' if len(result['text']) > 500 else result['text'],
                'full_text': result['text'],
                'source': 'captions'
            })

        # No captions available, fall back to Whisper transcription
        print("No captions found, transcribing with Whisper...")
        download_result = downloader.download(youtube_url)

        # Initialize transcriber
        transcriber = VideoTranscriber(
            model_size=model_size,
            language=None if language == 'auto' else language
        )

        # Transcribe video
        result = transcriber.transcribe(download_result['file_path'])

        # Get base filename without extension and sanitize it
        base_filename = os.path.splitext(os.path.basename(download_result['file_path']))[0]
        base_filename = sanitize_filename(base_filename)

        # Generate all output formats with video metadata
        output_files = transcriber.save_all_formats(
            result,
            base_filename,
            app.config['TRANSCRIPT_FOLDER'],
            video_url=download_result.get('url'),
            video_author=download_result.get('author')
        )

        # Clean up downloaded file
        os.remove(download_result['file_path'])

        return jsonify({
            'success': True,
            'files': output_files,
            'title': download_result['title'],
            'text': result['text'][:500] + '...' if len(result['text']) > 500 else result['text'],
            'full_text': result['text'],
            'source': 'whisper'
        })

    except Exception as e:
        app.logger.error(f"YouTube transcription error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'YouTube transcription failed: {str(e)}'}), 500

@app.route('/convert', methods=['POST'])
def convert_transcript():
    """Convert existing transcript to HTML"""
    try:
        if 'transcript' not in request.files:
            return jsonify({'error': 'No transcript file uploaded'}), 400

        file = request.files['transcript']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_transcript_file(file.filename):
            return jsonify({'error': 'Invalid file type. Supported formats: TXT, SRT, VTT'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Get file extension and sanitize filename
        ext = os.path.splitext(filename)[1].lower()
        base_filename = os.path.splitext(filename)[0]
        base_filename = sanitize_filename(base_filename)

        # Get optional video metadata from form
        video_title = request.form.get('videoTitle', '').strip()
        video_url = request.form.get('videoUrl', '').strip()
        video_author = request.form.get('videoAuthor', '').strip()

        # Use video title as base filename if provided
        if video_title:
            base_filename = sanitize_filename(video_title)

        # Parse transcript based on format
        converter = TranscriptConverter()

        if ext == '.srt':
            result = converter.parse_srt(upload_path)
        elif ext == '.vtt':
            result = converter.parse_vtt(upload_path)
        elif ext == '.txt':
            result = converter.parse_txt(upload_path)
        else:
            return jsonify({'error': 'Unsupported transcript format'}), 400

        # Convert to HTML with video metadata
        html_path = converter.convert_to_html(
            result,
            base_filename,
            app.config['TRANSCRIPT_FOLDER'],
            video_url=video_url if video_url else None,
            video_author=video_author if video_author else None
        )

        # Clean up uploaded file
        os.remove(upload_path)

        return jsonify({
            'success': True,
            'html_file': os.path.basename(html_path),
            'text': result['text'][:500] + '...' if len(result['text']) > 500 else result['text'],
            'full_text': result['text']
        })

    except Exception as e:
        app.logger.error(f"Conversion error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/edit', methods=['POST'])
def edit_transcript():
    """Handle edited transcript and regenerate all formats"""
    try:
        data = request.get_json()
        edited_text = data.get('text', '').strip()
        title = data.get('title', 'Edited Transcript')
        video_url = data.get('video_url')
        video_author = data.get('video_author')

        if not edited_text:
            return jsonify({'error': 'No text provided'}), 400

        # Sanitize title for filename
        base_filename = sanitize_filename(title)

        # Parse edited text as plain text transcript
        converter = TranscriptConverter()
        result = converter.parse_txt_from_string(edited_text)

        # Convert filename to camelCase
        from transcription_processor import VideoTranscriber
        camel_case_filename = VideoTranscriber._to_camel_case(base_filename)

        # Save as TXT
        txt_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], f"{camel_case_filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(edited_text)

        # Save as SRT (with fake timestamps)
        srt_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], f"{camel_case_filename}.srt")
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result['segments'], start=1):
                start_time = VideoTranscriber._format_srt_time(segment['start'])
                end_time = VideoTranscriber._format_srt_time(segment['end'])
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        # Save as VTT (with fake timestamps)
        vtt_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], f"{camel_case_filename}.vtt")
        with open(vtt_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for segment in result['segments']:
                start_time = VideoTranscriber._format_vtt_time(segment['start'])
                end_time = VideoTranscriber._format_vtt_time(segment['end'])
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        # Convert to HTML with video metadata
        html_path = converter.convert_to_html(
            result,
            base_filename,
            app.config['TRANSCRIPT_FOLDER'],
            video_url=video_url,
            video_author=video_author
        )

        output_files = {
            'txt': os.path.basename(txt_path),
            'srt': os.path.basename(srt_path),
            'vtt': os.path.basename(vtt_path),
            'html': os.path.basename(html_path)
        }

        return jsonify({
            'success': True,
            'files': output_files,
            'title': title,
            'text': edited_text[:500] + '...' if len(edited_text) > 500 else edited_text,
            'full_text': edited_text
        })

    except Exception as e:
        app.logger.error(f"Edit error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Failed to save edits: {str(e)}'}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a transcript file"""
    try:
        # Don't use secure_filename here - filenames are already sanitized when saved
        file_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/view/<path:filename>')
def view_file(filename):
    """View HTML transcript in browser"""
    try:
        # Don't use secure_filename here - filenames are already sanitized when saved
        file_path = os.path.join(app.config['TRANSCRIPT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content
    except Exception as e:
        app.logger.error(f"View error: {str(e)}")
        return jsonify({'error': 'View failed'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TRANSCRIPT_FOLDER'], exist_ok=True)

    print("Starting Video Transcription Tool...")
    print("Open http://localhost:5001 in your browser")
    app.run(debug=True, port=5001)
