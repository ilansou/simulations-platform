from datetime import datetime
from db_client import experiments_collection
from bson import ObjectId
import streamlit as st
from llm.ingest import process_simulation_output
from llm.retrieval import setup_vector_search_index


def load_chat_history(simulation_id):
    try:
        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if experiment and "chat_history" in experiment:
            return [(msg["question"], msg["answer"]) for msg in experiment["chat_history"]]
        return []
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
        return []


def save_chat_message(simulation_id, question, answer):
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$push": {
                "chat_history": {"question": question, "answer": answer, "timestamp": datetime.now().isoformat()}}}
        )
        return True
    except Exception as e:
        st.error(f"Error saving chat message: {e}")
        return False


def ingest_experiment_data(experiment):
    """Process and store experiment output files for LLM retrieval"""
    if experiment.get("state") == "Finished" and experiment.get("run_dir"):
        try:
            with st.spinner("Processing simulation files for chat..."):
                run_dir = experiment["run_dir"]
                
                # If run_dir is relative, it will be handled in process_simulation_output
                processed_files = process_simulation_output(run_dir)

                if not processed_files:
                    st.warning("No simulation files were processed. The chat feature may not work properly.")
                    return False

                if setup_vector_search_index():
                    st.success("Vector search capabilities ready!")
                else:
                    st.warning("Vector search setup failed. Chat may not work optimally.")

                st.session_state.ingested_files = processed_files
                st.success(f"Successfully processed {len(processed_files)} simulation files for chat.")
                return len(processed_files) > 0
        except Exception as e:
            st.error(f"Error processing simulation files: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return False
    return False
