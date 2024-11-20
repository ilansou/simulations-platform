import streamlit as st
import requests
import pandas as pd

# Define the Simulation data structure
class Simulation:
    def __init__(self, simulation_id, simulation_name, date, state, parameters, path, result):
        self.simulation_id = simulation_id
        self.simulation_name = simulation_name
        self.date = date
        self.state = state
        self.parameters = parameters
        self.path = path
        self.result = result

# Function to fetch simulations
def fetch_simulations():
    try:
        response = requests.post('http://localhost:8000/api/get_simulate_flood_dns', json={"state": st.session_state.user_info})
        simulations = response.json()
        for sim in simulations:
            sim['state'] = sim.get('state', 'Finished')
        return simulations
    except Exception as e:
        st.error(f"Error fetching simulations: {e}")
        return []

# Function to re-run a simulation
def re_run_simulation(simulation_id, path):
    try:
        response = requests.post("http://localhost:8000/api/re_run_simulation", json={"data": path, "simulation_id": simulation_id, "user_id": st.session_state.uid})
        return response.json()
    except Exception as e:
        st.error(f"Error re-running simulation: {e}")
        return {}

# Function to delete a simulation
def delete_simulation(simulation_id):
    try:
        response = requests.post("http://localhost:8000/api/delte_simulation", json={"data": simulation_id, "user_id": st.session_state.uid})
        return response.json()
    except Exception as e:
        st.error(f"Error deleting simulation: {e}")
        return {}

# Function to create a new simulation
def create_simulation(params):
    try:
        response = requests.post('http://localhost:8000/api/simulate_flood_dns', json={"params": params, "user_id": st.session_state.uid})
        return response.json()
    except Exception as e:
        st.error(f"Error creating simulation: {e}")
        return {}

# Function to edit a simulation
def edit_simulation(params, simulation_id):
    try:
        response = requests.post("http://localhost:8000/api/simulation_update", json={"params": params, "simulationID": simulation_id, "user_id": st.session_state.uid})
        return response.json()
    except Exception as e:
        st.error(f"Error updating simulation: {e}")
        return {}

# Streamlit app
def main():
    st.title("Simulations Dashboard")

    # Initialize session state
    if 'simulations' not in st.session_state:
        st.session_state.simulations = []
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None  # Replace with actual user info
    if 'uid' not in st.session_state:
        st.session_state.uid = "user_id"  # Replace with actual user ID

    # Fetch simulations
    st.session_state.simulations = fetch_simulations()

    # Search bar
    search_text = st.text_input("Search simulations...")
    if search_text:
        st.session_state.simulations = [sim for sim in st.session_state.simulations if search_text.lower() in sim['simulation_name'].lower() or search_text.lower() in sim['parameters'].lower()]

    # Display simulations in a table
    if st.session_state.simulations:
        df = pd.DataFrame(st.session_state.simulations)
        st.dataframe(df)

    # New Simulation button
    if st.button("New Simulation"):
        st.session_state.show_modal = True

    # Modal for creating a new simulation
    if st.session_state.get('show_modal', False):
        with st.form(key='new_simulation_form'):
            st.subheader("Creating New Simulation")
            simulation_name = st.text_input("Simulation Name")
            num_jobs = st.number_input("Num Jobs", max_value=8)
            num_cores = st.selectbox("Num Cores", [0, 1, 4, 8])
            ring_size = st.selectbox("Num Rings", [2, 4, 8])
            routing = st.selectbox("Algorithm", ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"])
            seed = st.selectbox("Seed", [0, 42, 200, 404, 1234])
            submitted = st.form_submit_button("Create Simulation")
            if submitted:
                params = {
                    "simulation_name": simulation_name,
                    "num_jobs": num_jobs,
                    "num_cores": num_cores,
                    "ring_size": ring_size,
                    "routing": routing,
                    "seed": seed
                }
                create_simulation(params)
                st.session_state.show_modal = False

    # Modal for editing a simulation
    if st.session_state.get('show_edit_modal', False):
        with st.form(key='edit_simulation_form'):
            st.subheader("Editing Simulation")
            simulation_name = st.text_input("Simulation Name", value=st.session_state.get('edit_simulation_name', ''))
            num_jobs = st.number_input("Num Jobs", max_value=8, value=st.session_state.get('edit_num_jobs', ''))
            num_cores = st.selectbox("Num Cores", [0, 1, 4, 8], index=st.session_state.get('edit_num_cores', 1))
            ring_size = st.selectbox("Num Rings", [2, 4, 8], index=st.session_state.get('edit_ring_size', 1))
            routing = st.selectbox("Algorithm", ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"], index=st.session_state.get('edit_routing', 0))
            seed = st.selectbox("Seed", [0, 42, 200, 404, 1234], index=st.session_state.get('edit_seed', 0))
            submitted = st.form_submit_button("Edit Simulation")
            if submitted:
                params = {
                    "simulation_name": simulation_name,
                    "num_jobs": num_jobs,
                    "num_cores": num_cores,
                    "ring_size": ring_size,
                    "routing": routing,
                    "seed": seed
                }
                edit_simulation(params, st.session_state.edit_simulation_id)
                st.session_state.show_edit_modal = False

    # Actions for each simulation
    for sim in st.session_state.simulations:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Re-Run", key=f"re_run_{sim['simulation_id']}"):
                re_run_simulation(sim['simulation_id'], sim['path'])
        with col2:
            if st.button("Edit", key=f"edit_{sim['simulation_id']}"):
                st.session_state.show_edit_modal = True
                st.session_state.edit_simulation_id = sim['simulation_id']
                st.session_state.edit_simulation_name = sim['simulation_name']
                st.session_state.edit_num_jobs = sim['parameters'].split(',')[0]
                st.session_state.edit_num_cores = sim['parameters'].split(',')[1]
                st.session_state.edit_ring_size = sim['parameters'].split(',')[2]
                st.session_state.edit_routing = sim['parameters'].split(',')[3]
                st.session_state.edit_seed = sim['parameters'].split(',')[4]
        with col3:
            if st.button("Delete", key=f"delete_{sim['simulation_id']}"):
                delete_simulation(sim['simulation_id'])

main()
