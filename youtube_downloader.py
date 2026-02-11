"""
YouTube Video Downloader for transcription
Uses yt-dlp to download videos/audio from YouTube
"""
import os
import yt_dlp
from typing import Dict

class YouTubeDownloader:
    """Downloads YouTube videos for transcription"""

    def __init__(self, output_dir: str = 'uploads'):
        """
        Initialize YouTube downloader

        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def download_captions(self, url: str) -> Dict:
        """
        Try to download captions from YouTube video

        Args:
            url: YouTube video URL

        Returns:
            Dict with caption info or None if no captions available
        """
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', info.get('channel', 'Unknown'))

                # Check if captions are available
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})

                if 'en' in subtitles or 'en' in automatic_captions:
                    print(f"Found captions for: {title}")
                    print(f"Duration: {duration} seconds")
                    print(f"Author: {uploader}")
                    print("Downloading captions...")

                    # Download captions
                    info = ydl.extract_info(url, download=True)

                    # Find the VTT caption file
                    base_filename = ydl.prepare_filename(info)
                    base_filename = os.path.splitext(base_filename)[0]
                    vtt_filename = f"{base_filename}.en.vtt"

                    if os.path.exists(vtt_filename):
                        return {
                            'file_path': vtt_filename,
                            'title': title,
                            'duration': duration,
                            'url': url,
                            'author': uploader,
                            'source': 'captions'
                        }

                print("No captions available, will need to transcribe audio")
                return None

        except Exception as e:
            print(f"Could not download captions: {str(e)}")
            return None

    def download(self, url: str) -> Dict[str, str]:
        """
        Download YouTube video audio

        Args:
            url: YouTube video URL

        Returns:
            Dict with file path, title, and duration
        """
        # Configure yt-dlp options for audio extraction
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', info.get('channel', 'Unknown'))

                print(f"Downloading: {title}")
                print(f"Duration: {duration} seconds")
                print(f"Author: {uploader}")

                # Download audio
                info = ydl.extract_info(url, download=True)

                # Get the actual filename (yt-dlp may sanitize the title)
                filename = ydl.prepare_filename(info)
                # Change extension to mp3 since we're extracting audio
                filename = os.path.splitext(filename)[0] + '.mp3'

                return {
                    'file_path': filename,
                    'title': title,
                    'duration': duration,
                    'url': url,
                    'author': uploader,
                    'source': 'audio'
                }

        except Exception as e:
            raise Exception(f"Failed to download YouTube video: {str(e)}")

    def get_video_info(self, url: str) -> Dict:
        """
        Get video information without downloading

        Args:
            url: YouTube video URL

        Returns:
            Dict with video metadata
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')
                }
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python youtube_downloader.py <youtube_url>")
        sys.exit(1)

    url = sys.argv[1]
    downloader = YouTubeDownloader()

    print("Getting video info...")
    info = downloader.get_video_info(url)
    print(f"Title: {info['title']}")
    print(f"Duration: {info['duration']} seconds")

    print("\nDownloading...")
    result = downloader.download(url)
    print(f"Downloaded to: {result['file_path']}")
