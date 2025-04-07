from llm.generate import generate_response
import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os

from floodns.external.simulation.main import local_run_single_job
from floodns.external.schemas.routing import Routing
from db_client import experiments_collection
from llm.ingest import process_simulation_output

def fetch_experiment_details(simulation_id):
    try:
        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if experiment:
            experiment['_id'] = str(experiment['_id'])  # Convert ObjectId to string
            return experiment
        else:
            st.error("Experiment not found")
            return None
    except Exception as e:
        st.error(f"Error fetching experiment details: {e}")
        return None


# Function to handle re-running an experiment
def re_run_experiment(simulation_id):
    print(">>> re_run_experiment CALLED!", simulation_id)
    st.write(">>> re_run_experiment CALLED!", simulation_id)
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$set": {"state": "Re-Running"}}
        )

        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if not experiment:
            st.error("Experiment not found for re-run.")
            return

        params = experiment["params"]
        num_jobs, num_cores, ring_size, routing_str, seed = params.split(",")
        model = "BLOOM"
        routing_enum = Routing[routing_str]

        st.write("Let's launch local_run_single_job...")
        proc = local_run_single_job(
            seed=int(seed),
            n_core_failures=int(num_cores),
            ring_size=int(ring_size),
            model=model,
            alg=routing_enum
        )
        st.write("local_run_single_job зcompleted. See logs in console Docker.")
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "state": "Finished",
                    "end_time": datetime.now().isoformat(),
                }
            },
        )
        st.success("Experiment re-run successfully!")
    except Exception as e:
        st.error(f"Error re-running experiment: {e}")
        print(f"Exception in re_run_experiment: {e}")


# Function to handle saving edited experiments
def save_edited_experiment(simulation_id):
    try:
        updated_params = f"{st.session_state.params['num_jobs']},{st.session_state.params['num_cores']},{st.session_state.params['ring_size']},{st.session_state.params['routing']},{st.session_state.params['seed']}"
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "params": updated_params,
                    "simulation_name": st.session_state.params["simulation_name"],
                }
            },
        )
        st.session_state.show_modal = False
        st.success("Experiment updated successfully!")
    except Exception as e:
        st.error(f"Error updating experiment: {e}")


def delete_experiment(simulation_id):
    try:
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
        st.session_state.experiment = None
        st.success("Experiment deleted successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting experiment: {e}")
        
def render_output_files(folder_path: str, filenames):
    """
    Checks the folder for specific files and adds download buttons for each.
    """
    folder_abs = os.path.abspath(folder_path)
    if not os.path.exists(folder_abs) or not os.path.isdir(folder_abs):
        st.write(f"Folder not found or is not a directory: {folder_abs}")
        return

    for fname in filenames:
        fpath = os.path.join(folder_abs, fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label=f"Download {fname}",
                data=file_bytes,
                file_name=fname,
                mime="application/octet-stream"
            )
        else:
            st.write(f"File not found: {fname}")


def ingest_experiment_data(experiment):
    """Process and store experiment output files for LLM retrieval"""
    if experiment.get("state") == "Finished" and experiment.get("run_dir"):
        try:
            with st.spinner("Processing simulation files for chat..."):
                processed_files = process_simulation_output(experiment["run_dir"])
                
                if not processed_files:
                    st.warning("No simulation files were processed. The chat feature may not work properly.")
                    return False
                    
                # Set up vector search index
                from llm.retrieval import setup_vector_search_index
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


def save_chat_message(simulation_id, question, answer):
    """Save chat message to the database to persist between sessions"""
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$push": {"chat_history": {"question": question, "answer": answer, "timestamp": datetime.now().isoformat()}}}
        )
        return True
    except Exception as e:
        st.error(f"Error saving chat message: {e}")
        return False


def load_chat_history(simulation_id):
    """Load chat history from the database"""
    try:
        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if experiment and "chat_history" in experiment:
            return [(msg["question"], msg["answer"]) for msg in experiment["chat_history"]]
        return []
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
        return []


def display_page(simulation_id):
    tab1, tab2 = st.tabs(["Experiment Details", "Chat"])

    with tab1:
        if "experiment" not in st.session_state or not st.session_state.experiment:
            st.session_state.experiment = fetch_experiment_details(simulation_id)

        if st.session_state.experiment:
            experiment = st.session_state.experiment

            st.header(f"Simulation Name: {experiment['simulation_name']}")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.button("Re-run", on_click=lambda: re_run_experiment(simulation_id))
            with col2:
                st.button("Edit", on_click=lambda: st.session_state.update(show_modal=True))
            with col3:
                st.button("Delete", on_click=lambda: delete_experiment(simulation_id))
            st.subheader("Summary")
            st.write(f"Date: {experiment['date']}")
            st.write(f"Start time: {experiment['start_time']}")
            st.write(f"End time: {experiment['end_time']}")
            st.write(f"State: {experiment['state']}")
            
            if experiment.get("state") == "Finished" and experiment.get("run_dir"):
                st.subheader("Output Files")
                filenames = [
                    "flow_bandwidth.csv",
                    "flow_info.csv",
                    "link_utilization.csv",
                    "node_info.csv",
                    "connection_bandwidth.csv",
                    "connection_info.csv"
                ]
                render_output_files(experiment["run_dir"], filenames)
                
                # Ingest data for LLM if not already done
                if "files_ingested" not in st.session_state:
                    with st.spinner("Processing simulation data for chat..."):
                        st.session_state.files_ingested = ingest_experiment_data(experiment)
            else:
                st.write("This experiment does not have a 'run_dir' field or is not finished.")

            st.subheader("Parameters")
            params_array = experiment["params"].split(",")
            params_dict = {
                "Num Jobs": params_array[0],
                "Num Cores": params_array[1],
                "Ring Size": params_array[2],
                "Routing Algorithm": params_array[3],
                "Seed": params_array[4],
            }
            st.write(pd.DataFrame([params_dict]))

            if st.session_state.get("show_modal", False):
                with st.form(key="edit_experiment_form"):
                    st.text_input("Simulation Name", key="simulation_name", value=experiment["simulation_name"])
                    st.text_input("Num Jobs", key="num_jobs", value=params_array[0])
                    possible_cores = [1, 4, 8]
                    core_index = possible_cores.index(int(params_array[1])) if int(params_array[1]) in possible_cores else 0
                    st.selectbox("Num Cores", possible_cores, key="num_cores", index=core_index)
                    possible_ring = [2, 4, 8]
                    ring_index = possible_ring.index(int(params_array[2])) if int(params_array[2]) in possible_ring else 0
                    st.selectbox("Ring Size", possible_ring, key="ring_size", index=ring_index)
                    possible_routings = ["ecmp", "ilp_solver", "simulated_annealing"]
                    routing_index = possible_routings.index(params_array[3]) if params_array[3] in possible_routings else 0
                    st.selectbox("Routing Algorithm", possible_routings, key="routing", index=routing_index)
                    st.text_input("Seed", key="seed", value=params_array[4])
                    st.form_submit_button("Save", on_click=lambda: save_edited_experiment(simulation_id))

    with tab2:
        st.title("Chat with Your Simulation Data")
        
        # Display available files and example questions at the top
        if "files_ingested" in st.session_state and st.session_state.files_ingested:
            if "ingested_files" in st.session_state and st.session_state.ingested_files:
                st.info(f"You can ask questions about these simulation files: {', '.join(st.session_state.ingested_files)}")
                st.write("Example questions you can ask:")
                st.write("- What is the average bandwidth in the flow_bandwidth.csv file?")
                st.write("- How many nodes are in the simulation?")
                st.write("- Summarize the connection information data.")
        
        # Load chat history from database instead of session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = load_chat_history(simulation_id)

        # Display chat history
        for i, (question, answer) in enumerate(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                st.write(answer)

        if "files_ingested" in st.session_state and st.session_state.files_ingested:
            # Get user question
            user_question = st.chat_input("Ask about your simulation data...")
            
            if user_question:
                with st.chat_message("user"):
                    st.write(user_question)

                with st.chat_message("assistant"):
                    try:
                        with st.spinner("Analyzing simulation data..."):
                            answer = generate_response(user_question)
                            st.write(answer)
                            # Save to session state
                            st.session_state.chat_history.append((user_question, answer))
                            # Save to database
                            save_chat_message(simulation_id, user_question, answer)
                    except Exception as e:
                        error_message = f"Error generating response: {str(e)}"
                        st.error(error_message)
                        # Add technical details that can be expanded/collapsed
                        with st.expander("Technical error details"):
                            import traceback
                            st.code(traceback.format_exc(), language="python")
                        # Still add to chat history so user knows there was an error
                        st.session_state.chat_history.append((user_question, error_message))
                        # Save error to database too
                        save_chat_message(simulation_id, user_question, error_message)
        else:
            st.warning("Chat is only available for finished experiments with processed output files. Please ensure your experiment is complete and the data has been processed successfully.")
            
            # Add button to try processing files if they exist but weren't processed
            if st.session_state.experiment and st.session_state.experiment.get("state") == "Finished" and st.session_state.experiment.get("run_dir"):
                if st.button("Process Files for Chat"):
                    with st.spinner("Processing simulation files..."):
                        st.session_state.files_ingested = ingest_experiment_data(st.session_state.experiment)

def main():
    st.title("Experiment Details")
    simulation_id = st.query_params["simulation_id"] if "simulation_id" in st.query_params else None
    if simulation_id:
        display_page(simulation_id)
    else:
        st.error("Simulation ID is missing from the URL.")

main()