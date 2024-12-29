import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["experiment_db"]
experiments_collection = db["experiments"]


def fetch_all_experiments():
    """
    Fetches all experiments from the MongoDB collection.

    This function retrieves all documents from the "experiments" collection in the database,
    converts the ObjectId to a string for compatibility with Streamlit, and returns the list
    of experiments.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an experiment.
                    Returns an empty list if an error occurs.
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

    Depending on the selected action, this function performs:
    - "Re-Run": Sets query parameters and refreshes the app.
    - "Edit": Sets query parameters and refreshes the app.
    - "Delete": Deletes the simulation from the MongoDB collection.

    Args:
        action (str): The action selected by the user. Valid values are "Re-Run", "Edit", and "Delete".
        simulation_id (str): The ID of the simulation on which the action is performed.
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
    Creates a new simulation in the MongoDB collection.

    This function takes user input for a new simulation, constructs a dictionary with simulation details,
    and inserts it into the "experiments" collection. It then refreshes the app.

    Args:
        simulation_name (str): The name of the new simulation.
        params (str): A string containing simulation parameters (e.g., number of jobs, cores, routing algorithm).
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
        experiments_collection.insert_one(new_experiment)
        st.success("New simulation created successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error creating new simulation: {e}")


def main():
    """
    Main function to render the Streamlit simulation dashboard.

    This function serves as the entry point for the Streamlit app and performs the following:
    - Displays a button to create a new simulation.
    - Renders a modal form for entering details of a new simulation.
    - Fetches and displays all existing experiments from the database in a tabular format.
    - Provides options for user actions on each experiment (Re-Run, Edit, Delete).
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
                num_jobs = st.text_input("Num Jobs")
                num_cores = st.selectbox("Num Cores", [1, 4, 8])
                ring_size = st.selectbox("Ring Size", [2, 4, 8])
                routing = st.selectbox("Routing Algorithm", ["ecmp", "ilp_solver", "simulated_annealing"])
                seed = st.text_input("Seed")
                params = f"{num_jobs},{num_cores},{ring_size},{routing},{seed}"
                submit_button = st.form_submit_button(label="Create")

        # Clear the placeholder container if the close button is clicked
        if close_button:
            placeholder.empty()
            st.session_state.new_simulation_modal = False

        # Clear the placeholder container after the form is submitted
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
