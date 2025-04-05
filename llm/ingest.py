import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from db_client import chat_collection, db_client
import warnings

warnings.filterwarnings("ignore", message=".*torch.classes.*")

# Initialize embedding model - use the same model as in the example
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # 384-dimensional embeddings

# Define a function to generate embeddings
def get_embedding(data):
    """Generates vector embeddings for the given data."""
    embedding = model.encode(data)
    return embedding.tolist()

def process_and_store_data(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        embedding = model.encode(content).tolist()
        
        # Include filename in the document
        filename = os.path.basename(file_path)
        document = {
            "text": content,
            "embedding": embedding,
            "filename": filename,
            "file_path": file_path
        }
        
        # Ensure the collection exists
        if chat_collection is None:
            raise ValueError("Chat collection is not available. Database connection may have failed.")
        
        chat_collection.insert_one(document)

def process_simulation_output(run_dir):
    """Process all simulation output files from a run directory.
    
    Args:
        run_dir (str): Path to the simulation run directory
        
    Returns:
        list: List of successfully processed filenames
    """
    # Ensure MongoDB connection is available
    if db_client is None or chat_collection is None:
        print("MongoDB connection not available")
        return []
    
    # Drop and recreate the collection to avoid dimension conflicts
    db = db_client["experiment_db"]
    if "chat" in db.list_collection_names():
        print("Dropping existing 'chat' collection to avoid dimension conflicts")
        db.drop_collection("chat")
    
    print("Creating 'chat' collection in experiment_db")
    db.create_collection("chat")
    
    output_files = [
        "flow_bandwidth.csv",
        "flow_info.csv",
        "link_utilization.csv",
        "node_info.csv",
        "connection_bandwidth.csv",
        "connection_info.csv"
    ]
    
    processed_files = []
    
    for filename in output_files:
        file_path = os.path.join(run_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                process_and_store_data(file_path)
                processed_files.append(filename)
                print(f"Successfully processed {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    return processed_files

# Example usage
#process_and_store_data('path_to_your_output_file.txt')
#process_simulation_output('/path/to/run_dir')
