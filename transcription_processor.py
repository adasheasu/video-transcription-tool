"""
Video Transcription Processor using OpenAI Whisper
Supports multiple output formats: TXT, SRT, VTT, HTML
"""
import os
import whisper
from datetime import timedelta
from typing import Dict, List, Optional

class VideoTranscriber:
    """Handles video transcription using OpenAI Whisper"""

    def __init__(self, model_size: str = 'base', language: Optional[str] = None):
        """
        Initialize transcriber with Whisper model

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (e.g., 'en', 'es', 'fr') or None for auto-detect
        """
        self.model_size = model_size
        self.language = language
        print(f"Loading Whisper model: {model_size}...")
        self.model = whisper.load_model(model_size)
        print("Model loaded successfully!")

    def transcribe(self, video_path: str) -> Dict:
        """
        Transcribe video or audio file

        Args:
            video_path: Path to video/audio file

        Returns:
            Dict with transcription results including text and segments
        """
        print(f"Transcribing: {video_path}")

        # Transcribe with word-level timestamps
        result = self.model.transcribe(
            video_path,
            language=self.language,
            word_timestamps=True,
            verbose=False
        )

        print(f"Transcription complete! Detected language: {result.get('language', 'unknown')}")
        return result

    def save_all_formats(self, result: Dict, base_filename: str, output_dir: str,
                         video_url: str = None, video_author: str = None) -> Dict[str, str]:
        """
        Save transcription in all supported formats

        Args:
            result: Whisper transcription result
            base_filename: Base filename without extension
            output_dir: Directory to save files

        Returns:
            Dict mapping format names to filenames
        """
        os.makedirs(output_dir, exist_ok=True)

        output_files = {}

        # Plain text format
        txt_file = self._save_txt(result, base_filename, output_dir)
        output_files['txt'] = os.path.basename(txt_file)

        # SRT subtitles
        srt_file = self._save_srt(result, base_filename, output_dir)
        output_files['srt'] = os.path.basename(srt_file)

        # VTT subtitles
        vtt_file = self._save_vtt(result, base_filename, output_dir)
        output_files['vtt'] = os.path.basename(vtt_file)

        # HTML format
        html_file = self._save_html(result, base_filename, output_dir, video_url, video_author)
        output_files['html'] = os.path.basename(html_file)

        return output_files

    def _save_txt(self, result: Dict, base_filename: str, output_dir: str) -> str:
        """Save as plain text file"""
        output_path = os.path.join(output_dir, f"{base_filename}.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])

        return output_path

    def _save_srt(self, result: Dict, base_filename: str, output_dir: str) -> str:
        """Save as SRT subtitle file"""
        output_path = os.path.join(output_dir, f"{base_filename}.srt")

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result['segments'], start=1):
                start_time = self._format_srt_time(segment['start'])
                end_time = self._format_srt_time(segment['end'])

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        return output_path

    def _save_vtt(self, result: Dict, base_filename: str, output_dir: str) -> str:
        """Save as VTT subtitle file"""
        output_path = os.path.join(output_dir, f"{base_filename}.vtt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")

            for segment in result['segments']:
                start_time = self._format_vtt_time(segment['start'])
                end_time = self._format_vtt_time(segment['end'])

                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        return output_path

    def _save_html(self, result: Dict, base_filename: str, output_dir: str,
                   video_url: str = None, video_author: str = None) -> str:
        """Save as accessible WCAG 2.2 AA compliant HTML file with timestamps"""
        # Convert filename to camelCase for HTML
        camel_case_filename = self._to_camel_case(base_filename)
        output_path = os.path.join(output_dir, f"{camel_case_filename}.html")

        # Break full text into paragraphs (split approximately every 3-4 sentences)
        full_text = result['text']
        paragraphs = self._split_into_paragraphs(full_text)

        # Calculate duration
        duration_seconds = result['segments'][-1]['end'] if result['segments'] else 0
        duration_formatted = self._format_duration(duration_seconds)

        # Build metadata HTML
        metadata_html = f'<p><strong>Duration:</strong> {duration_formatted}</p>'
        if video_url:
            metadata_html += f'<p><strong>Original video link:</strong> <a href="{video_url}" target="_blank" rel="noopener noreferrer">{base_filename}</a></p>'
        if video_author:
            metadata_html += f'<p><strong>Author:</strong> {video_author}</p>'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcript: {filename}</title>
    <style>
        /* ASU Brand Colors: Maroon #8C1D40, Gold #FFC627 */
        body {{
            font-family: Arial, "Helvetica Neue", sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #8C1D40;
            border-bottom: 3px solid #FFC627;
            padding-bottom: 10px;
            font-weight: bold;
        }}
        .metadata {{
            background: #FFF9E6;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #8C1D40;
        }}
        .metadata p {{
            margin: 5px 0;
            color: #191919;
        }}
        .full-text {{
            margin: 30px 0;
            padding: 20px;
            background: #FFF9E6;
            border-radius: 5px;
            border-left: 4px solid #FFC627;
        }}
        .full-text h2 {{
            margin-top: 0;
            color: #8C1D40;
            font-weight: bold;
        }}
        .segments {{
            margin: 30px 0;
        }}
        .segment {{
            margin: 15px 0;
            padding: 15px;
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            transition: all 0.2s;
        }}
        .segment:hover {{
            box-shadow: 0 2px 8px rgba(140, 29, 64, 0.2);
            border-color: #8C1D40;
        }}
        .timestamp {{
            display: inline-block;
            background: #8C1D40;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 10px;
            min-width: 80px;
            text-align: center;
        }}
        .text {{
            display: inline;
            color: #191919;
        }}
        .search-box {{
            margin: 20px 0;
            padding: 15px;
            background: #FFF9E6;
            border: 2px solid #8C1D40;
            border-radius: 5px;
        }}
        .search-box input {{
            width: 100%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #8C1D40;
            border-radius: 4px;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: #FFC627;
            box-shadow: 0 0 0 3px rgba(255, 198, 39, 0.3);
        }}
        .highlight {{
            background-color: #FFC627;
            font-weight: bold;
            color: #000;
        }}
        .full-text p {{
            margin-bottom: 1em;
            line-height: 1.8;
        }}
        /* Screen reader only class */
        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }}
        /* Skip link for accessibility */
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 0;
            background: #8C1D40;
            color: white;
            padding: 8px;
            text-decoration: none;
            z-index: 100;
        }}
        .skip-link:focus {{
            top: 0;
        }}
        /* WCAG 2.2 compliant focus indicators */
        a:focus, button:focus, input:focus {{
            outline: 3px solid #FFC627;
            outline-offset: 2px;
        }}
        .metadata a {{
            color: #8C1D40;
            text-decoration: underline;
        }}
        .metadata a:hover {{
            color: #6d1632;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
            .search-box, .skip-link {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <!-- Skip link for keyboard navigation -->
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <div class="container">
        <h1 id="main-content" tabindex="-1">Transcript: {filename}</h1>

        <div class="metadata" role="contentinfo" aria-label="Video information">
            {metadata}
        </div>

        <div class="search-box">
            <label for="searchInput" class="sr-only">Search transcript</label>
            <input type="text" id="searchInput" placeholder="Search transcript..." aria-label="Search transcript">
        </div>

        <div class="full-text">
            <h2>Full Transcript</h2>
            {paragraphs_html}
        </div>

        <h2>Timestamped Segments</h2>
        <div class="segments" id="segments" role="region" aria-label="Timestamped transcript segments">
""".format(
                filename=base_filename,
                metadata=metadata_html,
                paragraphs_html=''.join(f'<p>{p}</p>' for p in paragraphs)
            ))

            # Write segments
            for segment in result['segments']:
                start_time = self._format_display_time(segment['start'])
                text = segment['text'].strip()

                f.write(f"""            <div class="segment">
                <span class="timestamp">{start_time}</span>
                <span class="text">{text}</span>
            </div>
""")

            # Close HTML
            f.write("""        </div>
    </div>

    <script>
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const segments = document.getElementById('segments');
        const fullText = document.querySelector('.full-text');

        // Store original content
        const fullTextParagraphs = Array.from(fullText.querySelectorAll('p')).map(p => p.textContent);
        const segmentTexts = Array.from(segments.getElementsByClassName('segment')).map(seg => {
            const textSpan = seg.querySelector('.text');
            return textSpan ? textSpan.textContent : seg.textContent;
        });

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const segmentDivs = segments.getElementsByClassName('segment');

            if (searchTerm === '') {
                // Reset everything
                fullText.querySelectorAll('p').forEach((p, i) => {
                    p.innerHTML = fullTextParagraphs[i];
                });
                Array.from(segmentDivs).forEach((div, i) => {
                    div.style.display = 'block';
                    const textSpan = div.querySelector('.text');
                    if (textSpan) {
                        textSpan.textContent = segmentTexts[i];
                    }
                });
            } else {
                // Search and highlight in full text
                fullText.querySelectorAll('p').forEach((p, i) => {
                    const originalText = fullTextParagraphs[i];
                    if (originalText.toLowerCase().includes(searchTerm)) {
                        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
                        p.innerHTML = originalText.replace(regex, '<span class="highlight">$1</span>');
                    } else {
                        p.innerHTML = originalText;
                    }
                });

                // Search and highlight in segments
                Array.from(segmentDivs).forEach((div, i) => {
                    const text = div.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        div.style.display = 'block';
                        const textSpan = div.querySelector('.text');
                        if (textSpan) {
                            const originalText = segmentTexts[i];
                            const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
                            textSpan.innerHTML = originalText.replace(regex, '<span class="highlight">$1</span>');
                        }
                    } else {
                        div.style.display = 'none';
                    }
                });
            }
        });
    </script>
</body>
</html>
""")

        return output_path

    @staticmethod
    def _split_into_paragraphs(text: str, sentences_per_paragraph: int = 4) -> List[str]:
        """
        Split text into readable paragraphs

        Args:
            text: Full text to split
            sentences_per_paragraph: Approximate number of sentences per paragraph

        Returns:
            List of paragraph strings
        """
        import re

        # Split by sentence boundaries (., !, ?)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        paragraphs = []
        current_paragraph = []

        for i, sentence in enumerate(sentences):
            current_paragraph.append(sentence)

            # Create paragraph every N sentences or at the end
            if (i + 1) % sentences_per_paragraph == 0 or i == len(sentences) - 1:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []

        return paragraphs

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        millis = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format time for VTT format (HH:MM:SS.mmm)"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        millis = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _format_display_time(seconds: float) -> str:
        """Format time for display (MM:SS)"""
        td = timedelta(seconds=seconds)
        minutes = td.seconds // 60
        secs = td.seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def _to_camel_case(filename: str) -> str:
        """Convert filename to camelCase (PascalCase)"""
        import re
        # Remove special characters except spaces and alphanumeric
        filename = re.sub(r'[^\w\s]', '', filename)
        # Split by spaces and capitalize first letter of each word
        words = filename.split()
        # Join words with first letter capitalized
        camel_case = ''.join(word.capitalize() for word in words)
        return camel_case

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration for display"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcription_processor.py <video_file>")
        sys.exit(1)

    video_file = sys.argv[1]
    transcriber = VideoTranscriber(model_size='base')
    result = transcriber.transcribe(video_file)

    # Save all formats
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_files = transcriber.save_all_formats(result, base_name, 'output')

    print("\nTranscription saved in the following formats:")
    for format_name, filename in output_files.items():
        print(f"  - {format_name.upper()}: {filename}")
