import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["experiment_db"]
experiments_collection = db["experiments"]

# Verify connection
print(f"Connected to database: {db.name}")
print(f"Using collection: {experiments_collection.name}")


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
    try:
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)}, {"$set": {"state": "Re-Running"}}
        )
        # Simulate the experiment re-run
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


def display_experiment(simulation_id):
    # Fetch experiment details if not already loaded
    if "experiment" not in st.session_state or not st.session_state.experiment:
        st.session_state.experiment = fetch_experiment_details(simulation_id)

    if st.session_state.experiment:
        experiment = st.session_state.experiment

        st.header(f"Simulation Name: {experiment['simulation_name']}")
        st.subheader("Summary")
        st.write(f"Date: {experiment['date']}")
        st.write(f"Start time: {experiment['start_time']}")
        st.write(f"End time: {experiment['end_time']}")
        st.write(f"State: {experiment['state']}")

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

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.button("Re-run", on_click=lambda: re_run_experiment(simulation_id))
        with col2:
            st.button("Edit", on_click=lambda: st.session_state.update(show_modal=True))
        with col3:
            st.button("Delete", on_click=lambda: delete_experiment(simulation_id))

        # Modal for editing
        if st.session_state.get("show_modal", False):
            with st.form(key="edit_experiment_form"):
                st.text_input("Simulation Name", key="simulation_name", value=experiment["simulation_name"])
                st.text_input("Num Jobs", key="num_jobs", value=params_array[0])
                st.selectbox("Num Cores", [1, 4, 8], key="num_cores", index=int(params_array[1]) // 4)
                st.selectbox("Ring Size", [2, 4, 8], key="ring_size", index=int(params_array[2]) // 2)
                st.selectbox("Routing Algorithm", ["ecmp", "ilp_solver", "simulated_annealing"], key="routing",
                             index=["ecmp", "ilp_solver", "simulated_annealing"].index(params_array[3]))
                st.text_input("Seed", key="seed", value=params_array[4])
                st.form_submit_button("Save", on_click=lambda: save_edited_experiment(simulation_id))


def main():
    st.title("Experiment Details")
    if st.button("Home"):
        st.switch_page("routes/dashboard.py")

    # Get simulation_id from URL
    simulation_id = st.query_params["simulation_id"] if "simulation_id" in st.query_params else None

    if simulation_id:
        display_experiment(simulation_id)
    else:
        st.error("Simulation ID is missing from the URL.")


main()