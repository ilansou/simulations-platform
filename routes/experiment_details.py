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
        
def render_output_files(run_dir, filenames):
    """
    Renders links to download output files from the simulation.
    """
    # If run_dir is a relative path, convert it to absolute using FLOODNS_ROOT
    if not os.path.isabs(run_dir):
        run_dir = os.path.join(FLOODNS_ROOT, run_dir)
        
    # Check if any files exist
    files_exist = False
    for filename in filenames:
        file_path = os.path.join(run_dir, filename)
        if os.path.exists(file_path):
            files_exist = True
            break
    
    if not files_exist:
        st.write("No output files found for this experiment.")
        return
    
    # Create a container to display files in a grid layout
    file_container = st.container()
    
    # Create two columns within the container
    col1, col2 = file_container.columns(2)
    
    # Track which column to use for each file
    use_col1 = True
    
    # Display each file as a download button
    for filename in filenames:
        file_path = os.path.join(run_dir, filename)
        if os.path.exists(file_path):
            try:
                # Read the file and create a download button
                with open(file_path, "rb") as file:
                    file_data = file.read()
                    col = col1 if use_col1 else col2
                    col.download_button(
                        label=filename,
                        data=file_data,
                        file_name=filename,
                        mime="text/csv"
                    )
                # Toggle column for next file
                use_col1 = not use_col1
            except Exception as e:
                st.error(f"Error reading file {filename}: {e}")
        else:
            # Uncomment to show missing files (often not needed for cleaner UI)
            # st.write(f"File not found: {filename}")
            pass


def check_experiment_status(run_dir):
    """
    Checks the status of the experiment by reading the run_finished.txt file.
    """
    if not run_dir:
        st.error("No run directory specified. Please ensure the simulation was created successfully.")
        return False

    # If run_dir is a relative path, convert it to absolute using FLOODNS_ROOT
    if not os.path.isabs(run_dir):
        run_dir = os.path.join(FLOODNS_ROOT, run_dir)

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

        # Store the relative path instead of the absolute path
        if final_run_dir.startswith(FLOODNS_ROOT):
            relative_run_dir = os.path.relpath(final_run_dir, FLOODNS_ROOT)
        else:
            relative_run_dir = final_run_dir
            
        # Update the experiment with the relative run_dir
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "run_dir": relative_run_dir,
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
<<<<<<< HEAD
                # print("run_dir:", experiment.get("run_dir"))
                # print("state:", experiment.get("state"))
=======
>>>>>>> f3609153d39fd1aee4e569ac172ec2bc0de0ac89
                
            with col2:
                st.button("Edit", on_click=lambda: st.session_state.update({"edit_experiment_modal": True}))
            with col3:
                st.button("Delete", on_click=lambda: delete_experiment(simulation_id))
            if experiment.get("state") == "Running":
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

def fetch_multiple_experiments(simulation_ids):
    """
    Fetches multiple experiments by their IDs.
    
    Args:
        simulation_ids (list): List of simulation IDs
        
    Returns:
        list: List of experiment dictionaries
    """
    experiments = []
    for sim_id in simulation_ids:
        experiment = fetch_experiment_details(sim_id)
        if experiment:
            experiments.append(experiment)
    return experiments

def display_multiple_experiments_page(simulation_ids):
    """
    Displays the page for multiple selected experiments.
    
    Args:
        simulation_ids (list): List of simulation IDs to display
    """
    try:
        experiments = fetch_multiple_experiments(simulation_ids)
        if not experiments:
            st.error("No valid experiments found")
            return
        
        # Page title
        experiment_names = [exp['simulation_name'] for exp in experiments]
        st.title(f"Comparative Analysis: {len(experiments)} Experiments")
        st.info(f"**Selected experiments:** {', '.join(experiment_names)}")
        
        # Add a link back to dashboard
        st.markdown('<a href="/dashboard">← Back to Dashboard</a>', unsafe_allow_html=True)
        
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
            
        # Create tabs for the comparison view
        tab1, tab2 = st.tabs(["Experiments Comparison", "Chat with Multiple Simulations"])

        with tab1:
            st.header("Experiments Overview")
            
            # Display summary table
            st.subheader("Summary Comparison")
            summary_data = []
            for exp in experiments:
                params_array = exp["params"].split(",")
                summary_data.append({
                    "Name": exp['simulation_name'],
                    "Date": exp['date'],
                    "State": exp['state'],
                    "Start Time": exp['start_time'],
                    "End Time": exp['end_time'],
                    "Num Jobs": params_array[0],
                    "Num Cores": params_array[1],
                    "Ring Size": params_array[2],
                    "Routing": params_array[3],
                    "Seed": params_array[4],
                    "Model": params_array[5]
                })
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
            # Display output files for each experiment
            st.subheader("Output Files by Experiment")
            
            # Filter finished experiments that have output files
            finished_experiments = [exp for exp in experiments if exp.get("state") == "Finished" and exp.get("run_dir")]
            
            if finished_experiments:
                # Standard file list for all experiments
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
                
                # Create columns for each finished experiment (max 3 per row)
                num_experiments = len(finished_experiments)
                columns_per_row = min(3, num_experiments)
                
                for i in range(0, num_experiments, columns_per_row):
                    batch = finished_experiments[i:i+columns_per_row]
                    cols = st.columns(len(batch))
                    
                    for j, exp in enumerate(batch):
                        with cols[j]:
                            st.write(f"**{exp['simulation_name']}**")
                            render_output_files_compact(exp["run_dir"], filenames, exp['simulation_name'])
                        
                # Ingest data for all experiments for LLM if not already done
                if "multiple_files_ingested" not in st.session_state:
                    with st.spinner("Processing simulation data for comparative chat..."):
                        st.session_state.multiple_files_ingested = ingest_multiple_experiments_data(finished_experiments)
            else:
                st.write("No finished experiments with output files available.")

        with tab2:
            render_multiple_chat_tab(simulation_ids, experiments)
            
    except Exception as e:
        st.error(f"Error displaying multiple experiments: {e}")

def render_output_files_compact(run_dir, filenames, experiment_name=None):
    """
    Renders a compact list of download links for output files.
    """
    # If run_dir is a relative path, convert it to absolute using FLOODNS_ROOT
    if not os.path.isabs(run_dir):
        run_dir = os.path.join(FLOODNS_ROOT, run_dir)
        
    # Check if any files exist
    files_exist = False
    for filename in filenames:
        file_path = os.path.join(run_dir, filename)
        if os.path.exists(file_path):
            files_exist = True
            break
    
    if not files_exist:
        st.write("No output files found.")
        return
    
    # Display each file as a compact download button
    for filename in filenames:
        file_path = os.path.join(run_dir, filename)
        if os.path.exists(file_path):
            try:
                # Read the file and create a download button
                with open(file_path, "rb") as file:
                    file_data = file.read()
                    # Create unique key using experiment name and filename
                    unique_key = f"download_{experiment_name}_{filename}" if experiment_name else f"download_{filename}_{hash(run_dir)}"
                    st.download_button(
                        label=filename,
                        data=file_data,
                        file_name=f"{experiment_name}_{filename}" if experiment_name else filename,
                        mime="text/csv",
                        use_container_width=True,
                        key=unique_key
                    )
            except Exception as e:
                st.error(f"Error reading file {filename}: {e}")

def ingest_multiple_experiments_data(experiments):
    """
    Ingests data from multiple experiments for comparative analysis.
    """
    try:
        from llm.ingest import process_and_store_data, model
        from db_client import chat_collection, db_client
        import glob
        
        # Ensure MongoDB connection is available
        if db_client is None or chat_collection is None:
            return False
        
        # Drop and recreate the collection to avoid dimension conflicts
        db = db_client["experiment_db"]
        if "chat" in db.list_collection_names():
    
            db.drop_collection("chat")
        
        db.create_collection("chat")
        
        processed_files = []
        
        for experiment in experiments:
            run_dir = experiment.get("run_dir")
            if not run_dir:
                continue
                
            # If run_dir is a relative path, convert it to absolute using FLOODNS_ROOT
            if not os.path.isabs(run_dir):
                run_dir = os.path.join(FLOODNS_ROOT, run_dir)
            
            # Process all CSV files in the run directory
            csv_files = glob.glob(os.path.join(run_dir, "*.csv"))
            experiment_name = experiment.get("simulation_name", "Unknown")
            
            for file_path in csv_files:
                filename = os.path.basename(file_path)
                try:
                    # Read file content and create enhanced document
                    with open(file_path, 'r') as file:
                        content = file.read()
                        
                    # Add experiment context to the content
                    enhanced_content = f"""
                    Experiment: {experiment_name}
                    Simulation ID: {experiment['_id']}
                    Parameters: {experiment.get('params', 'N/A')}
                    File: {filename}
                    Content:
                    {content}
                    """
                    
                    embedding = model.encode(enhanced_content).tolist()
                    
                    document = {
                        "text": enhanced_content,
                        "embedding": embedding,
                        "filename": filename,
                        "file_path": file_path,
                        "experiment_name": experiment_name,
                        "experiment_id": experiment['_id'],
                        "experiment_params": experiment.get('params', 'N/A')
                    }
                    
                    chat_collection.insert_one(document)
                    processed_files.append(f"{experiment_name}/{filename}")
    
                except Exception as e:
                    pass
        
        # Set up vector search index after processing all files
        if processed_files:
            if setup_vector_search_index():
                st.success("Vector search capabilities ready!")
            else:
                st.warning("Vector search setup failed. Chat may not work optimally.")
            
            st.success(f"Successfully processed {len(processed_files)} simulation files for comparative chat.")
    
            
            # Store processed files in session state for the chat interface
            st.session_state.multi_ingested_files = processed_files
        
        return len(processed_files) > 0
        
            except Exception as e:
        st.error(f"Error processing simulation files: {str(e)}")
        return False

def load_multiple_chat_history(simulation_ids):
    """Load chat history for multiple simulations from database."""
    try:
        from db_client import db_client
        
        if db_client is None:
            st.warning("Database connection not available, using session state only")
            return []
        
        # Create a unique key for the combination of simulation IDs
        combined_key = "_".join(sorted(simulation_ids))
        
        # Get the multi_chat collection
        multi_chat_collection = db_client["experiment_db"]["multi_chat"]
        
        # Find the chat history document for this combination
        chat_document = multi_chat_collection.find_one({"simulation_ids_key": combined_key})
        
        if chat_document and "chat_history" in chat_document:
            return [(msg["question"], msg["answer"]) for msg in chat_document["chat_history"]]
        
        return []
    except Exception as e:
        st.error(f"Error loading multi-chat history: {e}")
        return []

def save_multiple_chat_message(simulation_ids, question, answer):
    """Save chat message for multiple simulations to database."""
    try:
        from db_client import db_client
        from datetime import datetime
        
        if db_client is None:
            st.warning("Database connection not available, message not saved")
            return False
        
        # Create a unique key for the combination of simulation IDs
        combined_key = "_".join(sorted(simulation_ids))
        
        # Get the multi_chat collection
        multi_chat_collection = db_client["experiment_db"]["multi_chat"]
        
        # Create the message document
        message_doc = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update or create the chat document
        multi_chat_collection.update_one(
            {"simulation_ids_key": combined_key},
            {
                "$push": {"chat_history": message_doc},
                "$setOnInsert": {
                    "simulation_ids": simulation_ids,
                    "simulation_ids_key": combined_key,
                    "created_at": datetime.now().isoformat()
                },
                "$set": {"updated_at": datetime.now().isoformat()}
            },
            upsert=True
        )
        
        return True
    except Exception as e:
        st.error(f"Error saving multi-chat message: {e}")
        return False

def clear_multiple_chat_history(simulation_ids):
    """Clear chat history for multiple simulations from database."""
    try:
        from db_client import db_client
        
        if db_client is None:
            st.warning("Database connection not available")
            return False
        
        # Create a unique key for the combination of simulation IDs
        combined_key = "_".join(sorted(simulation_ids))
        
        # Get the multi_chat collection
        multi_chat_collection = db_client["experiment_db"]["multi_chat"]
        
        # Delete the entire chat document for this combination
        result = multi_chat_collection.delete_one({"simulation_ids_key": combined_key})
        
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Error clearing multi-chat history: {e}")
        return False

def parse_thinking_tags(text):
    """
    Parse a response containing <think> or <thinking> tags and return content and thinking parts.
    """
    import re
    # Check for <think> tags first (newer format)
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, text, re.DOTALL)
    
    if think_match:
        thinking = think_match.group(1).strip()
        # Remove the think tags and content from the main text
        content = re.sub(think_pattern, '', text, flags=re.DOTALL).strip()
        return content, thinking
    
    # Check for <thinking> tags (older format)
    thinking_pattern = r'<thinking>(.*?)</thinking>'
    thinking_match = re.search(thinking_pattern, text, re.DOTALL)
    
    if thinking_match:
        thinking = thinking_match.group(1).strip()
        # Remove the thinking tags and content from the main text
        content = re.sub(thinking_pattern, '', text, flags=re.DOTALL).strip()
        return content, thinking
    
    return text, None

def parse_sources_tags(text):
    """
    Parse a response containing <sources> tags and return content and sources parts.
    """
    import re
    # Check for <sources> tags
    sources_pattern = r'<sources>(.*?)</sources>'
    sources_match = re.search(sources_pattern, text, re.DOTALL)
    
    if sources_match:
        sources = sources_match.group(1).strip()
        # Remove the sources tags and content from the main text
        content = re.sub(sources_pattern, '', text, flags=re.DOTALL).strip()
        return content, sources
    
    return text, None

def render_multiple_chat_tab(simulation_ids, experiments):
    """
    Renders the chat tab for multiple experiments.
    """
    st.header("Chat with Multiple Simulations")
    st.write("Ask questions about the selected simulations for comparative analysis.")

    # Load chat history for these simulations from database
    chat_history = load_multiple_chat_history(simulation_ids)
    
    # Store in session state for UI consistency
    st.session_state.multi_chat_history = chat_history

    # Information about available files and sample questions
    if "multiple_files_ingested" in st.session_state and st.session_state.multiple_files_ingested:
        # Count total files ingested
        finished_experiments = [exp for exp in experiments if exp.get("state") == "Finished" and exp.get("run_dir")]
        processed_files_info = st.session_state.get('multi_ingested_files', [])
        
        st.info(f"You can ask comparative questions about data from {len(finished_experiments)} experiments with {len(processed_files_info)} processed data files.")
        
        # Add clear history button if there's chat history
        if len(chat_history) > 0:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🗑️ Clear Chat History", help="Clear all chat messages for this simulation combination"):
                    if clear_multiple_chat_history(simulation_ids):
                        st.success("Chat history cleared successfully!")
                        st.session_state.multi_chat_history = []
                        st.rerun()
                    else:
                        st.error("Failed to clear chat history")
        
        with st.expander("Example comparative questions you can ask"):
            st.write("- Which algorithm performed best among these simulations?")
            st.write("- Compare the average bandwidth between these experiments")
            st.write("- What are the differences in link utilization across these simulations?")
            st.write("- Which experiment had the highest node throughput?")
            st.write("- Compare the connection information between the different routing algorithms")
            st.write("- Analyze the flow patterns across all selected experiments")

    # Show chat history
    for idx, (question, answer) in enumerate(st.session_state.multi_chat_history):
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            # Parse the answer to separate thinking and sources parts
            content_with_sources, thinking = parse_thinking_tags(answer)
            content, sources = parse_sources_tags(content_with_sources)
            
            # Display the main content
            st.markdown(content)
            
            # Create button columns
            button_cols = []
            if thinking:
                button_cols.append("thinking")
            if sources:
                button_cols.append("sources")
            
            if button_cols:
                # If only one button, center it; if two buttons, use columns
                if len(button_cols) == 1:
                    if thinking:
                        if st.button("🧠 Show Reasoning", key=f"show_multi_thinking_{idx}", help="View the model's reasoning process"):
                            st.session_state[f"multi_thinking_content_{idx}"] = thinking
                    elif sources:
                        if st.button("📋 Show Sources", key=f"show_multi_sources_{idx}", help="View retrieved documents and context"):
                            st.session_state[f"multi_sources_content_{idx}"] = sources
                else:
                    # Two buttons - use columns
                    cols = st.columns(len(button_cols))
                    col_idx = 0
                    
                    # Display thinking button if exists
                    if thinking:
                        with cols[col_idx]:
                            thinking_key = f"show_multi_thinking_{idx}"
                            if st.button("🧠 Show Reasoning", key=thinking_key, help="View the model's reasoning process"):
                                st.session_state[f"multi_thinking_content_{idx}"] = thinking
                        col_idx += 1
                    
                    # Display sources button if exists
                    if sources:
                        with cols[col_idx]:
                            sources_key = f"show_multi_sources_{idx}"
                            if st.button("📋 Show Sources", key=sources_key, help="View retrieved documents and context"):
                                st.session_state[f"multi_sources_content_{idx}"] = sources
            
            # Show thinking content if button was clicked
            if st.session_state.get(f"multi_thinking_content_{idx}"):
                with st.container():
                    st.markdown("**Model's Reasoning Process:**")
                    thinking_html = thinking.replace("\n", "<br>")
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; color: #333; border-left: 4px solid #007acc;">
                        {thinking_html}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    # Add close button
                    if st.button("❌ Hide Reasoning", key=f"hide_multi_thinking_{idx}"):
                        st.session_state[f"multi_thinking_content_{idx}"] = None
                        st.rerun()
            
            # Show sources content if button was clicked
            if st.session_state.get(f"multi_sources_content_{idx}"):
                with st.container():
                    st.markdown("**Retrieved Documents & Context:**")
                    sources_html = sources.replace("\n", "<br>")
                    st.markdown(
                        f"""
                        <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; color: #333; border-left: 4px solid #28a745;">
                        {sources_html}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    # Add close button
                    if st.button("❌ Hide Sources", key=f"hide_multi_sources_{idx}"):
                        st.session_state[f"multi_sources_content_{idx}"] = None
                        st.rerun()

    # Input only if you can chat
    if "multiple_files_ingested" in st.session_state and st.session_state.multiple_files_ingested:
        user_question = st.chat_input("Ask a comparative question about these simulations...")

        if user_question:
            # Generate a response without immediate display
            with st.spinner("Analyzing data from multiple simulations..."):
                try:
                    # For multiple experiments, we need to provide context about all experiments
                    # We'll use the first experiment's run_dir but the system should search across all data
                    answer = generate_response(user_question, run_dir=experiments[0].get("run_dir"))
                except Exception as e:
                    answer = f"Error generating response: {str(e)}"
            
            # Save the conversation to database and rerun to display it
            success = save_multiple_chat_message(simulation_ids, user_question, answer)
            st.rerun()
    else:
        st.warning("Comparative chat is only available when multiple finished experiments have been processed. Please ensure your experiments are complete and the data has been processed successfully.")
        
        finished_experiments = [exp for exp in experiments if exp.get("state") == "Finished" and exp.get("run_dir")]
        if finished_experiments and len(finished_experiments) >= 2:
            if st.button("Process Files for Comparative Chat"):
                with st.spinner("Processing simulation files from all experiments..."):
                    st.session_state.multiple_files_ingested = ingest_multiple_experiments_data(finished_experiments)

    # Autoscroll
    st.markdown(
        """
        <script>
        window.scrollTo(0, document.body.scrollHeight);
        </script>
        """, unsafe_allow_html=True
    )

def main():
    st.title("Experiment Details")
    
    # Check for multiple simulation IDs first
    simulation_ids_param = st.query_params.get("simulation_ids")
    simulation_id = st.query_params.get("simulation_id")
    
    if simulation_ids_param:
        # Handle multiple simulations
        simulation_ids = simulation_ids_param.split(",")
        display_multiple_experiments_page(simulation_ids)
    elif simulation_id:
        # Handle single simulation (existing functionality)
        display_page(simulation_id)
    else:
        st.error("Simulation ID(s) missing from the URL.")

main()
