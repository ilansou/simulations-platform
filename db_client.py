import os
import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_db_client():
    """
    Returns a single MongoClient object, cached by Streamlit.
    This client is available for all scripts and persists between renders.
    """
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    # If running locally, you might use: "mongodb://host.docker.internal:27017"
    # Replace with the appropriate URI if needed
    return MongoClient(mongo_uri)

# Create the client once
db_client = get_db_client()

# Create/get the database and collection
db = db_client["experiment_db"]
experiments_collection = db["experiments"]
