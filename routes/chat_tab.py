import streamlit as st
from llm.generate import generate_response
from routes.chat_utils import load_chat_history, save_chat_message, ingest_experiment_data
import re

def parse_thinking_tags(text):
    """
    Parse a response containing <thinking> tags and return content and thinking parts.
    
    Args:
        text (str): The input text with potential <thinking> tags
    
    Returns:
        tuple: (content, thinking) where thinking may be None if not present
    """
    thinking_pattern = r'<thinking>(.*?)</thinking>'
    thinking_match = re.search(thinking_pattern, text, re.DOTALL)
    
    if thinking_match:
        thinking = thinking_match.group(1).strip()
        # Remove the thinking tags and content from the main text
        content = re.sub(thinking_pattern, '', text, flags=re.DOTALL).strip()
        return content, thinking
    else:
        return text, None

def render_chat_tab(simulation_id, experiment):
    st.title("Chat with Your Simulation Data")

    # Load chat history from the database (once at startup)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history(simulation_id)

    # Information about available files and sample questions
    if "files_ingested" in st.session_state and st.session_state.files_ingested:
        st.info(f"You can ask questions about these simulation files: {', '.join(st.session_state.get('ingested_files', []))}")
        with st.expander("Example questions you can ask"):
            st.write("- What is the average bandwidth in the flow_bandwidth.csv file?")
            st.write("- How many nodes are in the simulation?")
            st.write("- Summarize the connection information data.")

    # Show chat history (UI only here)
    for idx, (question, answer) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            # Parse the answer to separate thinking part if exists
            content, thinking = parse_thinking_tags(answer)
            
            # Display the main content
            st.markdown(content)
            
            # Display the thinking part in a collapsible gray section if it exists
            if thinking:
                with st.expander("Click to see step-by-step thinking"):
                    # Creating a gray background using markdown and replacing newlines with HTML breaks
                    thinking_html = thinking.replace("\n", "<br>")
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; color: #333;">
                        {thinking_html}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

    # Input only if you can chat
    if "files_ingested" in st.session_state and st.session_state.files_ingested:
        user_question = st.chat_input("Ask about your simulation data...")

        if user_question:
            # First, add a question with an empty answer
            st.session_state.chat_history.append((user_question, ""))
            # Generate a response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing simulation data..."):
                    try:
                        answer = generate_response(user_question, run_dir=experiment.get("run_dir"))
                    except Exception as e:
                        answer = f"Error generating response: {str(e)}"
                
                # Parse the answer to separate thinking part if exists
                content, thinking = parse_thinking_tags(answer)
                
                # Display the main content
                st.markdown(content)
                
                # Display the thinking part in a collapsible gray section if it exists
                if thinking:
                    with st.expander("Click to see step-by-step thinking"):
                        # Creating a gray background using markdown and replacing newlines with HTML breaks
                        thinking_html = thinking.replace("\n", "<br>")
                        st.markdown(
                            f"""
                            <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; color: #333;">
                            {thinking_html}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
            
            # We save the answer to history and to the database
            st.session_state.chat_history[-1] = (user_question, answer)
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
