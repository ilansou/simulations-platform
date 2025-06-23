from llm.ingest import get_embedding
import os
import time
from pymongo.operations import SearchIndexModel
from db_client import chat_collection, db_client

def setup_vector_search_index():
    """Setup MongoDB vector search index for the chat collection"""
    # Check if MongoDB connection is available
    if db_client is None or chat_collection is None:
        return False
    
    # Define the vector search index for 384-dimensional embeddings
    vector_index_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 384,  # all-MiniLM-L6-v2 produces 384-dimensional vectors
                "similarity": "cosine",
            }
        ]
    }
    
    # Create the search index
    try:
        # Check if index exists before trying to drop it
        existing_indices = list(chat_collection.list_search_indexes())
        index_exists = any(idx.get("name") == "vector_index" for idx in existing_indices)
        
        if index_exists:
            chat_collection.drop_search_index("vector_index")
        
        # Create new index
        search_index_model = SearchIndexModel(
            definition=vector_index_definition, 
            name="vector_index", 
            type="vectorSearch"
        )
        
        chat_collection.create_search_index(model=search_index_model)
        
        # Wait for index to be ready
        time.sleep(5)
        
        return True
    except Exception as e:
        return False

def get_all_multi_experiment_documents():
    """Retrieves ALL documents for multi-experiment comprehensive analysis"""
    if db_client is None:
        return []
    
    # Ensure the chat collection exists
    db = db_client["experiment_db"]
    if "chat" not in db.list_collection_names():
        return []
    
    try:
        # Get ALL documents that have experiment_name field (indicating multi-experiment data)
        pipeline = [
            {"$match": {"experiment_name": {"$exists": True, "$ne": ""}}},
            {"$project": {
                "_id": 0,
                "text": 1,
                "filename": 1,
                "experiment_name": 1,
                "experiment_id": 1,
                "experiment_params": 1
            }}
        ]
        
        results = list(chat_collection.aggregate(pipeline))
        return results
    
    except Exception as e:
        return []

def get_all_single_experiment_documents():
    """Retrieves ALL documents for single experiment comprehensive analysis"""
    if db_client is None:
        return []
    
    # Ensure the chat collection exists
    db = db_client["experiment_db"]
    if "chat" not in db.list_collection_names():
        return []
    
    try:
        # Get ALL documents that DON'T have experiment_name field (indicating single-experiment data)
        pipeline = [
            {"$match": {"experiment_name": {"$exists": False}}},
            {"$project": {
                "_id": 0,
                "text": 1,
                "filename": 1
            }}
        ]
        
        results = list(chat_collection.aggregate(pipeline))
        return results
    
    except Exception as e:
        return []

def get_query_results(query, limit=5):
    """Gets results from a vector search query using MongoDB vector search"""
    # Check database connection
    if db_client is None:
        return []
    
    # Ensure the chat collection exists
    db = db_client["experiment_db"]
    if "chat" not in db.list_collection_names():
        return []
    
    try:
        # Enhance query for better retrieval on basic statistics questions
        enhanced_query = query
        # For node-related queries, add terms to improve matching
        if "node" in query.lower() or "nodes" in query.lower():
            enhanced_query = f"{query} node_info.csv number of nodes count"
        # For bandwidth-related queries
        elif "bandwidth" in query.lower():
            enhanced_query = f"{query} flow_bandwidth.csv connection_bandwidth.csv average bandwidth"
        # For link-related queries
        elif "link" in query.lower() or "connection" in query.lower():
            enhanced_query = f"{query} link_utilization.csv connection_info.csv"
        # For general simulation questions
        elif "simulation" in query.lower():
            enhanced_query = f"{query} node_info.csv flow_info.csv link_utilization.csv"
            
        # Generate embedding for the user query
        query_embedding = get_embedding(enhanced_query)
        
        # Define the vector search pipeline
        vector_search_stage = {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": 100,  # Number of candidate matches to consider
                "limit": limit,  # Return top matches
            }
        }
        
        project_stage = {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "text": 1,  # Include the text field
                "filename": 1,  # Include the filename field
                "score": {"$meta": "vectorSearchScore"},  # Include the search score
            }
        }
        
        pipeline = [vector_search_stage, project_stage]
        
        # Execute the search
        results = list(chat_collection.aggregate(pipeline))
        return results
    
    except Exception as e:
        # Handle errors and fallback to simple retrieval if necessary
        try:
            documents = list(chat_collection.find({}, {"text": 1, "filename": 1, "_id": 0}).limit(limit))
            return documents
        except Exception as fallback_error:
            return []

# Testing function            
if __name__ == "__main__":
    setup_vector_search_index()
    results = get_query_results("What is the average bandwidth?")
