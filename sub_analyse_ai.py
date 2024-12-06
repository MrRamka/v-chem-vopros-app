import json
import os

from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, \
    ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def analyze_content(transcript):
    # API ключи и настройки
    API_KEY = os.environ.get("GPT_API_KEY")
    BASE_URL = "https://api.aitunnel.ru/v1"

    # Инициализация моделей
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        openai_api_key=API_KEY,
        temperature=0,
        request_timeout=180,
        openai_api_base=BASE_URL
    )

    llm3 = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        openai_api_key=API_KEY,
        temperature=0,
        request_timeout=180,
        openai_api_base=BASE_URL
    )

    map_template = """
    Вы - полезный ассистент, который помогает извлекать темы из транскрипции видео
    - Ваша цель - выделить названия тем и краткое описание каждой темы в одном предложении
    - Темы включают:
      - Основные идеи
      - Бизнес-идеи
      - Интересные истории
      - Прибыльные бизнес-модели
      - Короткие истории о людях
      - Ментальные модели и концепции
      - Истории об отраслях
      - Упомянутые аналогии
      - Советы или предостережения
      - Новости или текущие события
      - И другие
    - Предоставьте краткое описание тем после названия темы. Пример: 'Тема: Краткое описание'
    - Используйте те же слова и терминологию, которые используются в видео
    - Не отвечайте ничем, что не упоминается в видео. Если тем нет, напишите 'Тем нет'
    - Используйте только маркированные списки, без нумерации
    - Делайте названия тем описательными, но краткими

    Текст для анализа: {text}
    """

    reduce_template = """
    Вы - полезный ассистент, который помогает извлекать темы из транскрипции подкаста/видео
    - Вам будет предоставлен список маркированных тем, найденных ранее
    - Ваша цель - извлечь названия тем и краткое описание каждой темы в одном предложении
    - Удалить любые повторяющиеся пункты
    - Использовать только темы из транскрипции

    Объедините следующие темы, удалив дубликаты и сохранив структуру маркированного списка:

    {text}
    """

    structure_template = """
    Преобразуйте следующий список тем в структурированный json формат. Для каждой темы (topics) укажите:
    topic_name: название темы (текст до двоеточия)
    description: описание темы (текст после двоеточия)
    tag: категория темы

    Предоставьте ответ в формате строго структурированного json текста, без дополнительных комментариев.

    Текст для структурирования:
    {text}
    """

    # Создание цепочек
    map_prompt = PromptTemplate.from_template(map_template)
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    structure_prompt = PromptTemplate.from_template(structure_template)

    map_chain = map_prompt | llm | StrOutputParser()
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    structure_chain = structure_prompt | llm3 | StrOutputParser()

    # Анализ текста
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " "],
        chunk_size=10000,
        chunk_overlap=2200
    )

    text_chunks = text_splitter.split_text(transcript)
    mapped_results = [map_chain.invoke({"text": chunk}) for chunk in text_chunks]
    combined_results = "\n\n".join(mapped_results)
    final_result = reduce_chain.invoke({"text": combined_results})
    topics_structured = structure_chain.invoke({"text": final_result})

    # Поиск временных меток
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=800)
    docs = text_splitter.create_documents([transcript])
    embeddings = OpenAIEmbeddings(openai_api_key=API_KEY, openai_api_base=BASE_URL)
    docsearch = Chroma.from_documents(docs, embeddings)

    system_template = """
    Какая первая временная метка, когда спикеры начали говорить о теме, которую укажет пользователь?
    Отвечайте только временной меткой, ничего больше. Пример: 00:18:24
    ----------------
    {context}
    """

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
    CHAT_PROMPT = ChatPromptTemplate.from_messages(messages)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=docsearch.as_retriever(k=10000),
        chain_type_kwargs={'prompt': CHAT_PROMPT}
    )

    topic_timestamps = []
    for topic in json.loads(topics_structured)['topics']:
        query = f"{topic['topic_name']} - {topic['description']}"
        timestamp = qa.invoke(query)
        topic_timestamps.append({
            "timestamp": timestamp['result'],
            "topic_name": topic['topic_name'],
            "description": topic['description'],
            "tag": topic['tag']
        })

    return json.loads(topics_structured), topic_timestamps


if __name__ == "__main__":
    # Тестирование функции
    with open('downloads/.txt', 'r', encoding='utf-8') as file:
        transcript = file.read()

    topics, timestamps = analyze_content(transcript)
    print("\nСтруктурированные темы:")
    print(json.dumps(topics, ensure_ascii=False, indent=2))
    print("\nВременные метки:")
    for item in sorted(timestamps, key=lambda x: x['timestamp']):
        print(f"{item['timestamp']} - {item['topic_name']}")
