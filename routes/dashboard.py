import streamlit as st
import pandas as pd
import requests
import jwt


def get_user_id(token):
    """
    This function decodes a JWT (JSON Web Token) and extracts the 'user_id' from it.
    The decoding skips signature verification for simplicity.
    If the 'user_id' key is not present in the decoded token, it returns an empty string.

    Args:
        token (str): The JWT string to be decoded.

    Returns:
        str: The 'user_id' extracted from the token, or an empty string if not found.
    """
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    return decoded_token.get('user_id', '')


def fetch_simulations(user_id):
    """
    This function sends a POST request to fetch simulation routes for a given user.
    It communicates with an API endpoint 'http://localhost:8000/api/get_simulation_routes'
    by sending the 'user_id' in the request payload.

    In case of any request exception, it logs an error message and returns an empty list.

    Args:
        user_id (str): The ID of the user for whom the simulation routes are fetched.

    Returns:
        list: The simulation routes data as a list (parsed from the JSON response),
              or an empty list if an error occurs during the request.
    """
    try:
        response = requests.post("http://localhost:8000/api/get_simulation_routes", json={'user_id': user_id})
        response.raise_for_status()
        simulation = response.json()
        return simulation
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching simulations: {e}")
        return []


def create_simulation(params, user_id):
    """
    This function sends a POST request to create a new simulation using the provided parameters
    and the user ID. It communicates with the API endpoint 'http://localhost:8000/api/simulate_flood_dns'.

    Args:
        params (dict): The parameters needed to create the simulation.
        user_id (str): The ID of the user creating the simulation.

    Returns:
        list: The data from the API response if successful, or an empty list if an error occurs.
    """
    try:
        response = requests.post("http://localhost:8000/api/simulate_flood_dns",json={"parms": params, "user_id": user_id})
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating simulations: {e}")
        return []


def update_simulation(params, simulation_id, user_id):
    """
    This function sends a POST request to update an existing simulation with new parameters.
    It communicates with the API endpoint 'http://localhost:8000/api/simulation_update'.

    Args:
        params (dict): The updated parameters for the simulation.
        simulation_id (str): The ID of the simulation to update.
        user_id (str): The ID of the user performing the update.

    Returns:
        list: The updated data from the API response if successful, or an empty list if an error occurs.
    """
    try:
        response = requests.post("http://localhost:8000/api/simulation_update", json={"parms": params, "simulation_id": simulation_id, "user_id": user_id})
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating simulation: {e}")
        return []


def rerun_simulation(path, simulation_id, user_id):
    """
    This function sends a POST request to re-run a simulation with the specified data and simulation ID.
    It communicates with the API endpoint 'http://localhost:8000/api/re_run_simulation'.

    Args:
        path (str): The path to the simulation data.
        simulation_id (str): The ID of the simulation to re-run.
        user_id (str): The ID of the user requesting the re-run.

    Returns:
        bool: True if the re-run request is successful, or False if an error occurs.
    """
    try:
        response = requests.post("http://localhost:8000/api/re_run_simulation", json={"data": path, "simulation_id": simulation_id, "user_id": user_id})
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error re-running simulation: {e}")
        return False


def delete_solution(simulation_id, user_id):
    """
    This function sends a POST request to delete a simulation with the given simulation ID.
    It communicates with the API endpoint 'http://localhost:8000/api/delte_simulation'.

    Args:
        simulation_id (str): The ID of the simulation to be deleted.
        user_id (str): The ID of the user requesting the deletion.

    Returns:
        bool: True if the deletion request is successful, or False if an error occurs.
    """
    try:
        response = requests.post("http://localhost:8000/api/delte_simulation", json={"data": simulation_id, "user_id": user_id})
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting simulation {e}")
        return False


def main():
    """
    This function is the entry point for the Streamlit-based "Simulations Dashboard" application.
    It provides a user interface for managing simulations, including viewing, creating, updating,
    re-running, and deleting simulations.

    Functionality:
    - Displays a login page if the user is not authenticated using a JWT token.
    - Decodes the JWT token to extract the user ID and fetches associated simulations.
    - Allows the user to perform the following actions:
        1. View and search simulations.
        2. View details of a selected simulation.
        3. Re-run, edit, or delete an existing simulation.
        4. Create a new simulation with custom parameters.
    - Provides a logout option to clear the session.

    Features:
    - Uses Streamlit widgets for a clean and interactive UI.
    - Displays data in a DataFrame for easy searching and visualization.
    - Supports dynamic updates and actions on simulations via API endpoints.

    Steps:
    1. Checks if a JWT token is available in the session state; if not, prompts the user to log in.
    2. Fetches and displays simulations for the logged-in user.
    3. Offers a sidebar menu for navigation between actions (view, create, etc.).
    4. Executes selected actions based on user inputs.

    Args:
        None

    Returns:
        None
    """
    st.title("Simulation Dashboard")

    # Check if 'token' is in session_state
    if 'token' not in st.session_state:
        st.session_state['token'] = ''

    # Check if user is logged in
    if st.session_state['token'] == '':
        st.info("Please enter your JWT token to continue.")
        token_input = st.text_input("JWT Token", type="password")
        if st.button("Login"):
            st.session_state['token'] = token_input
            st.rerun()
        return

    # Decode the token to get user_id
    user_id = get_user_id(st.session_state['token'])

    # Fetch simulation
    simulations = fetch_simulations(user_id)

    # Convert simulations to DataFrame for easier manipulation
    df_simulations = pd.DataFrame(simulations)

    # Sidebar for actions
    st.sidebar.header("Actions")
    action = st.sidebar.selectbox("Select Action", ["View Simulation", "Create Simulation"])

    if action == "View Simulation":
        # Search simulations
        search_text = st.text_input("Hold on! We are searching simulations...")
        if search_text:
            df_simulations = df_simulations[
                df_simulations['simulation_name'].str.contains(search_text, case=False) |
                df_simulations['parameters'].str.contains(search_text, case=False)
            ]

        # Display simulations
        st.dataframe(df_simulations)

        # Select a simulation
        selected_simulation = st.selectbox("Select a simulation to manage", df_simulations['simulation_id'])

        if selected_simulation:
            sim_data = df_simulations[df_simulations['simulation_id'] == selected_simulation].iloc[0]

            st.write("### Simulation Details")
            st.write(f"**Simulation Name:** {sim_data['simulation_name']}")
            st.write(f"**Date:** {sim_data['date']}")
            st.write(f"**Parameters:** {sim_data['parameters']}")
            st.write(f"**State:** {sim_data['state']}")

            # Actions on the selected simulation
            action_type = st.selectbox("Select Action", ["Re-Run simulation", "Edit simulation", "Delete simulation"])

            if action_type == "Re-Run Simulation":
                if st.button("Re-Run"):
                    success = rerun_simulation(sim_data['path'], sim_data['simulation_id'], user_id)
                    if success:
                        st.success("Simulation re-run successfully.")
                        st.rerun()

                elif action_type == "Edit Simulation":
                    st.write("#### Edit Simulation Parameters")

                    params = {
                        'simulation_name': st.text_input("Simulation Name", sim_data['simulation_name']),
                        'num_jobs': st.number_input("Num Jobs", min_value=1, max_value=100,
                                                    value=int(sim_data['parameters'].split(',')[0])),
                        'num_tors': "32",  # Assuming fixed value
                        'num_cores': st.selectbox("Num Cores", [0, 1, 4, 8],
                                                  index=[0, 1, 4, 8].index(int(sim_data['parameters'].split(',')[1]))),
                        'ring_size': st.selectbox("Ring Size", [2, 4, 8],
                                                  index=[2, 4, 8].index(int(sim_data['parameters'].split(',')[2]))),
                        'routing': st.selectbox("Algorithm",
                                                ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"],
                                                index=["ecmp", "edge_coloring", "ilp_solver", "mcvlc",
                                                       "simulated_annealing"].index(
                                                    sim_data['parameters'].split(',')[3])),
                        'path': sim_data['path'],
                        'seed': st.selectbox("Seed", ["0", "42", "200", "404", "1234"],
                                             index=["0", "42", "200", "404", "1234"].index(
                                                 sim_data['parameters'].split(',')[4]))
                    }

                    if st.button("Update Simulation"):
                        update_simulation(params, sim_data['simulation_id'], user_id)
                        st.success("Simulation updated successfully.")
                        st.rerun()

                elif action_type == "Delete Simulation":
                    if st.button("Delete Simulation"):
                        delete_solution(sim_data['simulation_id'], user_id)
                        st.success("Simulation deleted successfully.")
                        st.rerun()

    elif action == "Create Simulation":
        st.header("Create new simulation")

        params = {
            'simulation_name': st.text_input("Simulation Name"),
            'num_jobs': st.number_input("Num Jobs", min_value=1, max_value=100, value=1),
            'num_tors': "32",  # Assuming fixed value
            'num_cores': st.selectbox("Num Cores", [0, 1, 4, 8]),
            'ring_size': st.selectbox("Ring Size", [2, 4, 8]),
            'routing': st.selectbox("Algorithm", ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"]),
            'path': "",
            'seed': st.selectbox("Seed", ["0", "42", "200", "404", "1234"])
        }

        if st.button("Create simulation"):
            if not params['simulation_name']:
                st.error("Simulation Name is required.")
            else:
                create_simulation(params, user_id)
                st.success("Simulation created successfully.")
                st.rerun()


if __name__ == "__main__":
    main()
