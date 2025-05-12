import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os

from floodns.external.simulation.main import (
    local_run_single_job,
    local_run_multiple_jobs,
    local_run_multiple_jobs_different_ring_size
)
from floodns.external.schemas.routing import Routing
from conf import FLOODNS_ROOT
from db_client import experiments_collection

def fetch_all_experiments():
    """
    Fetches all experiments from the MongoDB collection.
    """
    try:
        experiments = list(experiments_collection.find())
        for experiment in experiments:
            experiment['_id'] = str(experiment['_id'])  # Convert ObjectId to string
        return experiments
    except Exception as e:
        st.error(f"Error fetching experiments: {e}")
        return []

def fetch_experiment(simulation_id):
    """
    Fetches a single experiment by ID.
    """
    try:
        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if experiment:
            experiment['_id'] = str(experiment['_id'])
            return experiment
        else:
            st.error("Experiment not found")
            return None
    except Exception as e:
        st.error(f"Error fetching experiment: {e}")
        return None
    
def handle_action_change(action, simulation_id):
    """
    Handles user actions (Re-Run, Edit, Delete, Stop) on simulations.
    """
    if action == "Re-Run":
        re_run_simulation(simulation_id)
    elif action == "Edit":
        st.query_params.simulation_id = simulation_id
        st.session_state.show_edit_modal = True
    elif action == "Delete":
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
        st.success("Simulation deleted successfully!")
        st.rerun()
    elif action == "Stop":
        stop_experiment(simulation_id)

def stop_experiment(simulation_id):
    """
    Stops the experiment by updating its state in MongoDB.
    """
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "state": "Finished",
                    "end_time": datetime.now().isoformat(),
                }
            }
        )
        st.success("Experiment stopped successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error stopping experiment: {e}")

def check_experiment_status(run_dir):
    """
    Checks the status of the experiment by reading the run_finished.txt file.
    Returns True if the file contains 'yes', False otherwise.
    """
    if not run_dir:
        print("No run directory specified.")
        return False  # No run directory specified

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

def update_experiment_status(simulation_id, new_state="Finished"):
    """Updates the experiment state in the database."""
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$set": {"state": new_state, "end_time": datetime.now().isoformat()}}
        )
        st.success(f"Experiment {simulation_id} marked as {new_state}.")
    except Exception as e:
        st.error(f"Error updating experiment status in DB: {e}")

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

    if ring_size_param not in valid_ring_sizes and ring_size != "different":
        return False, "Invalid ring size. Must be 2, 4, 8, or 'different'."

    if routing not in valid_routing_algorithms:
        return False, "Invalid routing algorithm."

    if seed not in valid_seeds:
        return False, "Invalid seed. Must be 0, 42, 200, 404, or 1234."
    
    if model not in valid_models and num_jobs == 1:
        return False, "Invalid model. Must be BLOOM, GPT_3, or LLAMA2_70B for a single job."
    
    if num_jobs == 1 and model not in valid_models:
        return False, "Invalid model. Must be BLOOM, GPT_3, or LLAMA2_70B for a single job."

    if num_jobs in [1, 2, 3] and ring_size_param not in [2, 8] and ring_size_param != "different":
        return False, "Invalid ring size for 1-3 jobs. Must be 2, 8, or 'different'."

    if num_jobs in [4, 5] and ring_size_param not in [2, 4] and ring_size_param != "different":
        return False, "Invalid ring size for 4-5 jobs. Must be 2, 4, or 'different'."

    return True, "Parameters are valid."

def save_edited_simulation(simulation_id, simulation_name, params):
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
        st.session_state.show_edit_modal = False
        st.session_state.edit_simulation_id = None
        st.rerun()
    except Exception as e:
        st.error(f"Error updating simulation: {e}")

def create_new_simulation(simulation_name, params):
    """
    Creates a new simulation in the MongoDB collection.
    """
    try:
        num_jobs, num_cores, ring_size, routing, seed, model = params.split(",")
        if int(num_jobs) > 1:
            model = None  # No model needed for multiple jobs
        
        # Validate parameters
        is_valid, message = validate_simulation_params(
            int(num_jobs), int(num_cores), ring_size, routing, int(seed), model
        )

        if not is_valid:
            st.error(message)
            return None

        new_experiment = {
            "simulation_name": simulation_name,
            "params": params,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "state": "Running",
        }
        result = experiments_collection.insert_one(new_experiment)
        simulation_id = result.inserted_id
        st.success("New simulation created successfully!")
        
        run_simulation(
            simulation_id,
            num_jobs,
            num_cores,
            ring_size,
            routing,
            seed,
            model
        )

        return simulation_id

    except Exception as e:
        st.error(f"Error creating new simulation: {e}")
        return None


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
                    "run_dir": final_run_dir
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
    
def re_run_simulation(simulation_id):
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

        # Validate parameters
        is_valid, message = validate_simulation_params(
            int(num_jobs), int(num_cores), ring_size, routing, int(seed), model
        )

        if not is_valid:
            st.error(message)
            return

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
        
        # Run the simulation
        run_simulation(simulation_id, num_jobs, num_cores, ring_size, routing, seed, model)

    except Exception as e:
        st.error(f"Error re-running simulation: {e}")


def main():
    """
    Main function to render the Streamlit simulation dashboard.
    """
    st.title("Simulation Dashboard")

    if st.button("New Simulation"):
        st.session_state.new_simulation_modal = True
        st.session_state.edit_simulation_id = None
        
    if st.session_state.get("show_edit_modal", False) and st.session_state.get("edit_simulation_id"):
        experiment = fetch_experiment(st.session_state.edit_simulation_id)
        if experiment:
            placeholder = st.empty()
            with placeholder.container():
                close_button = st.button("✖")
                with st.form(key="edit_simulation_form"):
                    st.write("Edit Simulation")
                    simulation_name = st.text_input("Simulation Name", value=experiment["simulation_name"])
                    params_array = experiment["params"].split(",")
                    num_jobs = st.selectbox("Num Jobs", [1, 2, 3, 4, 5], index=[1, 2, 3, 4, 5].index(int(params_array[0])))
                    num_cores = st.selectbox("Num Cores (n_core_failures)", [0, 1, 4, 8], index=[0, 1, 4, 8].index(int(params_array[1])))
                    ring_size_options = [2, 4, 8, "different"]
                    ring_size_index = ring_size_options.index(params_array[2] if params_array[2] == "different" else int(params_array[2]))
                    ring_size = st.selectbox("Ring Size", ring_size_options, index=ring_size_index)
                    routing_options = ["ecmp", "ilp_solver", "simulated_annealing", "edge_coloring", "mcvlc"]
                    routing = st.selectbox("Routing Algorithm", routing_options, index=routing_options.index(params_array[3]))
                    seed = st.selectbox("Seed", [0, 42, 200, 404, 1234], index=[0, 42, 200, 404, 1234].index(int(params_array[4])))
                    model_options = ["BLOOM", "GPT_3", "LLAMA2_70B"]
                    model = st.selectbox("Model (for single job)", model_options, index=model_options.index(params_array[5]))
                    params = f"{num_jobs},{num_cores},{ring_size},{routing},{seed},{model}"
                    submit_button = st.form_submit_button(label="Save")

                if close_button:
                    placeholder.empty()
                    st.session_state.show_edit_modal = False
                    st.session_state.edit_simulation_id = None

                if submit_button:
                    save_edited_simulation(st.session_state.edit_simulation_id, simulation_name, params)
                    placeholder.empty()

    if st.session_state.get("new_simulation_modal", False):
        placeholder = st.empty()
        with placeholder.container():
            close_button = st.button("✖")
            with st.form(key="new_simulation_form"):
                st.write("Create New Simulation")
                simulation_name = st.text_input("Simulation Name")
                num_jobs = st.selectbox("Num Jobs", [1, 2, 3, 4, 5])
                num_cores = st.selectbox("Num Cores (n_core_failures)", [0, 1, 4, 8])
                ring_size = st.selectbox("Ring Size", [2, 4, 8, "different"])
                routing = st.selectbox("Routing Algorithm", ["ecmp", "ilp_solver", "simulated_annealing", "edge_coloring", "mcvlc"])
                seed = st.selectbox("Seed", [0, 42, 200, 404, 1234])
                model = st.selectbox("Model", ["BLOOM", "GPT_3", "LLAMA2_70B"])
                params = f"{num_jobs},{num_cores},{ring_size},{routing},{seed},{model}"
                submit_button = st.form_submit_button(label="Create")

            if close_button:
                placeholder.empty()
                st.session_state.new_simulation_modal = False

            if submit_button:
                create_new_simulation(simulation_name, params)
                placeholder.empty()
                st.session_state.new_simulation_modal = False

    experiments = fetch_all_experiments()

    if experiments:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 1, 2])
        col1.markdown("**Simulation Name**")
        col2.markdown("**Date**")
        col3.markdown("**Params**")
        col4.markdown("**Status**")
        col5.markdown("**Check**")  # New column for status check button
        col6.markdown("**Actions**")

        for experiment in experiments:
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 1, 2])

            exp_id = experiment["_id"]
            exp_name = experiment["simulation_name"]
            exp_state = experiment["state"]
            run_dir = experiment.get("run_dir")

            is_finished = False

            # Check if status is running and need to check the file
            if exp_state == "Running" and run_dir:
                is_finished = check_experiment_status(run_dir)
                if is_finished:
                    # Update DB if file indicates experiment is finished
                    update_experiment_status(exp_id)
                    st.rerun()  # Refresh to update UI

            # Only show link if experiment is finished or manually indicate it's finished from file
            if exp_state == "Finished" or is_finished:
                col1.markdown(
                    f'<a href="/experiment_details?simulation_id={exp_id}">{exp_name}</a>',
                    unsafe_allow_html=True)
            else:
                col1.text(exp_name)  # Just show text without link

            col2.text(experiment["date"])
            col3.text(experiment["params"])

            status_icon = "✅" if exp_state == "Finished" else "⏳"
            col4.text(status_icon)

            # Add check button for running experiments
            if exp_state == "Running":
                check_button_key = f"check_status_{exp_id}"
                if col5.button("🔄", key=check_button_key, help="Check if experiment is finished"):
                    if check_experiment_status(run_dir):
                        update_experiment_status(exp_id)
                        st.rerun()
                    else:
                        st.warning(f"Experiment '{exp_name}' is still running.")
            else:
                col5.write("")  # Empty placeholder to maintain column alignment

            action = col6.selectbox(
                'Select Action',
                ['', 'Re-Run', 'Edit', 'Delete', 'Stop'],
                key=f"action_{exp_id}"
            )

            if action:
                handle_action_change(action, exp_id)

main()
