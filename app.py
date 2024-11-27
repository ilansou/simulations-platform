import streamlit as st

from pages.dashboard import main as dashboard_main
from pages.experiment_details import main as experiment_details_main


def main():
    """
    Main function to manage page navigation and configuration.
    Renders different pages based on the query parameters.
    """
    # Set Streamlit page configuration
    st.set_page_config(page_title="Simulation Manager", page_icon=":microscope:", layout="wide")

    # Retrieve the current query parameters
    query_params = st.query_params

    # Get the 'page' parameter from the query parameters, defaulting to 'dashboard' if not specified
    page = query_params.get("page", "dashboard")

    # Handle cases where 'page' may be a list (multiple values in query parameters)
    if isinstance(page, list):
        page = page[0]

    # Navigate to the appropriate page based on the 'page' parameter
    if page == "dashboard":
        # Render the dashboard page
        dashboard_main()
    elif page == "experiment_details":
        # Render the experiment details page
        experiment_details_main()
    else:
        # Display an error message for invalid or unknown pages
        st.error("Page not found.")


# Entry point for the application
if __name__ == "__main__":
    main()
