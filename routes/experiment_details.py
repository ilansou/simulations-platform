# import streamlit as st
# import requests

# # Function to fetch experiment details
# def fetch_experiment_details(experiment_id):
#     response = requests.get(f'http://localhost:8000/api/get_experiment/{experiment_id}')
#     return response.json()

# # Function to fetch output files
# def fetch_output_files(path):
#     encoded_path = requests.utils.quote(path)
#     response = requests.get(f'http://localhost:8000/api/get_files/{encoded_path}')
#     return response.json()

# # Function to fetch file content
# def fetch_file_content(file_path):
#     encoded_file_path = requests.utils.quote(file_path)
#     response = requests.get(f'http://localhost:8000/api/get_file_content/{encoded_file_path}')
#     return response.json()

# # Function to re-run an experiment
# def re_run_experiment(data, experiment_id):
#     response = requests.post("http://localhost:8000/api/re_run_simulation", json={"data": data, "simulation_id": experiment_id})
#     return response.json()

# # Function to edit an experiment
# def edit_experiment(params, experiment_id):
#     response = requests.post("http://localhost:8000/api/simulation_update", json={"params": params, "simulationID": experiment_id})
#     return response.json()

# # Function to delete an experiment
# def delete_experiment(experiment_id):
#     response = requests.post("http://localhost:8000/api/delte_simulation", json={"data": experiment_id})
#     return response.json()

# # Main app function
# def app():
#     st.title("Experiment Details")

#     # Get experiment ID from query params
#     experiment_id = st.experimental_get_query_params().get("id", [None])[0]

#     if experiment_id:
#         # Fetch experiment details
#         experiment = fetch_experiment_details(experiment_id)
#         st.write(f"## {experiment['simulation_name']}")
#         st.write(f"**Date:** {experiment['date']}")
#         st.write(f"**Start Time:** {experiment['start_time']}")
#         st.write(f"**End Time:** {experiment['end_time']}")

#         # Fetch and display output files
#         output_files = fetch_output_files(experiment['path'])
#         st.write("### Output Files")
#         for file in output_files['files']:
#             if st.button(file, key=file):
#                 file_content = fetch_file_content(file)
#                 st.write(f"### {file}")
#                 st.code(file_content['content'])

#         # Form to edit experiment
#         with st.form("edit_experiment_form"):
#             st.subheader("Edit Experiment")
#             simulation_name = st.text_input("Simulation Name", value=experiment['simulation_name'])
#             num_jobs = st.number_input("Num Jobs", min_value=0, max_value=8, value=int(experiment['params'].split(',')[0]))
#             num_cores = st.selectbox("Num Cores", [0, 1, 4, 8], index=int(experiment['params'].split(',')[1]))
#             ring_size = st.selectbox("Ring Size", [2, 4, 8], index=int(experiment['params'].split(',')[2]))
#             routing = st.selectbox("Algorithm", ["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"], index=["ecmp", "edge_coloring", "ilp_solver", "mcvlc", "simulated_annealing"].index(experiment['params'].split(',')[3]))
#             submitted = st.form_submit_button("Save Changes")

#             if submitted:
#                 params = {
#                     "simulation_name": simulation_name,
#                     "num_jobs": num_jobs,
#                     "num_cores": num_cores,
#                     "ring_size": ring_size,
#                     "routing": routing
#                 }
#                 edited_experiment = edit_experiment(params, experiment_id)
#                 st.success("Experiment edited successfully!")

#         # Button to re-run experiment
#         if st.button("Re-run Experiment"):
#             re_run_experiment(experiment['path'], experiment_id)
#             st.success("Experiment re-run successfully!")

#         # Button to delete experiment
#         if st.button("Delete Experiment"):
#             delete_experiment(experiment_id)
#             st.success("Experiment deleted successfully!")
#     else:
#         st.write("No experiment ID provided.")

# # Run the app function
# if __name__ == "__main__":
#     app()
