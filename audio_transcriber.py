import os

from transformers import pipeline
import torch


class AudioTranscriber:
    def __init__(self, audio_path, interval=10):
        self.audio_path = audio_path
        self.interval = interval
        self.ffmpeg_path = os.environ.get("FFMPEG_PATH")
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.asr_pipeline = pipeline("automatic-speech-recognition",
                                     model=os.environ.get("MODEL_NAME"),
                                     device=self.device,
                                     chunk_length_s=self.interval,
                                     stride_length_s = (4, 2)
                                     )

    def transcribe_audio(self):
        transcription = self.asr_pipeline(self.audio_path, return_timestamps=True)

        return transcription["chunks"]
