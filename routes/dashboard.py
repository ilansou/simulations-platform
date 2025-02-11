import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

from floodns.external.simulation.main import local_run_single_job
from floodns.external.schemas.routing import Routing

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
    Handles user actions (Re-Run, Edit, Delete) on simulations.
    """
    if action in ["Re-Run", "Edit"]:
        st.query_params.simulation_id = simulation_id
        st.rerun()
    elif action == "Delete":
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
        st.success("Simulation deleted successfully!")
        st.rerun()


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

        # ============================================================
        # Call local_run_single_job after creating a document in the DB
        # =============================================================
        # PARSE PARAMETERS: num_jobs, num_cores, ring_size, routing, seed
        try:
            num_jobs, num_cores, ring_size, routing_str, seed = params.split(",")
            #Here model is hardcoded for now
            model = "BLOOM"

            # Let's convert the string into enum Routing:
            # ecmp -> Routing.ecmp
            # ilp_solver -> Routing.ilp_solver
            # simulated_annealing -> Routing.simulated_annealing
            routing_enum = Routing[routing_str]  # if the string is "ecmp", it will be Routing.ecmp

            # For single_job we need:
            # (seed, n_core_failures, ring_size, model, alg)
            proc = local_run_single_job(
                seed=int(seed),
                n_core_failures=int(num_cores),  # we decide that "num_cores" = "n_core_failures"
                ring_size=int(ring_size),
                model=model,
                alg=routing_enum
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

    # New Simulation button
    if st.button("New Simulation"):
        st.session_state.new_simulation_modal = True

    # Modal for creating a new simulation
    if st.session_state.get("new_simulation_modal", False):
        placeholder = st.empty()
        with placeholder.container():
            # Close button for the modal
            close_button = st.button("✖")
            with st.form(key="new_simulation_form"):
                st.write("Create New Simulation")
                simulation_name = st.text_input("Simulation Name")
                num_jobs = st.text_input("Num Jobs", value="1")
                num_cores = st.selectbox("Num Cores (will be n_core_failures)", [1, 4, 8])
                ring_size = st.selectbox("Ring Size", [2, 4, 8])
                routing = st.selectbox("Routing Algorithm", ["ecmp", "ilp_solver", "simulated_annealing"])
                seed = st.text_input("Seed", value="42")
                # We collect a string for params
                params = f"{num_jobs},{num_cores},{ring_size},{routing},{seed}"
                submit_button = st.form_submit_button(label="Create")

        # Close the form if you pressed "✖"
        if close_button:
            placeholder.empty()
            st.session_state.new_simulation_modal = False

        # When submitting, we call create_new_simulation
        if submit_button:
            create_new_simulation(simulation_name, params)
            placeholder.empty()
            st.session_state.new_simulation_modal = False

    # Fetch all experiments
    experiments = fetch_all_experiments()

    # Display experiments
    if experiments:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 2])
        col1.markdown("**Simulation Name**")
        col2.markdown("**Date**")
        col3.markdown("**Params**")
        col4.markdown("**Is Running?**")
        col5.markdown("**Actions**")

        # Display each entry
        for experiment in experiments:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 2])
            col1.markdown(
                f'<a href="/experiment_details?simulation_id={experiment["_id"]}">{experiment["simulation_name"]}</a>',
                unsafe_allow_html=True)
            col2.text(experiment["date"])
            col3.text(experiment["params"])
            is_running = "✔" if experiment["state"] == "Running" else "✘"
            col4.text(is_running)

            # Adding a selectbox for actions
            action = col5.selectbox(
                'Select Action',
                ['', 'Re-Run', 'Edit', 'Delete'],
                key=f"action_{experiment['_id']}"
            )

            # Processing the selected action
            if action:
                handle_action_change(action, experiment['_id'])


main()
