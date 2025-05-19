import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from llm.retrieval import get_query_results, setup_vector_search_index
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import pandas as pd
import io
import re
import requests
import json

load_dotenv()

# Change to a small model that's definitely available on the free tier
model_name = os.getenv("MODEL_NAME")

# Read FloodNS framework.md as static context for all prompts
def get_framework_context():
    """Read FloodNS framework.md to provide key concepts as context for LLM prompts"""
    framework_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "floodns", "doc", "framework.md")
    try:
        with open(framework_path, "r") as f:
            framework_content = f.read()
        return framework_content
    except Exception as e:
        print(f"Warning: Could not read framework.md: {e}")
        return "Framework document could not be loaded. Key concepts include: Network, Node, Link, Flow, Connection, Event, Aftermath, and Simulator."

# Load the framework context once when the module is imported
FRAMEWORK_CONTEXT = get_framework_context()


def generate_with_ollama(prompt, model_name="deepseek-r1:1.5b"):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "model": model_name,
                "prompt": prompt,
                "stream": False
            })
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        print(f"Error using local Ollama model: {e}")
        return "There was an error calling the local model through Ollama."


def generate_response(query, run_dir=None):
    """Generate a response using DeepSeek model based on retrieved context"""
    try:
        # First check if this is a bandwidth analysis question
        if is_bandwidth_query(query):
            try:
                # Import here to avoid circular imports
                from llm.bandwidth_analysis import analyze_bandwidth_for_chat
                
                # Only use bandwidth analysis if we have a run directory
                if run_dir:
                    return analyze_bandwidth_for_chat(run_dir=run_dir, query=query)
            except Exception as e:
                print(f"Error in bandwidth analysis: {e}")
                # Continue with standard response generation if bandwidth analysis fails
        
        # Check if this is a request for step-by-step reasoning
        if any(phrase in query.lower() for phrase in ["step by step", "explain your thinking", "show your work", "reasoning"]):
            return generate_response_with_reasoning(query)
        
        # Standard response generation
        # Retrieve relevant documents with vector search
        context_docs = get_query_results(query, limit=3)
        
        if not context_docs:
            return "I couldn't find any relevant information in the simulation data to answer your question."
        
        # Extract text and filenames for context
        contexts = []
        filenames = []
        for doc in context_docs:
            filename = doc.get("filename", "unknown file")
            text = doc.get("text", "")
            if text:
                contexts.append(f"From {filename}:\n{text[:1000]}...")
                filenames.append(filename)
        
        # Combine contexts
        context_string = "\n\n".join(contexts)
        
        # Build the RAG prompt with framework context
        prompt = f"""You are an AI assistant analyzing network simulation data. 
Use only the following context to answer the user's question.
Be specific and extract numbers, statistics and factual information from the provided data.
If the data contains CSV content, analyze the structure and count unique entries if needed.
For node counts, count unique node IDs. For bandwidth questions, look for numerical values.

## FloodNS Framework Concepts:
{FRAMEWORK_CONTEXT}

## Simulation Data:
{context_string}

User Question: {query}
Answer:"""
        
        try:
            # Check whether to use local Ollama model or HuggingFace API
            use_local = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
            
            if use_local:
                response = generate_with_ollama(prompt)
            else:
                response = generate_with_api(prompt, context_docs, query)
                
            # Add reasoning block after the main answer
            context_summary = "\n".join([f"- {filename}" for filename in filenames])
            context_preview = "\n".join([doc.get("text", "")[:100] + "..." for doc in context_docs])
            
            reasoning = f"""

--- Reasoning ---
1. Retrieved documents:
{context_summary}

2. Used context:
{context_preview}

3. Based on this information, the answer above was generated.
"""
            
            # Return final response with reasoning
            return f"{response}{reasoning}"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error in generate_response: {error_msg}")
            return fallback_parser(query, context_docs)
    except Exception as e:
        print(f"Error in RAG pipeline: {e}")
        return f"I had trouble searching through the simulation data. Please try again or ask an administrator to check the vector search configuration."


def is_bandwidth_query(query):
    """
    Detect if the query is asking about bandwidth analysis.
    
    This function checks if the query contains keywords related to bandwidth,
    specifically with the flow_bandwidth.csv file.
    """
    query_lower = query.lower()
    
    # Check for bandwidth keywords in combination with file references
    bandwidth_keywords = ['bandwidth', 'throughput', 'speed', 'data rate']
    file_keywords = ['flow', 'flow_bandwidth', 'flow bandwidth', 'flow_bandwidth.csv']
    
    bandwidth_match = any(kw in query_lower for kw in bandwidth_keywords)
    file_match = any(kw in query_lower for kw in file_keywords)
    
    # Check if the query is asking about averages, statistics, etc.
    stat_keywords = ['average', 'avg', 'mean', 'statistics', 'calculate', 'median', 'min', 'max']
    stat_match = any(kw in query_lower for kw in stat_keywords)
    
    # Return true if it's likely a bandwidth query
    return (bandwidth_match and (file_match or stat_match)) or (file_match and stat_match)


def generate_response_with_reasoning(query):
    """Generate a response with step-by-step reasoning"""
    try:
        from llm.think_step_by_step import think_step_by_step
        
        # Retrieve relevant documents with vector search
        context_docs = get_query_results(query, limit=5)  # Get more context for reasoning
        
        if not context_docs:
            return "I couldn't find any relevant information in the simulation data to answer your question."
        
        # Extract text and filenames for context
        contexts = []
        for doc in context_docs:
            filename = doc.get("filename", "unknown file")
            text = doc.get("text", "")
            if text:
                contexts.append(f"From {filename}:\n{text[:1500]}...")  # Include more context
        
        # Combine contexts
        context_string = "\n\n".join(contexts)
        
        # Add framework concepts to the context
        combined_context = f"""## FloodNS Framework Concepts:
{FRAMEWORK_CONTEXT}

## Simulation Data:
{context_string}"""
        
        # Always use API for think_step_by_step
        response = think_step_by_step(query, None, combined_context, use_api=True)
        
        # Format the response
        formatted_response = f"## Step-by-Step Reasoning\n\n{response['reasoning']}\n\n## Final Answer\n\n{response['result']}"
        
        return formatted_response
        
    except Exception as e:
        print(f"Error in reasoning pipeline: {e}")
        return f"I had trouble applying step-by-step reasoning to your question. Error: {str(e)}"


def generate_with_local_model(prompt):
    """Generate text using a local DeepSeek model if available"""
    try:
        # Load model and tokenizer
        model_name = os.getenv("MODEL_NAME")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Try to use GPU if available, otherwise use CPU
        device_map = "auto" if torch.cuda.is_available() else {"": "cpu"}
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            device_map=device_map,
            torch_dtype=dtype
        )
        
        # Generate response
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids
        
        # Move input to correct device
        if torch.cuda.is_available():
            input_ids = input_ids.to("cuda")
        
        # Generate with appropriate parameters
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode and return the response
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract only the answer part after the prompt
        answer = response[len(prompt):]
        return answer.strip()
    
    except Exception as e:
        print(f"Local model inference error: {e}")
        return generate_with_api(prompt)

def generate_with_api(prompt, context_docs=None, query=None):
    """Generate text using the Hugging Face Inference API"""
    try:        
        # Initialize the client
        hf_token = os.getenv("HF_TOKEN")
        model_name = os.getenv("MODEL_NAME")
        if not hf_token:
            print("No Hugging Face token found. Trying without authentication...")
            client = InferenceClient()
        else:
            client = InferenceClient(token=hf_token)
        
        print(f"Sending request to model: {model_name}")
        
        # Generate response using the API
        response = client.text_generation(
            prompt=prompt,
            model=model_name,
            max_new_tokens=150,
            temperature=0.7,
            repetition_penalty=1.1
        )
        
        # Extract the answer part (remove the prompt)
        answer = response[len(prompt):] if len(response) > len(prompt) else response
        return answer.strip()
        
    except Exception as e:
        print(f"API inference error: {e}")
        
        # Add debugging information to help troubleshoot
        print(f"Attempted to use model: {model_name}")
        print("Try running without HF_TOKEN by setting it to an empty string in .env")
        
        # Use the fallback parser if context and query are available
        if context_docs and query:
            print("Using fallback parser to extract information directly from documents")
            return fallback_parser(query, context_docs)
        
        # Manual fallback - extract information from retrieved documents to provide a basic answer
        return "I'm sorry, I couldn't access the language model service. Please try again later."

def fallback_parser(query, context_docs):
    """Directly parse the simulation data when the API is unavailable"""
    query_lower = query.lower()
    
    # Extract information based on query type
    if "node" in query_lower and ("count" in query_lower or "how many" in query_lower):
        # Count unique nodes in node_info.csv
        for doc in context_docs:
            if doc.get("filename") == "node_info.csv":
                text = doc.get("text", "")
                if text:
                    try:
                        # Parse CSV content
                        df = pd.read_csv(io.StringIO(text), header=None)
                        # First column typically contains node IDs
                        node_count = df[0].nunique()
                        return f"Based on the node_info.csv file, there are {node_count} unique nodes in the simulation."
                    except Exception as e:
                        print(f"Error parsing node_info.csv: {e}")
                        # Try a basic line count approach
                        lines = text.strip().split('\n')
                        return f"Based on the node_info.csv file, there appear to be approximately {len(lines)} nodes in the simulation."
                        
    elif "bandwidth" in query_lower and "average" in query_lower:
        # Calculate average bandwidth
        for doc in context_docs:
            if "bandwidth" in doc.get("filename", "").lower():
                text = doc.get("text", "")
                if text:
                    try:
                        # Try to parse the CSV
                        df = pd.read_csv(io.StringIO(text), header=None)
                        # Look for columns that might contain bandwidth values
                        # Typically the last column in bandwidth files
                        last_col = df.columns[-1]
                        # Convert to numeric, ignoring errors
                        bandwidth_values = pd.to_numeric(df[last_col], errors='coerce')
                        # Calculate average of non-NaN values
                        avg_bandwidth = bandwidth_values.mean()
                        return f"Based on {doc.get('filename')}, the average bandwidth is approximately {avg_bandwidth:.2f}."
                    except Exception as e:
                        print(f"Error parsing bandwidth data: {e}")
                        # Try a simpler approach with regex
                        numbers = re.findall(r'[\d.]+', text)
                        if numbers:
                            try:
                                values = [float(num) for num in numbers if float(num) > 0]
                                if values:
                                    avg = sum(values) / len(values)
                                    return f"Based on {doc.get('filename')}, the average bandwidth is approximately {avg:.2f}."
                            except:
                                pass
    
    # General fallback for other queries
    filenames = [doc.get("filename", "unknown") for doc in context_docs]
    return f"I found relevant information in {', '.join(filenames)}, but couldn't process it automatically. The API service is currently unavailable."
