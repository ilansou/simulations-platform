import streamlit as st
from llm.generate import generate_response
from routes.chat_utils import load_chat_history, save_chat_message, clear_chat_history, ingest_experiment_data
import re

def parse_thinking_tags(text):
    """
    Parse a response containing <think> or <thinking> tags and return content and thinking parts.
    
    Args:
        text (str): The input text with potential <think> or <thinking> tags
    
    Returns:
        tuple: (content, thinking) where thinking may be None if not present
    """
    # Check for <think> tags first (newer format)
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, text, re.DOTALL)
    
    if think_match:
        thinking = think_match.group(1).strip()
        # Remove the think tags and content from the main text
        content = re.sub(think_pattern, '', text, flags=re.DOTALL).strip()
        return content, thinking
    
    # Check for <thinking> tags (older format)
    thinking_pattern = r'<thinking>(.*?)</thinking>'
    thinking_match = re.search(thinking_pattern, text, re.DOTALL)
    
    if thinking_match:
        thinking = thinking_match.group(1).strip()
        # Remove the thinking tags and content from the main text
        content = re.sub(thinking_pattern, '', text, flags=re.DOTALL).strip()
        return content, thinking
    
    return text, None

def parse_sources_tags(text):
    """
    Parse a response containing <sources> tags and return content and sources parts.
    
    Args:
        text (str): The input text with potential <sources> tags
    
    Returns:
        tuple: (content, sources) where sources may be None if not present
    """
    # Check for <sources> tags
    sources_pattern = r'<sources>(.*?)</sources>'
    sources_match = re.search(sources_pattern, text, re.DOTALL)
    
    if sources_match:
        sources = sources_match.group(1).strip()
        # Remove the sources tags and content from the main text
        content = re.sub(sources_pattern, '', text, flags=re.DOTALL).strip()
        return content, sources
    
    return text, None

def render_chat_tab(simulation_id, experiment):
    st.title("Chat with Your Simulation Data")
    
    # Add a link back to dashboard
    st.markdown('<a href="/dashboard">← Back to Dashboard</a>', unsafe_allow_html=True)

    # Load chat history from the database (once at startup)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history(simulation_id)

    # Information about available files and sample questions
    if "files_ingested" in st.session_state and st.session_state.files_ingested:
        # Add clear history button if there's chat history
        if len(st.session_state.chat_history) > 0:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🗑️ Clear Chat History", help="Clear all chat messages for this simulation"):
                    if clear_chat_history(simulation_id):
                        st.success("Chat history cleared successfully!")
                        st.session_state.chat_history = []
                        st.rerun()
                    else:
                        st.error("Failed to clear chat history")
        
        with st.expander("Example questions you can ask"):
            st.write("- What is the average bandwidth in the flow_bandwidth.csv file?")
            st.write("- How many nodes are in the simulation?")
            st.write("- Summarize the connection information data.")

    # Show chat history (UI only here)
    for idx, (question, answer) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            # Parse the answer to separate thinking and sources parts
            content_with_sources, thinking = parse_thinking_tags(answer)
            content, sources = parse_sources_tags(content_with_sources)
            
            # Display the main content
            st.markdown(content)
            
            # Create button columns
            button_cols = []
            if thinking:
                button_cols.append("thinking")
            if sources:
                button_cols.append("sources")
            
            if button_cols:
                # If only one button, center it; if two buttons, use columns
                if len(button_cols) == 1:
                    if thinking:
                        if st.button("🧠 Show Reasoning", key=f"show_thinking_{idx}", help="View the model's reasoning process"):
                            st.session_state[f"thinking_content_{idx}"] = thinking
                    elif sources:
                        if st.button("📋 Show Sources", key=f"show_sources_{idx}", help="View retrieved documents and context"):
                            st.session_state[f"sources_content_{idx}"] = sources
                else:
                    # Two buttons - use columns
                    cols = st.columns(len(button_cols))
                    col_idx = 0
                    
                    # Display thinking button if exists
                    if thinking:
                        with cols[col_idx]:
                            thinking_key = f"show_thinking_{idx}"
                            if st.button("🧠 Show Reasoning", key=thinking_key, help="View the model's reasoning process"):
                                st.session_state[f"thinking_content_{idx}"] = thinking
                        col_idx += 1
                    
                    # Display sources button if exists
                    if sources:
                        with cols[col_idx]:
                            sources_key = f"show_sources_{idx}"
                            if st.button("📋 Show Sources", key=sources_key, help="View retrieved documents and context"):
                                st.session_state[f"sources_content_{idx}"] = sources
            
            # Show thinking content if button was clicked
            if st.session_state.get(f"thinking_content_{idx}"):
                with st.container():
                    st.markdown("**Model's Reasoning Process:**")
                    thinking_html = thinking.replace("\n", "<br>")
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; color: #333; border-left: 4px solid #007acc;">
                        {thinking_html}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    # Add close button
                    if st.button("❌ Hide Reasoning", key=f"hide_thinking_{idx}"):
                        st.session_state[f"thinking_content_{idx}"] = None
                        st.rerun()
            
            # Show sources content if button was clicked
            if st.session_state.get(f"sources_content_{idx}"):
                with st.container():
                    st.markdown("**Retrieved Documents & Context:**")
                    sources_html = sources.replace("\n", "<br>")
                    st.markdown(
                        f"""
                        <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; color: #333; border-left: 4px solid #28a745;">
                        {sources_html}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    # Add close button
                    if st.button("❌ Hide Sources", key=f"hide_sources_{idx}"):
                        st.session_state[f"sources_content_{idx}"] = None
                        st.rerun()

    # Input only if you can chat
    if "files_ingested" in st.session_state and st.session_state.files_ingested:
        user_question = st.chat_input("Ask about your simulation data...")

        if user_question:
            # Generate a response
            with st.spinner("Analyzing simulation data..."):
                try:
                    answer = generate_response(user_question, run_dir=experiment.get("run_dir"))
                except Exception as e:
                    answer = f"Error generating response: {str(e)}"
            
            # Save the answer to history and to the database
            st.session_state.chat_history.append((user_question, answer))
            save_chat_message(simulation_id, user_question, answer)
            st.rerun()
    else:
        st.warning("Chat is only available for finished experiments with processed output files. Please ensure your experiment is complete and the data has been processed successfully.")
        if experiment and experiment.get("state") == "Finished" and experiment.get("run_dir"):
            if st.button("Process Files for Chat"):
                with st.spinner("Processing simulation files..."):
                    st.session_state.files_ingested = ingest_experiment_data(experiment)

    # Autoscroll
    st.markdown(
        """
        <script>
        window.scrollTo(0, document.body.scrollHeight);
        </script>
        """, unsafe_allow_html=True
    )
