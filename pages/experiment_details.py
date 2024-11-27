import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId


def fetch_experiment_details(simulation_id):
    """
    Fetch experiment details from the MongoDB database.

    Args:
        simulation_id (str): ID of the simulation.

    Returns:
        dict: Experiment details if found, or None if not found.
    """
    try:
        # Connect to the MongoDB database
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Retrieve the experiment by its ID
        experiment = experiments_collection.find_one({"_id": ObjectId(simulation_id)})
        if experiment:
            experiment['_id'] = str(experiment['_id'])  # Convert ObjectId to a string
            return experiment
        else:
            st.error("Experiment not found.")
            return None
    except Exception as e:
        st.error(f"Error fetching experiment details: {e}")
        return None


def save_new_experiment(params):
    """
    Save a new experiment to the database.

    Args:
        params (dict): Parameters of the new experiment.
    """
    try:
        # Connect to the MongoDB database
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Create a new experiment document
        experiment = {
            "simulation_name": params['simulation_name'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "state": "Running",
            "params": f"{params['num_jobs']},{params['num_cores']},{params['ring_size']},{params['routing']},{params['seed']}"
        }

        # Insert the new experiment into the collection
        result = experiments_collection.insert_one(experiment)
        st.success("Experiment created successfully!")
        # Navigate to the details of the newly created experiment
        st.query_params.from_dict({"page": "experiment_details", "simulation_id": str(result.inserted_id)})
        st.rerun()
    except Exception as e:
        st.error(f"Error saving experiment: {e}")


def save_edited_experiment(simulation_id, params):
    """
    Save edited experiment details to the database.

    Args:
        simulation_id (str): ID of the experiment to update.
        params (dict): Updated parameters for the experiment.
    """
    try:
        # Connect to the MongoDB database
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Format updated parameters
        updated_params = f"{params['num_jobs']},{params['num_cores']},{params['ring_size']},{params['routing']},{params['seed']}"

        # Update the experiment in the collection
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "simulation_name": params["simulation_name"],
                    "params": updated_params,
                    "state": "Updated",
                    "end_time": datetime.now().isoformat(),
                }
            },
        )
        st.success("Experiment updated successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error updating experiment: {e}")


def re_run_experiment(simulation_id):
    """
    Re-run an experiment by updating its state in the database.

    Args:
        simulation_id (str): ID of the experiment to re-run.
    """
    try:
        # Connect to the MongoDB database
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Update the experiment's state to "Re-Running"
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$set": {"state": "Re-Running", "start_time": datetime.now().isoformat(), "end_time": None}}
        )
        # Simulate the re-run process and update the state to "Finished"
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
        st.rerun()
    except Exception as e:
        st.error(f"Error re-running experiment: {e}")


def delete_experiment(simulation_id):
    """
    Delete an experiment from the database.

    Args:
        simulation_id (str): ID of the experiment to delete.
    """
    try:
        # Connect to the MongoDB database
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Delete the experiment by its ID
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
        st.success("Experiment deleted successfully!")
        # Navigate back to the dashboard
        st.query_params.from_dict({"page": "dashboard"})
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting experiment: {e}")


def display_experiment(simulation_id):
    """
    Display detailed information about a specific experiment.

    Args:
        simulation_id (str): ID of the experiment to display.
    """
    experiment = fetch_experiment_details(simulation_id)

    if experiment:
        # Display the main details of the experiment
        st.header(f"Simulation Name: {experiment['simulation_name']}")
        st.subheader("Summary")
        st.write(f"Date: {experiment['date']}")
        st.write(f"Start time: {experiment['start_time']}")
        st.write(f"End time: {experiment['end_time']}")
        st.write(f"State: {experiment['state']}")

        # Display experiment parameters
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

        # Create action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("Re-run"):
                re_run_experiment(simulation_id)
        with col2:
            if st.button("Edit"):
                st.session_state.show_edit_form = True
        with col3:
            if st.button("Delete"):
                delete_experiment(simulation_id)
        with col4:
            if st.button("Back to Dashboard"):
                st.query_params.from_dict({"page": "dashboard"})
                st.rerun()

        # Display edit form if "Edit" button is clicked
        if st.session_state.get("show_edit_form", False):
            st.subheader("Edit Experiment")
            with st.form(key="edit_experiment_form"):
                simulation_name = st.text_input("Simulation Name", value=experiment["simulation_name"])
                num_jobs = st.number_input("Num Jobs", min_value=1, max_value=100, value=int(params_array[0]))
                num_cores = st.selectbox("Num Cores", [0, 1, 4, 8], index=[0, 1, 4, 8].index(int(params_array[1])))
                ring_size = st.selectbox("Ring Size", [2, 4, 8], index=[2, 4, 8].index(int(params_array[2])))
                routing = st.selectbox("Algorithm",
                                       ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"],
                                       index=["ecmp", "edge_coloring", "ilp_solver", "mcvlc",
                                              "simulated_annealing"].index(params_array[3]))
                seed = st.selectbox("Seed", ["0", "42", "200", "404", "1234"],
                                    index=["0", "42", "200", "404", "1234"].index(params_array[4]))
                submit = st.form_submit_button("Save")
                if submit:
                    params = {
                        "simulation_name": simulation_name,
                        "num_jobs": num_jobs,
                        "num_cores": num_cores,
                        "ring_size": ring_size,
                        "routing": routing,
                        "seed": seed,
                    }
                    save_edited_experiment(simulation_id, params)
                    st.session_state.show_edit_form = False


def create_new_experiment():
    """
    Display the form to create a new experiment.
    """
    st.header("Create New Experiment")
    with st.form(key="create_experiment_form"):
        simulation_name = st.text_input("Simulation Name")
        num_jobs = st.number_input("Num Jobs", min_value=1, max_value=100, value=1)
        num_cores = st.selectbox("Num Cores", [0, 1, 4, 8])
        ring_size = st.selectbox("Ring Size", [2, 4, 8])
        routing = st.selectbox("Algorithm", ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"])
        seed = st.selectbox("Seed", ["0", "42", "200", "404", "1234"])
        submit = st.form_submit_button("Create")
        if submit:
            if not simulation_name:
                st.error("Simulation Name is required.")
            else:
                params = {
                    "simulation_name": simulation_name,
                    "num_jobs": num_jobs,
                    "num_cores": num_cores,
                    "ring_size": ring_size,
                    "routing": routing,
                    "seed": seed,
                }
                save_new_experiment(params)

    # Button to return to the dashboard
    if st.button("Back to Dashboard"):
        st.query_params.from_dict({"page": "dashboard"})
        st.rerun()


def main():
    """
    Main function for the Experiment Details page.
    Handles navigation between viewing, editing, and creating experiments.
    """
    st.title("Experiment Details")

    # Get query parameters
    query_params = st.query_params

    # Determine the current mode (view or create)
    mode = query_params.get('mode', 'view')
    if isinstance(mode, list):
        mode = mode[0]

    if mode == 'create':
        create_new_experiment()
    else:
        # Get simulation_id from query parameters
        simulation_id = query_params.get('simulation_id', None)
        if isinstance(simulation_id, list):
            simulation_id = simulation_id[0]

        if simulation_id:
            display_experiment(simulation_id)
        else:
            st.error("No simulation selected.")


# Run the main function
main()
