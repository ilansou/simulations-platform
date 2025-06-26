import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from db_client import chat_collection, db_client
import warnings
import glob

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
        return []
    
    # If run_dir is a relative path, convert it to absolute using FLOODNS_ROOT
    if not os.path.isabs(run_dir):
        from conf import FLOODNS_ROOT
        run_dir = os.path.join(FLOODNS_ROOT, run_dir)
    
    # Drop and recreate the collection to avoid dimension conflicts
    db = db_client["experiment_db"]
    if "chat" in db.list_collection_names():
        db.drop_collection("chat")
    
    db.create_collection("chat")
    
    # All expected CSV files from FloodNS framework documentation
    output_files = [
        "flow_bandwidth.csv",
        "flow_info.csv",
        "link_info.csv",
        "link_num_active_flows.csv",
        "link_utilization.csv",
        "node_info.csv",
        "node_num_active_flows.csv",
        "connection_bandwidth.csv",
        "connection_info.csv"
    ]
    
    processed_files = []
    
    # Automatically detect and process all CSV files in the run directory
    csv_files = glob.glob(os.path.join(run_dir, "*.csv"))
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        try:
            process_and_store_data(file_path)
            processed_files.append(filename)
        except Exception as e:
            pass
    
    return processed_files

# Example usage
#process_and_store_data('path_to_your_output_file.txt')
#process_simulation_output('/path/to/run_dir')
