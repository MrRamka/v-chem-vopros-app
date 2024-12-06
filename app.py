import streamlit as st
from os.path import join, dirname
from dotenv import load_dotenv

from audio_transcriber import AudioTranscriber
from video_downloader import VideoDownloader
from sub_analyse_ai import analyze_content


def seconds_to_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

st.title("Обработка видео с YouTube")

video_url = st.text_input("Введите ссылку на видео с YouTube:")
interval = st.slider("Выберите интервал временных отметок (в секундах):",
                     min_value=5, max_value=30, value=15, step=5)
upload_button = st.button("Начать обработку", type="primary")

if upload_button:
    if video_url:
        # Скачивание видео
        with st.spinner("Скачиваю видео..."):
            try:
                downloader = VideoDownloader(video_url)
                audio_path = downloader.download_video()
                st.success("Видео успешно скачано!")
            except Exception as e:
                st.error(f"Ошибка при скачивании видео: {e}")
                st.stop()

        # Транскрипция
        with st.spinner("Преобразую аудио в текст..."):
            try:
                transcriber = AudioTranscriber(audio_path, interval)
                transcription_result = transcriber.transcribe_audio()
                st.success("Транскрипция завершена!")
            except Exception as e:
                st.error(f"Ошибка при транскрипции: {e}")
                st.stop()

        # Запись транскрипции в файл
        with open('downloads/sub.txt', 'w', encoding='utf-8') as f1:
            full_transcript = ""
            for entry in transcription_result:
                start_time, end_time = entry['timestamp']
                text = entry['text']
                start_formatted = seconds_to_timestamp(start_time)
                end_formatted = seconds_to_timestamp(end_time)
                line = f"({start_formatted}-{end_formatted}): {text}\n"
                f1.write(line)
                full_transcript += line

        # Анализ контента
        with st.spinner("Анализирую содержание..."):
            try:
                topics, timestamps = analyze_content(full_transcript)
                st.success("Анализ завершен!")
            except Exception as e:
                st.error(f"Ошибка при анализе контента: {e}")
                st.stop()

        # Использование вкладок для отображения результатов
        tab1, tab2 = st.tabs(["⏰ Временные линии", "📝 Транскрипция"])

        with tab1:
            st.header("⏰ Временные линии")
            for item in sorted(timestamps, key=lambda x: x['timestamp']):
                with st.expander(f"🕒 {item['timestamp']} - {item['topic_name']}", expanded=True):
                    st.markdown(f"**Описание:** _{item['description']}_")
                    st.markdown(f"**Категория:** `{item['tag']}`")

        with tab2:
            st.header("📝 Транскрипция")
            for entry in transcription_result:
                start_time, end_time = entry['timestamp']
                text = entry['text']
                start_formatted = seconds_to_timestamp(start_time)
                end_formatted = seconds_to_timestamp(end_time)
                st.markdown(f"**({start_formatted}-{end_formatted}):** {text}")

    else:
        st.error("Пожалуйста, введите ссылку на видео.")
