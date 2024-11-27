import streamlit as st
import pandas as pd
from pymongo import MongoClient
from bson.objectid import ObjectId


def fetch_simulations():
    """
    Fetch simulations from the MongoDB database.

    Returns:
        list: A list of simulation data.
    """
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Retrieve all simulations
        simulations = list(experiments_collection.find())
        for sim in simulations:
            sim['_id'] = str(sim['_id'])  # Convert ObjectId to string

        return simulations
    except Exception as e:
        st.error(f"Error fetching simulations: {e}")
        return []


def delete_simulation(simulation_id):
    """
    Delete a simulation by its ID.

    Args:
        simulation_id (str): ID of the simulation to delete.
    """
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["experiment_db"]
        experiments_collection = db["experiments"]

        # Delete the simulation by its ID
        experiments_collection.delete_one({"_id": ObjectId(simulation_id)})
    except Exception as e:
        st.error(f"Error deleting simulation: {e}")


def main():
    """
    Main function for the Simulation Dashboard.

    Displays simulations and provides options to view details, re-run,
    or delete simulations. Includes functionality to create a new simulation.
    """
    st.title("Simulation Dashboard")

    # Fetch simulations from the database
    simulations = fetch_simulations()

    # Convert simulation data to a DataFrame for easier manipulation
    df_simulations = pd.DataFrame(simulations)

    # Search simulations by name or parameters
    search_text = st.text_input("Search simulations...")
    if search_text:
        df_simulations = df_simulations[
            df_simulations['simulation_name'].str.contains(search_text, case=False, na=False) |
            df_simulations['params'].str.contains(search_text, case=False, na=False)
        ]

    if df_simulations.empty:
        st.info("No simulations found.")
        return

    # Display the list of simulations
    st.header("Your Simulations")
    for index, row in df_simulations.iterrows():
        st.write(f"### {row['simulation_name']}")
        st.write(f"**Date:** {row['date']}")
        st.write(f"**Parameters:** {row['params']}")
        st.write(f"**State:** {row['state']}")

        # Create columns for action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            # Button to view details of the simulation
            if st.button("View Details", key=f"view_{row['_id']}"):
                # Set simulation_id and navigate to experiment details page
                st.query_params.from_dict({"page": "experiment_details", "simulation_id": row['_id']})
                st.rerun()
        with col2:
            # Button to delete the simulation
            if st.button("Delete Simulation", key=f"delete_{row['_id']}"):
                delete_simulation(row['_id'])
                st.success("Simulation deleted successfully.")
                st.rerun()
        with col3:
            # Button to re-run the simulation
            if st.button("Re-Run", key=f"rerun_{row['_id']}"):
                st.query_params.from_dict({"page": "experiment_details", "simulation_id": row['_id'], "mode": "rerun"})
                st.rerun()

    # Divider
    st.markdown("---")

    # Button to create a new simulation
    if st.button("Create New Simulation"):
        st.query_params.from_dict({"page": "experiment_details", "mode": "create"})
        st.rerun()


# Run the main function
main()
