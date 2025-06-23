import os
from dotenv import load_dotenv
from db_client import db_client
from llm.ingest import process_simulation_output
from llm.retrieval import setup_vector_search_index

# Load environment variables
load_dotenv()

def reprocess_simulation_data():
    """Force reprocessing of all simulation data"""
    if db_client is None:
        return False
    
    # Try to find the latest simulation run
    latest_run_dir = None
    
    # Check if FLOODNS_ROOT is defined
    try:
        from conf import FLOODNS_ROOT
        # Check floodns runs directory if it exists
        floodns_path = os.path.join(FLOODNS_ROOT, "runs")
        if os.path.exists(floodns_path):
            
            # Navigate through the directory structure
            for root, dirs, files in os.walk(floodns_path):
                # Check if this directory has logs_floodns
                if "logs_floodns" in dirs:
                    logs_dir = os.path.join(root, "logs_floodns")
                    # Check if it contains our target files
                    target_files = ["flow_bandwidth.csv", "link_utilization.csv", "node_info.csv"]
                    has_files = any(os.path.exists(os.path.join(logs_dir, f)) for f in target_files)
                    
                    if has_files:
                        latest_run_dir = logs_dir
                        break
    except ImportError:
        pass
    
    if not latest_run_dir:
        return False
    
    # Drop existing collection if it exists
    db = db_client["experiment_db"]
    if "chat" in db.list_collection_names():
        db.drop_collection("chat")
    
    # Process the simulation data
    processed_files = process_simulation_output(latest_run_dir)
    
    # Setup vector search index
    result = setup_vector_search_index()
    
    return True

if __name__ == "__main__":
    reprocess_simulation_data() 