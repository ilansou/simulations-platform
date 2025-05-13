import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.title("Simulation Configurations Overview")

CONFIG_FILE = Path(__file__).resolve().parent.parent / "configurations.json"

@st.cache_data
def load_configs():
    if not CONFIG_FILE.exists():
        st.error(f"Configuration file not found: {CONFIG_FILE}")
        return pd.DataFrame() # Return empty dataframe if file not found
    try:
        with open(CONFIG_FILE, 'r') as f:
            configs = json.load(f)
        return pd.DataFrame(configs)
    except json.JSONDecodeError:
        st.error(f"Error decoding JSON from {CONFIG_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred while loading configurations: {e}")
        return pd.DataFrame()

df_configs = load_configs()

if not df_configs.empty:
    st.write("Displaying all loaded simulation configurations:")
    st.dataframe(df_configs, use_container_width=True)
else:
    st.warning("No configurations loaded or file is empty/corrupted.") 