import streamlit as st
from os.path import join, dirname
from dotenv import load_dotenv

from audio_transcriber import AudioTranscriber
from video_downloader import VideoDownloader


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

st.title("Обработка видео с YouTube")

video_url = st.text_input("Введите ссылку на видео с YouTube:")
interval = st.slider("Выберите интервал временных отметок (в секундах):", min_value=5, max_value=30, value=10, step=5)
upload_button = st.button("Начать обработку", type="primary")

if upload_button:
    if video_url:
        with st.spinner("Скачиваю видео..."):
            try:
                downloader = VideoDownloader(video_url)
                audio_path = downloader.download_video()
                st.success("Видео успешно скачано!")
            except Exception as e:
                st.error(f"Ошибка при скачивании видео: {e}")
                st.stop()

        with st.spinner("Преобразую аудио в текст..."):
            try:
                transcriber = AudioTranscriber(audio_path, interval)
                transcription_result = transcriber.transcribe_audio()
                st.success("Транскрипция завершена!")
            except Exception as e:
                st.error(f"Ошибка при транскрипции: {e}")
                st.stop()

        st.header("Результаты транскрипции:")
        for entry in transcription_result:
            start_time, end_time = entry['timestamp']
            text = entry['text']

            st.markdown(f"**{start_time:.2f}s - {end_time:.2f}s:** {text}")
    else:
        st.error("Пожалуйста, введите ссылку на видео.")