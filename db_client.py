import os
from dotenv import load_dotenv
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Load environment variables from .env file
load_dotenv()

@st.cache_resource
def get_db_client():
    """
    Returns a cached MongoClient object with proper error handling
    """
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        st.error("MongoDB URI not found in environment variables!")
        return None

    try:
        # Create client with increased timeout
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command('ping')
        st.success("Successfully connected to MongoDB!")
        return client
    except ServerSelectionTimeoutError as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error while connecting to MongoDB: {e}")
        return None

# Create the client
db_client = get_db_client()

if db_client:
    db = db_client["experiment_db"]
    experiments_collection = db["experiments"]
    chat_collection = db["chat"]  
else:
    st.error("Could not initialize database connection!")
    experiments_collection = None
    chat_collection = None
