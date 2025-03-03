import streamlit as st
from llm.rag_pipeline import RAGPipeline

def run():
    st.title("Query Simulation Data")

    # Initialize RAG pipeline
    rag = RAGPipeline()

    # Input for user query
    question = st.text_input("Enter your question:")

    if st.button("Submit"):
        if question:
            # Get the answer from the RAG pipeline
            answer = rag.query(question)
            st.write(f"**Answer:** {answer}")
        else:
            st.write("Please enter a question.")

if __name__ == "__main__":
    run()
