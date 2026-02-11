"""
Transcript Converter - Convert existing transcripts to HTML with ASU branding
Supports TXT, SRT, VTT formats
"""
import os
import re
from typing import Dict, List, Optional
from datetime import timedelta

class TranscriptConverter:
    """Convert existing transcripts to accessible HTML format"""

    @staticmethod
    def parse_srt(file_path: str) -> Dict:
        """
        Parse SRT subtitle file

        Args:
            file_path: Path to SRT file

        Returns:
            Dict with segments and full text
        """
        segments = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by double newlines (SRT format)
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Line 0: sequence number
                # Line 1: timestamp
                # Line 2+: text
                timestamp_line = lines[1]
                text = ' '.join(lines[2:])

                # Parse timestamp: 00:00:00,000 --> 00:00:05,000
                match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_line)
                if match:
                    start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
                    end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])

                    start_seconds = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                    end_seconds = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000

                    segments.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': text.strip()
                    })

        full_text = ' '.join(seg['text'] for seg in segments)

        return {
            'segments': segments,
            'text': full_text,
            'language': 'unknown'
        }

    @staticmethod
    def parse_vtt(file_path: str) -> Dict:
        """
        Parse VTT subtitle file

        Args:
            file_path: Path to VTT file

        Returns:
            Dict with segments and full text
        """
        segments = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove WEBVTT header
        content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)

        # Split by double newlines
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 2:
                # Line 0: timestamp (or id + timestamp)
                # Line 1+: text

                # Find the timestamp line
                timestamp_line = None
                text_start_idx = 1

                if '-->' in lines[0]:
                    timestamp_line = lines[0]
                elif len(lines) > 1 and '-->' in lines[1]:
                    timestamp_line = lines[1]
                    text_start_idx = 2

                if timestamp_line:
                    text = ' '.join(lines[text_start_idx:])

                    # Parse timestamp: 00:00:00.000 --> 00:00:05.000
                    match = re.match(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})', timestamp_line)
                    if match:
                        start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
                        end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])

                        start_seconds = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                        end_seconds = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000

                        segments.append({
                            'start': start_seconds,
                            'end': end_seconds,
                            'text': text.strip()
                        })

        full_text = ' '.join(seg['text'] for seg in segments)

        return {
            'segments': segments,
            'text': full_text,
            'language': 'unknown'
        }

    @staticmethod
    def parse_txt(file_path: str) -> Dict:
        """
        Parse plain text transcript file

        Args:
            file_path: Path to TXT file

        Returns:
            Dict with text (no segments)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()

        return TranscriptConverter.parse_txt_from_string(text)

    @staticmethod
    def parse_txt_from_string(text: str) -> Dict:
        """
        Parse plain text transcript from string

        Args:
            text: Transcript text

        Returns:
            Dict with text and segments
        """
        text = text.strip()

        # Try to split into paragraphs for segments
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if not paragraphs:
            paragraphs = [text]

        # Create fake segments (no timestamps)
        segments = []
        for i, para in enumerate(paragraphs):
            segments.append({
                'start': i * 10,  # Fake timestamp
                'end': (i + 1) * 10,
                'text': para
            })

        return {
            'segments': segments,
            'text': text,
            'language': 'unknown'
        }

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
    def convert_to_html(result: Dict, base_filename: str, output_dir: str,
                       video_url: str = None, video_author: str = None) -> str:
        """
        Convert transcript to ASU-branded HTML

        Args:
            result: Parsed transcript dict
            base_filename: Base filename without extension
            output_dir: Directory to save HTML file
            video_url: Optional video URL
            video_author: Optional video author

        Returns:
            Path to HTML file
        """
        os.makedirs(output_dir, exist_ok=True)
        # Convert filename to camelCase for HTML
        camel_case_filename = TranscriptConverter._to_camel_case(base_filename)
        output_path = os.path.join(output_dir, f"{camel_case_filename}.html")

        has_timestamps = result['segments'] and result['segments'][0].get('start', 0) > 0

        # Break full text into paragraphs
        paragraphs = TranscriptConverter._split_into_paragraphs(result['text'])

        # Build metadata HTML if video metadata is provided
        metadata_html = ''
        if video_url or video_author:
            metadata_html = '<div class="metadata" role="contentinfo" aria-label="Video information">'
            if video_url:
                metadata_html += f'<p><strong>Original video link:</strong> <a href="{video_url}" target="_blank" rel="noopener noreferrer">{base_filename}</a></p>'
            if video_author:
                metadata_html += f'<p><strong>Author:</strong> {video_author}</p>'
            metadata_html += '</div>'

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

        {metadata}

        <div class="search-box">
            <label for="searchInput" class="sr-only">Search transcript</label>
            <input type="text" id="searchInput" placeholder="Search transcript..." aria-label="Search transcript">
        </div>

        <div class="full-text">
            <h2>Full Transcript</h2>
            {paragraphs_html}
        </div>

        <h2>Transcript Segments</h2>
        <div class="segments" id="segments" role="region" aria-label="Transcript segments">
""".format(
                filename=base_filename,
                metadata=metadata_html,
                paragraphs_html=''.join(f'<p>{p}</p>' for p in paragraphs)
            ))

            # Write segments
            for segment in result['segments']:
                if has_timestamps:
                    start_time = TranscriptConverter._format_display_time(segment['start'])
                    f.write(f"""            <div class="segment">
                <span class="timestamp">{start_time}</span>
                <span class="text">{segment['text'].strip()}</span>
            </div>
""")
                else:
                    f.write(f"""            <div class="segment">
                <span class="text">{segment['text'].strip()}</span>
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


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcript_converter.py <transcript_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    converter = TranscriptConverter()

    # Determine file type
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.srt':
        result = converter.parse_srt(file_path)
    elif ext == '.vtt':
        result = converter.parse_vtt(file_path)
    elif ext == '.txt':
        result = converter.parse_txt(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        sys.exit(1)

    # Convert to HTML
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    html_path = converter.convert_to_html(result, base_name, 'output')

    print(f"Converted to HTML: {html_path}")
