import streamlit as st
import os
import pandas as pd
from pathlib import Path

from llm.think_step_by_step import analyze_and_explain, think_step_by_step
from floodns.external.analysis.analysis_bandwidth import load_simulation_csv, preprocess_data


def app():
    st.title("Simulation Analysis with Step-by-Step Reasoning")
    
    st.write("""
    This page demonstrates Chain of Thought (CoT) reasoning for analyzing network simulation results.
    The LLM will explain its analysis process step by step before providing the final answer.
    """)
    
    # Section for simulation directory selection
    st.header("Select Simulation Data")
    
    # Get the base directory for simulations
    base_dir = os.path.join(os.getcwd(), "floodns", "external", "simulation", "logs_floodns")
    if not os.path.exists(base_dir):
        st.warning(f"Default simulation directory not found: {base_dir}")
        base_dir = os.getcwd()
    
    # Let user input a custom path
    custom_dir = st.text_input("Simulation results directory path:", value=base_dir)
    
    if not os.path.exists(custom_dir):
        st.error(f"Directory does not exist: {custom_dir}")
        return
    
    # List subdirectories
    subdirs = [d for d in os.listdir(custom_dir) if os.path.isdir(os.path.join(custom_dir, d))]
    
    if not subdirs:
        st.warning(f"No simulation result directories found in {custom_dir}")
        return
    
    # Let user select a simulation run
    selected_run = st.selectbox("Select a simulation run:", subdirs)
    run_dir = os.path.join(custom_dir, selected_run)
    
    # Check if necessary CSV files exist
    flow_csv = os.path.join(run_dir, "flow_info.csv")
    conn_csv = os.path.join(run_dir, "connection_info.csv")
    link_csv = os.path.join(run_dir, "link_info.csv")
    
    missing_files = []
    if not os.path.exists(flow_csv): missing_files.append("flow_info.csv")
    if not os.path.exists(conn_csv): missing_files.append("connection_info.csv")
    if not os.path.exists(link_csv): missing_files.append("link_info.csv")
    
    if missing_files:
        st.error(f"Missing required CSV files in {run_dir}: {', '.join(missing_files)}")
        return
    
    # Section for analysis query
    st.header("Ask a Question")
    
    # Provide example questions
    example_questions = [
        "Calculate the total bandwidth across all flows and explain your method.",
        "What is the average throughput for completed connections?",
        "Compare the performance of different paths in the network.",
        "Identify the links with highest utilization and explain why."
    ]
    
    example = st.selectbox("Example questions:", [""] + example_questions)
    query = st.text_area("Enter your question:", value=example if example else "", height=100)
    
    # Model selection
    use_api = st.checkbox("Use API model (uncheck to use local model if available)", value=True)
    
    # Run analysis button
    if st.button("Analyze with Step-by-Step Reasoning"):
        if not query:
            st.error("Please enter a question to analyze.")
            return
        
        with st.spinner("Analyzing data with step-by-step reasoning..."):
            try:
                # Get reasoning result
                result = analyze_and_explain(query, run_dir, use_api)
                
                # Display reasoning
                st.subheader("Step-by-Step Reasoning Process")
                st.markdown(result["reasoning"])
                
                # Display final result
                st.subheader("Final Answer")
                st.success(result["result"])
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
    
    # Display available data overview
    with st.expander("View Available Data Overview"):
        try:
            df_flow, df_conn, df_link = load_simulation_csv(run_dir)
            df_flow, df_conn, df_link = preprocess_data(df_flow, df_conn, df_link)
            
            st.subheader("Flow Data")
            st.write(f"Total flows: {len(df_flow)}")
            st.dataframe(df_flow.head(5))
            
            st.subheader("Connection Data")
            st.write(f"Total connections: {len(df_conn)}")
            st.dataframe(df_conn.head(5))
            
            st.subheader("Link Data")
            st.write(f"Total links: {len(df_link)}")
            st.dataframe(df_link.head(5))
            
        except Exception as e:
            st.error(f"Error loading data preview: {str(e)}")


if __name__ == "__main__":
    app() 