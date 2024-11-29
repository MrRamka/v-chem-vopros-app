## Установка и запуск

### Windows
1. Ставим зависимости проекта `pip install -r requirements.txt`
2. Ставим ffmpeg https://github.com/BtbN/FFmpeg-Builds/releases
3. В `.env` добавляем путь до бинарников
4. Добавить `FFMPEG_BIN` в переменный окружения системы
5. `streamlit run app.py`

### Mac
1. Ставим зависимости проекта `pip install -r requirements.txt`
2. `brew install ffmpeg`
3. `streamlit run app.py`