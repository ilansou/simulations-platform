# db_client.py
import os
import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_db_client():
    """
    Возвращает *единый* объект MongoClient, кешируемый Streamlit
    (доступен для всех скриптов и сохраняется между рендерами).
    """
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    # Если у вас локально: "mongodb://host.docker.internal:27017",
    # или замените на нужный URI
    return MongoClient(mongo_uri)

# создаём клиента один раз
db_client = get_db_client()

# создаём/берём базу и коллекцию
db = db_client["experiment_db"]
experiments_collection = db["experiments"]
