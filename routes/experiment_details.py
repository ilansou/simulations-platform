from llm.generate import generate_response
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os
import streamlit.components.v1 as components

from routes.chat_utils import ingest_experiment_data
from routes.chat_tab import render_chat_tab
from floodns.external.simulation.main import local_run_single_job, local_run_multiple_jobs, local_run_multiple_jobs_different_ring_size
from floodns.external.schemas.routing import Routing
from db_client import experiments_collection
from llm.retrieval import setup_vector_search_index
from llm.ingest import process_simulation_output
from conf import FLOODNS_ROOT

from routes.valid_options import (
    valid_num_jobs, valid_num_cores, valid_ring_sizes,
    valid_routing_algorithms, valid_seeds, valid_models
)



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
    
def validate_simulation_params(num_jobs, num_cores, ring_size, routing, seed, model):
    """
    Validates the simulation parameters according to the requirements.
    """
    valid_num_jobs = [1, 2, 3, 4, 5]
    valid_num_cores = [0, 1, 4, 8]
    valid_ring_sizes = [2, 4, 8, "different"]
    valid_routing_algorithms = ["ecmp", "ilp_solver", "simulated_annealing", "edge_coloring", "mcvlc"]
    valid_seeds = [0, 42, 200, 404, 1234]
    valid_models = ["BLOOM", "GPT_3", "LLAMA2_70B"]

    ring_size_param = int(ring_size) if ring_size != "different" else ring_size

    if num_jobs not in valid_num_jobs:
        return False, "Invalid number of jobs. Must be between 1 and 5."

    if num_cores not in valid_num_cores:
        return False, "Invalid number of core failures. Must be 0, 1, 4, or 8."

    if ring_size_param not in valid_ring_sizes:
        return False, "Invalid ring size. Must be 2, 4, 8, or 'different'."

    if num_jobs == 1 and ring_size == "different":
        return False, "Invalid ring size for single job. Must be 2, 4, or 8."

    if routing not in valid_routing_algorithms:
        return False, "Invalid routing algorithm."

    if seed not in valid_seeds:
        return False, "Invalid seed. Must be 0, 42, 200, 404, or 1234."

    if num_jobs == 1 and model not in valid_models:
        return False, "Invalid model. Must be BLOOM, GPT_3, or LLAMA2_70B for a single job."

    if num_jobs in [1, 2, 3] and ring_size_param not in [2, 8, "different"]:
        return False, "Invalid ring size for 1-3 jobs. Must be 2, 8, or 'different'."

    if num_jobs in [4, 5] and ring_size_param not in [2, 4, "different"]:
        return False, "Invalid ring size for 4-5 jobs. Must be 2, 4, or 'different'."

    return True, "Parameters are valid."

# Function to handle saving edited experiments
def save_edited_experiment(simulation_id, simulation_name, params):
    """
    Saves the edited simulation parameters to the database.
    """
    try:
        num_jobs, num_cores, ring_size, routing, seed, model = params.split(",")
        if int(num_jobs) > 1:
            model = None

        is_valid, message = validate_simulation_params(
            int(num_jobs), int(num_cores), ring_size, routing, int(seed), model
        )
        if not is_valid:
            st.error(message)
            return

        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "simulation_name": simulation_name,
                    "params": params,
                    "state": "Edited",
                    "end_time": None
                }
            }
        )
        st.success("Simulation updated successfully!")
        st.session_state.edit_experiment_modal = False
        st.rerun()
    except Exception as e:
        st.error(f"Error updating simulation: {e}")


def delete_experiment(simulation_id):
    try:
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
        st.session_state.experiment = None
        st.success("Experiment deleted successfully!")
        st.session_state.delete_success = True
        st.session_state.delete_simulation_id = simulation_id
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


def check_experiment_status(run_dir):
    """
    Checks the status of the experiment by reading the run_finished.txt file.
    """
    if not run_dir:
        st.error("No run directory specified. Please ensure the simulation was created successfully.")
        return False

    status_file_path = os.path.join(run_dir, "run_finished.txt")
    try:
        if os.path.exists(status_file_path):
            with open(status_file_path, 'r') as f:
                content = f.read().strip().lower()
                if content == "yes":
                    return True
        return False
    except Exception as e:
        st.error(f"Error checking experiment status file {status_file_path}: {e}")
        return False
    
def re_run_experiment(simulation_id):
    """
    Re-runs the simulation based on the parameters provided.
    """
    try:
        # Fetch the experiment details
        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if not experiment:
            st.error("Experiment not found for re-run.")
            return

        # Extract parameters from the experiment
        params = experiment["params"]
        num_jobs, num_cores, ring_size, routing, seed, model = params.split(",")

        # Update the experiment state to "Running"
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "state": "Running",
                    "start_time": datetime.now().isoformat(),
                    "end_time": None,
                    "run_dir": None,
                }
            }
        )
        
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
        
        # Run the simulation
        run_simulation(simulation_id, num_jobs, num_cores, ring_size, routing, seed, model)

    except Exception as e:
        st.error(f"Error re-running simulation: {e}")

def run_simulation(simulation_id, num_jobs, num_cores, ring_size, routing, seed, model):
    """
    Runs the simulation based on the parameters provided.
    """
    try:
        routing_enum = Routing[routing]

        # Determine the appropriate run function and parameters
        run_dir = None
        ring_size_param = int(ring_size) if ring_size != "different" else ring_size

        # Convert ring_size to int if it's not "different"
        if int(num_jobs) == 1:
            proc = local_run_single_job(
                seed=int(seed),
                n_core_failures=int(num_cores),
                ring_size=ring_size_param,
                model=model,
                alg=routing_enum
            )

            # Determine the run directory path for single job
            ring_size_path_part = "different_ring_size" if ring_size == "different" else f"ring_size_{ring_size_param}"
            run_dir = os.path.join(
                FLOODNS_ROOT,
                "runs",
                f"seed_{seed}",
                "concurrent_jobs_1",
                f"{num_cores}_core_failures",
                ring_size_path_part,
                model,
                routing
            )

        elif int(num_jobs) > 1 and ring_size == "different":
            proc = local_run_multiple_jobs_different_ring_size(
                seed=int(seed),
                n_jobs=int(num_jobs),
                n_core_failures=int(num_cores),
                alg=routing_enum
            )

            # Determine the run directory path for multiple jobs with different ring sizes
            run_dir = os.path.join(
                FLOODNS_ROOT,
                "runs",
                f"seed_{seed}",
                f"concurrent_jobs_{num_jobs}",
                f"{num_cores}_core_failures",
                "different_ring_size",
                routing
            )

        else:
            proc = local_run_multiple_jobs(
                seed=int(seed),
                n_jobs=int(num_jobs),
                ring_size=int(ring_size),
                n_core_failures=int(num_cores),
                alg=routing_enum
            )

            # Determine the run directory path for multiple jobs with the same ring size
            run_dir = os.path.join(
                FLOODNS_ROOT,
                "runs",
                f"seed_{seed}",
                f"concurrent_jobs_{num_jobs}",
                f"{num_cores}_core_failures",
                f"ring_size_{ring_size}",
                routing
            )

        # Ensure run_dir is valid
        if not run_dir:
            raise ValueError("Failed to determine run directory.")

        # Create run_dir if it doesn't exist
        os.makedirs(run_dir, exist_ok=True)

        # Get the logs_floodns path specifically for analysis
        logs_floodns_dir = os.path.join(run_dir, "logs_floodns")
        final_run_dir = logs_floodns_dir if os.path.exists(logs_floodns_dir) else run_dir

        # Update the experiment with the run_dir
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "run_dir": final_run_dir,
                }
            }
        )

        st.write(f"Simulation launched! Run directory: {final_run_dir}")
        

    except Exception as e:
        st.error(f"Error starting simulation: {e}")
        # Update the experiment state to error
        experiments_collection.update_one(
            {"_id": simulation_id},
            {"$set": {"state": "Error", "error_message": str(e)}}
        )

def display_page(simulation_id):
    """
    Displays the experiment details page.
    
    Args:
        simulation_id (str): The ID of the experiment to display
    """
    try:
        experiment = fetch_experiment_details(simulation_id)
        if not experiment:
            st.error(f"Could not fetch experiment with ID {simulation_id}")
            return
        
        st.title(f"Experiment: {experiment['simulation_name']}")
        
        # Add FloodNS Framework Overview
        with st.expander("Framework Overview", expanded=False):
            st.markdown("""
            ## FloodNS Framework Concepts
            
            ### Core Components
            
            - **Network(V, E, F):** Network consisting of node set *V* and link set *E* connecting these nodes. Within the network is a set of flows *F* present.
            - **Node:** Point in the network to which links can be connected. It can function as a flow entry, relay or exit.
            - **Link(u, v, c):** A directed edge from node *u* to node *v* with a fixed capacity *c*.
            - **Flow(s, t, path):** A stream from start node *s* to target node *t* over a fixed *path* with a certain bandwidth.
            - **Connection(Q, s, t):** Abstraction for an amount *Q* that is desired to be transported from *s* to *t* over a set of flows.
            - **Event:** Core component which is user-defined.
            - **Aftermath:** Core component which enforces some state invariant (user-defined), for example max-min fair (MMF) allocation.
            - **Simulator:** Event-driven single-run engine that executes events.
            
            ### CSV Log Files
            
            The simulation produces these log files:
            
            - **flow_bandwidth.csv:** Flow bandwidth intervals
            - **flow_info.csv:** Aggregate flow information
            - **link_info.csv:** Aggregate link information
            - **link_num_active_flows.csv:** Link active flows intervals
            - **link_utilization.csv:** Link utilization intervals
            - **node_info.csv:** Aggregate node information
            - **node_num_active_flows.csv:** Node active flows intervals
            - **connection_bandwidth.csv:** Connection bandwidth intervals
            - **connection_info.csv:** Aggregate connection information
            """)
            
        # Create tabs for the experiment details
        tab1, tab2 = st.tabs(["Experiment Details", "Chat with Simulation Data"])

        with tab1:
            st.header(f"Simulation Name: {experiment['simulation_name']}")
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                st.button("Re-run", on_click=lambda: re_run_experiment(simulation_id))
                print("run_dir:", experiment.get("run_dir"))
                print("state:", experiment.get("state"))
                
            with col2:
                st.button("Edit", on_click=lambda: st.session_state.update({"edit_experiment_modal": True}))
            with col3:
                st.button("Delete", on_click=lambda: delete_experiment(simulation_id))
            if experiment.get("state") == "Running":
                    print("run dir:", experiment["run_dir"])
                    if st.button("🔄"): 
                        if check_experiment_status(experiment.get("run_dir")):
                            experiments_collection.update_one(
                                {"_id": ObjectId(simulation_id)},
                                {"$set": {"state": "Finished", "end_time": datetime.now().isoformat()}}
                            )
                            st.success("Experiment completed successfully!")
                            st.rerun()
                        else:
                            st.warning("Experiment is still running.")

            # Handle deletion success
            if st.session_state.get("delete_success", False) and st.session_state.get("delete_simulation_id") == simulation_id:
                st.success("Experiment deleted successfully!")
                st.session_state.delete_success = False
                st.session_state.delete_simulation_id = None
                st.markdown('<a href="/dashboard">Return to Dashboard</a>', unsafe_allow_html=True)
                return

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
                    "link_info.csv",
                    "link_num_active_flows.csv",
                    "link_utilization.csv",
                    "node_info.csv",
                    "node_num_active_flows.csv",
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
                "Model": params_array[5],
            }
            st.write(pd.DataFrame([params_dict]))

            if st.session_state.get("edit_experiment_modal", False):
                placeholder = st.empty()
                with placeholder.container():
                    close_button = st.button("✖")
                    with st.form(key="edit_experiment_form"):
                        simulation_name = st.text_input("Simulation Name", value=experiment["simulation_name"])
                        num_jobs = st.selectbox("Num Jobs", options=valid_num_jobs, index=valid_num_jobs.index(int(params_array[0])))
                        num_cores = st.selectbox("Num Cores", options=valid_num_cores, index=valid_num_cores.index(int(params_array[1])))
                        ring_size_index = valid_ring_sizes.index(params_array[2] if params_array[2] == "different" else int(params_array[2]))
                        ring_size = st.selectbox("Ring Size", options=valid_ring_sizes, index=ring_size_index)
                        routing = st.selectbox("Routing Algorithm", options=valid_routing_algorithms, index=valid_routing_algorithms.index(params_array[3]))
                        seed = st.selectbox("Seed", options=valid_seeds, index=valid_seeds.index(int(params_array[4])))
                        model = st.selectbox("Model", options=valid_models, index=valid_models.index(params_array[5]))
                        params = f"{num_jobs},{num_cores},{ring_size},{routing},{seed},{model}"
                        submit_button = st.form_submit_button(label="Save Changes")

                    if close_button:
                        placeholder.empty()
                        st.session_state.edit_experiment_modal = False

                    if submit_button:
                        try:
                            save_edited_experiment(simulation_id, simulation_name, params)
                            st.session_state.experiment = fetch_experiment_details(simulation_id)
                            placeholder.empty()
                        except Exception as e:
                            st.error(f"Error in experiment details: {e}")
    except Exception as e:
        st.error(f"Error in experiment details: {e}")

    with tab2:
        render_chat_tab(simulation_id, experiment)

def main():
    st.title("Experiment Details")
    simulation_id = st.query_params["simulation_id"] if "simulation_id" in st.query_params else None
    if simulation_id:
        display_page(simulation_id)
    else:
        st.error("Simulation ID is missing from the URL.")

main()
