import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from llm.retrieval import get_query_results, setup_vector_search_index
from huggingface_hub import InferenceClient


def generate_response(query):
    """Generate a response using DeepSeek model based on retrieved context"""
    try:
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
        for doc in context_docs:
            filename = doc.get("filename", "unknown file")
            text = doc.get("text", "")
            if text:
                contexts.append(f"From {filename}:\n{text[:1000]}...")
        
        # Combine contexts
        context_string = "\n\n".join(contexts)
        
        # Build the RAG prompt
        prompt = f"""You are an AI assistant analyzing network simulation data. 
Use only the following context to answer the user's question.
If you don't have enough information in the context, say you don't know.

Context:
{context_string}

User Question: {query}
Answer:"""
        
        try:
            # Try inference with local model if available
            if torch.cuda.is_available():
                return generate_with_local_model(prompt)
            else:
                # Otherwise, use Hugging Face Inference API
                return generate_with_api(prompt)
        except Exception as e:
            error_msg = str(e)
            print(f"Error in generate_response: {error_msg}")
            return f"Sorry, I encountered an error while analyzing the simulation data. Please try again later."
    except Exception as e:
        print(f"Error in RAG pipeline: {e}")
        return f"I had trouble searching through the simulation data. Please try again or ask an administrator to check the vector search configuration."


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
        
        # Use think_step_by_step to generate reasoned response
        response = think_step_by_step(query, None, context_string, use_api=not torch.cuda.is_available())
        
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
        model_name = "deepseek-ai/DeepSeek-V3-0324"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Move model to GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        
        # Generate response
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
        
        # Use shorter sequence for CPU to avoid memory issues
        max_length = 512 if device == "cpu" else 1024
        
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

def generate_with_api(prompt):
    """Generate text using the Hugging Face Inference API"""
    try:        
        # Initialize the client
        hf_token = os.getenv("HF_TOKEN")
        client = InferenceClient(token=hf_token)
        
        # Generate response using the API
        response = client.text_generation(
            prompt=prompt,
            model="deepseek-ai/DeepSeek-V3-0324",
            max_new_tokens=150,
            temperature=0.7,
            repetition_penalty=1.1
        )
        
        # Extract the answer part (remove the prompt)
        answer = response[len(prompt):] if len(response) > len(prompt) else response
        return answer.strip()
        
    except Exception as e:
        print(f"API inference error: {e}")
        return "I'm sorry, I couldn't access the language model service. Please try again later."
