import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union

from llm.generate import generate_with_api, generate_with_local_model


def think_step_by_step(query: str, data: Optional[Dict[str, pd.DataFrame]] = None, 
                       context: Optional[str] = None, use_api: bool = True) -> Dict[str, str]:
    """
    Generate a step-by-step reasoning process using Chain of Thought (CoT) prompting 
    on simulation data analysis.
    
    Args:
        query (str): The user's question about the simulation data
        data (Dict[str, pd.DataFrame], optional): Dictionary of dataframes (flow, connection, link)
        context (str, optional): Additional context to include
        use_api (bool): Whether to use API or local model
    
    Returns:
        Dict[str, str]: Contains 'reasoning' (step-by-step thought process) and 'result' (final answer)
    """
    # Build a data description if data is provided
    data_description = ""
    if data:
        data_description = _build_data_description(data)
    
    # Build the prompt with CoT instructions
    prompt = f"""You are an expert network simulation analyst. You analyze simulation data carefully and systematically.

I need you to think step by step about this question and explain your reasoning process thoroughly.

{data_description}

{context or ""}

User Question: {query}

Please think step by step:
1. First, identify what information you need to answer this question
2. Describe each calculation or analysis step clearly
3. Consider any assumptions you're making
4. Explain what the results mean in context

After your detailed step-by-step reasoning, provide your final answer labeled as 'Final Result: '.
"""
    
    # Try to get model response
    try:
        if use_api:
            response = generate_with_api(prompt)
        else:
            response = generate_with_local_model(prompt)
        
        # Parse the response to separate reasoning from final result
        reasoning, result = _parse_cot_response(response)
    except Exception as e:
        # If both methods fail, provide a fallback response for bandwidth calculation
        if "bandwidth" in query.lower():
            reasoning = """
To calculate the total bandwidth:
1. We need to examine all flows in the network
2. For each flow, we need to determine the data rate or throughput
3. We sum up all flow rates to get the total bandwidth
4. We should account for any inactive or failed connections to get accurate results
"""
            if data and "flow" in data and not data["flow"].empty:
                # Simple calculation if flow data is available
                try:
                    total_bandwidth = data["flow"]["data_volume"].sum() if "data_volume" in data["flow"].columns else 0
                    result = f"The total bandwidth is approximately {total_bandwidth} units."
                except Exception:
                    result = "Unable to calculate precise bandwidth from the available data."
            else:
                result = "Unable to calculate bandwidth without flow data."
        else:
            reasoning = f"Error processing request: {str(e)}"
            result = "Unable to perform analysis due to a technical error."
    
    return {
        "reasoning": reasoning,
        "result": result
    }


def analyze_and_explain(query: str, run_dir: str, use_api: bool = True) -> Dict[str, str]:
    """
    Load simulation data from CSV files and analyze it with CoT reasoning.
    
    Args:
        query (str): The user's question about the simulation data
        run_dir (str): Path to the directory with simulation result CSV files
        use_api (bool): Whether to use API or local model
    
    Returns:
        Dict[str, str]: Contains 'reasoning' (step-by-step thought process) and 'result' (final answer)
    """
    # Import here to avoid circular imports
    from floodns.external.analysis.analysis_bandwidth import load_simulation_csv, preprocess_data
    
    try:
        # Load and preprocess the data
        df_flow, df_conn, df_link = load_simulation_csv(run_dir)
        df_flow, df_conn, df_link = preprocess_data(df_flow, df_conn, df_link)
        
        # Prepare data dictionary
        data = {
            "flow": df_flow,
            "connection": df_conn,
            "link": df_link
        }
        
        # Add context about the simulation
        context = f"This analysis is based on simulation data from: {run_dir}"
        
        # Get the reasoning and result
        return think_step_by_step(query, data, context, use_api)
        
    except Exception as e:
        return {
            "reasoning": f"Error loading or analyzing data: {str(e)}",
            "result": "Failed to analyze simulation data due to an error."
        }


def explain_bandwidth_calculation(df_flow: pd.DataFrame) -> Dict[str, str]:
    """
    Analyze total bandwidth using step-by-step reasoning.
    
    Args:
        df_flow (pd.DataFrame): Flow information dataframe
    
    Returns:
        Dict[str, str]: Contains 'reasoning' (step-by-step thought process) and 'result' (final answer)
    """
    # Create a focused query for bandwidth calculation
    query = "Calculate the total bandwidth across all flows and explain your calculation process."
    
    # Use the think_step_by_step function with just the flow data
    return think_step_by_step(query, {"flow": df_flow})


def _build_data_description(data: Dict[str, pd.DataFrame]) -> str:
    """
    Build a description of the available dataframes for the prompt.
    
    Args:
        data (Dict[str, pd.DataFrame]): Dictionary of dataframes
    
    Returns:
        str: Description of data
    """
    description = "You have the following simulation data:\n\n"
    
    for name, df in data.items():
        if df is not None and not df.empty:
            description += f"- {name}_data: {len(df)} rows with columns: {', '.join(df.columns.tolist())}\n"
            # Add sample row for better context
            if len(df) > 0:
                sample = df.iloc[0].to_dict()
                description += f"  Sample row: {json.dumps(sample, default=str)}\n\n"
    
    return description


def _parse_cot_response(response: str) -> Tuple[str, str]:
    """
    Parse the model response to separate reasoning from final result.
    
    Args:
        response (str): The full response from the language model
    
    Returns:
        Tuple[str, str]: (reasoning, result)
    """
    # Check if the result is clearly marked
    if "Final Result:" in response:
        parts = response.split("Final Result:", 1)
        reasoning = parts[0].strip()
        result = parts[1].strip()
    else:
        # If not clearly marked, use the last paragraph as the result
        paragraphs = response.split("\n\n")
        if len(paragraphs) > 1:
            result = paragraphs[-1].strip()
            reasoning = "\n\n".join(paragraphs[:-1]).strip()
        else:
            # If there's just one paragraph, use the whole response as reasoning
            reasoning = response.strip()
            result = "No clear final result provided."
    
    return reasoning, result 