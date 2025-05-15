import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

try:
    from db_client import db_client
    # Check MongoDB connection immediately
    if db_client is None:
        print("Error: MongoDB connection is not available")
        print("Please check your MONGODB_URI environment variable and MongoDB server")
        sys.exit(1)
except Exception as e:
    print(f"Error importing db_client: {e}")
    print("Please ensure MongoDB is running and MONGODB_URI is set in your .env file")
    sys.exit(1)

from llm.ingest import process_simulation_output
from llm.retrieval import setup_vector_search_index

def fix_chat_functionality():
    """Function to diagnose and fix chat functionality issues"""
    print("MongoDB connection: OK")
    
    # Check if the chat collection exists
    db = db_client["experiment_db"]
    collections = db.list_collection_names()
    if "chat" in collections:
        print("Chat collection exists: YES")
        doc_count = db["chat"].count_documents({})
        print(f"Documents in chat collection: {doc_count}")
        
        # Check if documents have embeddings
        docs_with_embedding = db["chat"].count_documents({"embedding": {"$exists": True}})
        print(f"Documents with embedding field: {docs_with_embedding}")
        
        if doc_count == 0 or docs_with_embedding == 0:
            print("Documents or embeddings missing - recreating collection...")
            recreate_chat_collection()
        else:
            # Just ensure vector index is created
            print("Ensuring vector search index is set up...")
            setup_vector_search_index()
    else:
        print("Chat collection exists: NO")
        print("Creating chat collection...")
        recreate_chat_collection()
    
    # Verify everything is working
    collections = db.list_collection_names()
    if "chat" in collections:
        doc_count = db["chat"].count_documents({})
        docs_with_embedding = db["chat"].count_documents({"embedding": {"$exists": True}})
        print("\nFinal Status:")
        print(f"- Chat collection exists: {'YES' if 'chat' in collections else 'NO'}")
        print(f"- Documents in chat collection: {doc_count}")
        print(f"- Documents with embedding field: {docs_with_embedding}")
        
        # List search indices to verify
        indices = list(db["chat"].list_search_indexes())
        vector_index_exists = any(idx.get("name") == "vector_index" for idx in indices)
        print(f"- Vector search index created: {'YES' if vector_index_exists else 'NO'}")
        
        return True
    else:
        print("Failed to create chat collection")
        return False

def recreate_chat_collection():
    """Recreate and populate the chat collection"""
    # Find simulation data directory
    simulation_dirs = ["simulation_data", "data", "output", "simulations"]
    run_dir = None
    
    for dir_name in simulation_dirs:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            # Look for subdirectories that might contain simulation output
            subdirs = [os.path.join(dir_name, d) for d in os.listdir(dir_name) 
                      if os.path.isdir(os.path.join(dir_name, d))]
            
            # Check each subdir for simulation output files
            for subdir in subdirs:
                output_files = ["flow_bandwidth.csv", "link_utilization.csv", "node_info.csv"]
                if any(os.path.exists(os.path.join(subdir, f)) for f in output_files):
                    run_dir = subdir
                    break
            
            if run_dir:
                break
    
    if not run_dir:
        print("Error: Could not find simulation output directory")
        print("Please specify the path to your simulation output files")
        return False
    
    print(f"Found simulation data in: {run_dir}")
    
    # Process simulation output to populate the chat collection
    print("Processing simulation output...")
    processed_files = process_simulation_output(run_dir)
    print(f"Processed {len(processed_files)} files: {', '.join(processed_files)}")
    
    # Setup vector search index
    print("Setting up vector search index...")
    result = setup_vector_search_index()
    print(f"Vector search index setup: {'SUCCESS' if result else 'FAILED'}")
    
    return result

if __name__ == "__main__":
    print("Starting chat functionality diagnostics and repair...")
    fix_chat_functionality() 