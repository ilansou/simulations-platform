import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os

from floodns.external.simulation.main import local_run_single_job
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

def handle_action_change(action, simulation_id):
    """
    Handles user actions (Re-Run, Edit, Delete, Stop) on simulations.
    """
    if action == "Re-Run":
        st.query_params.simulation_id = simulation_id
        st.rerun()
    elif action == "Edit":
        st.query_params.simulation_id = simulation_id
        st.rerun()
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

def update_experiment_status_in_db(simulation_id, new_state="Finished"):
    """Updates the experiment state in the database."""
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$set": {"state": new_state, "end_time": datetime.now().isoformat()}}
        )
        st.success(f"Experiment {simulation_id} marked as {new_state}.")
    except Exception as e:
        st.error(f"Error updating experiment status in DB: {e}")

def create_new_simulation(simulation_name, params):
    """
    Creates a new simulation in the MongoDB collection, and then calls local_run_single_job.
    """
    try:
        new_experiment = {
            "simulation_name": simulation_name,
            "params": params,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "state": "Running",
        }
        result = experiments_collection.insert_one(new_experiment)
        st.success("New simulation created successfully!")

        try:
            num_jobs, num_cores, ring_size, routing_str, seed = params.split(",")
            model = "BLOOM"
            routing_enum = Routing[routing_str]

            # # Build a path to the folder with the simulation results
            # run_dir = os.path.join(
            #     FLOODNS_ROOT, "runs", f"seed_{seed}", "concurrent_jobs_1",
            #     f"{num_cores}_core_failures", f"ring_size_{ring_size}",
            #     model, routing_str, "logs_floodns"
            # )

            # Ensure the directory exists
            # os.makedirs(run_dir, exist_ok=True)

            # Run the simulation
            proc = local_run_single_job(
                seed=int(seed),
                n_core_failures=int(num_cores),
                ring_size=int(ring_size),
                model=model,
                alg=routing_enum
            )

            # Save the path to the results in the database
            experiments_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"run_dir": run_dir}}
            )

            st.write("local_run_single_job launched!")
        except Exception as e:
            st.error(f"Error starting simulation: {e}")

        st.rerun()
    except Exception as e:
        st.error(f"Error creating new simulation: {e}")

def main():
    """
    Main function to render the Streamlit simulation dashboard.
    """
    st.title("Simulation Dashboard")

    if st.button("New Simulation"):
        st.session_state.new_simulation_modal = True

    if st.session_state.get("new_simulation_modal", False):
        placeholder = st.empty()
        with placeholder.container():
            close_button = st.button("✖")
            with st.form(key="new_simulation_form"):
                st.write("Create New Simulation")
                simulation_name = st.text_input("Simulation Name")
                num_jobs = st.text_input("Num Jobs", value="1")
                num_cores = st.selectbox("Num Cores (will be n_core_failures)", [1, 4, 8])
                ring_size = st.selectbox("Ring Size", [2, 4, 8])
                routing = st.selectbox("Routing Algorithm", ["ecmp", "ilp_solver", "simulated_annealing"])
                seed = st.text_input("Seed", value="42")
                params = f"{num_jobs},{num_cores},{ring_size},{routing},{seed}"
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
                    update_experiment_status_in_db(exp_id)
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
                        update_experiment_status_in_db(exp_id)
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
