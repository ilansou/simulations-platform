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
    try:
        experiments = list(experiments_collection.find())
        for experiment in experiments:
            experiment['_id'] = str(experiment['_id'])  # Convert ObjectId to string
        return experiments
    except Exception as e:
        st.error(f"Error fetching experiments: {e}")
        return []


def create_new_simulation(simulation_name, params):
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

    # Display experiments in a table
    if experiments:
        df = pd.DataFrame(experiments)
        df = df[["_id", "simulation_name", "date", "params", "state"]]
        df.rename(columns={"state": "Is Running?"}, inplace=True)
        df["Is Running?"] = df["Is Running?"].apply(lambda x: "✔" if x == "Running" else "✘")

        # Create a clickable link for the simulation name
        df['simulation_name'] = df.apply(
            lambda row: f'<a href="/experiment_details?simulation_id={row["_id"]}">{row["simulation_name"]}</a>', axis=1
        )

        # Create actions column within the DataFrame
        action_options = ['', 'Re-Run', 'Edit', 'Delete']  # Consistent options
        df['Actions'] = ''  # Initialize the Actions column. Important to avoid errors.

        st.markdown(
            df[['simulation_name', 'date', 'params', 'Is Running?', 'Actions']].to_html(escape=False, index=False),
            unsafe_allow_html=True)

        # Action Selection
        for index, row in df.iterrows():
            df.at[index, 'Actions'] = st.selectbox(
                'Select Action',
                action_options,
                key=f"action_{row['_id']}",  # Unique key for each selectbox
                on_change=handle_action_change,
                args=(row['_id'],),
            )


def handle_action_change(action, simulation_id):
    if action == "Re-Run":
        st.experimental_set_query_params(simulation_id=simulation_id)
        st.rerun()
    elif action == "Edit":
        st.experimental_set_query_params(simulation_id=simulation_id)
        st.rerun()
    elif action == "Delete":
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
        st.rerun()


main()