import streamlit as st

# Define the pages
dashboard = st.Page("routes/dashboard.py", title="Dashboard", icon=":material/dashboard:")
experiment_details = st.Page("routes/experiment_details.py", title="Experiment Details", icon=":material/description:")

# Set up navigation
pg = st.navigation([dashboard, experiment_details])

# Set page configuration
st.set_page_config(page_title="Simulation Manager", page_icon=":material/science:", layout="wide") 

pg.run()