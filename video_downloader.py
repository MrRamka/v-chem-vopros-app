import os
import yt_dlp
import hashlib



def generate_hash(string):
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


class VideoDownloader:
    def __init__(self, url):
        self.url = url
        self.ffmpeg_path = os.environ.get("FFMPEG_PATH")
        self.output_path = os.environ.get("DOWNLOAD_PATH")

    def download_video(self):
        hash_name = generate_hash(self.url)

        # Настройки для загрузки только аудио
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.output_path, f"{hash_name}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "ffmpeg_location": self.ffmpeg_path,  # Указываем путь к FFmpeg
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=True)
            file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            return file_path