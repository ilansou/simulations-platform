from flask import Blueprint, request, jsonify
import os
from pathlib import Path

from llm.think_step_by_step import analyze_and_explain, think_step_by_step

# Create blueprint
reasoning_bp = Blueprint('reasoning', __name__)

@reasoning_bp.route('/api/reasoning', methods=['POST'])
def get_reasoning():
    """
    API endpoint for getting step-by-step reasoning for simulation analysis.
    
    Expected JSON input:
    {
        "query": "Calculate the total bandwidth",
        "run_dir": "path/to/simulation/results",
        "use_api": true  # Optional, defaults to false
    }
    
    Returns:
    {
        "reasoning": "Step-by-step explanation",
        "result": "Final answer"
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    query = data.get('query')
    run_dir = data.get('run_dir')
    use_api = data.get('use_api', False)
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    if not run_dir:
        return jsonify({"error": "No run_dir provided"}), 400
    
    # Verify run_dir exists
    run_path = Path(run_dir)
    if not run_path.exists():
        return jsonify({"error": f"Run directory {run_dir} does not exist"}), 404
    
    try:
        # Get the reasoning result
        result = analyze_and_explain(query, str(run_path), use_api)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reasoning_bp.route('/api/reasoning/direct', methods=['POST'])
def get_direct_reasoning():
    """
    API endpoint for getting step-by-step reasoning directly from query and context.
    
    Expected JSON input:
    {
        "query": "Calculate the total bandwidth",
        "context": "Optional context information",
        "use_api": true  # Optional, defaults to false
    }
    
    Returns:
    {
        "reasoning": "Step-by-step explanation",
        "result": "Final answer"
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    query = data.get('query')
    context = data.get('context', '')
    use_api = data.get('use_api', False)
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Get the reasoning result
        result = think_step_by_step(query, None, context, use_api)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500 