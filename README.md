docker-compose down
docker-compose rm -f
docker-compose build --no-cache

docker-compose up

# Simulations Platform: Comprehensive Documentation

**Authors**: Yosi Matatov and Ilan Shushan  
**Project**: AI-Powered Network Simulation Framework

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Core Components](#core-components)
5. [Usage Guide](#usage-guide)
6. [API Reference](#api-reference)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Contributing](#contributing)
11. [FAQ](#faq)

---

## Project Overview

The **Simulations Platform** is a comprehensive network simulation framework built around the FloodNS simulation engine. It provides a modern web-based interface for running, managing, and analyzing network simulations with AI-powered insights. The platform is specifically designed for simulating distributed training workloads and network traffic patterns in data center environments.

### What This Platform Does

- **Network Flow Simulation**: Simulates routed flows over time using the FloodNS engine
- **Distributed Training Simulation**: Models traffic patterns for distributed deep learning training jobs
- **Web-Based Management**: Provides a Streamlit dashboard for experiment management
- **AI-Powered Analysis**: Integrates LLM capabilities for intelligent data analysis and insights
- **Experiment Tracking**: Stores and manages simulation experiments with MongoDB persistence
- **Visualization & Analytics**: Generates comprehensive reports and visualizations from simulation data

### Key Features

- ⚡ **High Performance**: Flow-level simulation is faster than packet-level alternatives
- 🎯 **Specialized**: Optimized for distributed training workload simulations
- 🌐 **Web Interface**: Modern Streamlit-based dashboard
- 🤖 **AI Integration**: LLM-powered data analysis and querying
- 📊 **Rich Analytics**: Comprehensive bandwidth, utilization, and performance metrics
- 🔧 **Extensible**: Built on the robust FloodNS framework
- 📈 **Scalable**: Supports multi-job concurrent simulations

---

## Architecture

The platform follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │◄───┤   Application   │◄───┤   Simulation    │
│   (Streamlit)   │    │     Layer       │    │     Engine      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Routes   │    │   Business      │    │    FloodNS      │
│   & Interface   │    │     Logic       │    │   (Java Core)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Analysis  │    │    MongoDB      │    │   File System   │
│   & Retrieval   │    │   Persistence   │    │   (Logs/Data)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Architectural Components

1. **Frontend Layer** (`app.py`, `routes/`)
   - Streamlit-based web application
   - Multi-page navigation system
   - Real-time experiment monitoring

2. **Simulation Engine** (`floodns/`)
   - Java-based FloodNS core simulation engine
   - Python wrappers and utilities
   - Routing algorithms and network topology management

3. **AI/LLM Layer** (`llm/`)
   - Vector-based document retrieval
   - Query processing and response generation
   - Bandwidth analysis and reporting

4. **Data Persistence** (`db_client.py`, `mongo_data/`)
   - MongoDB for experiment metadata
   - File system storage for simulation outputs
   - Session state management

---

## Quick Start

For experienced users who want to get the platform running quickly:

```bash
# 1. Setup environment
git clone <repository-url>
cd simulations-platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Setup MongoDB (Ubuntu/Debian)
sudo systemctl start mongod

# 3. Build FloodNS engine
cd floodns
make install-python-requirements
make compile-maven
cd ..

# 4. Setup environment variables
cat > .env << EOF
MONGODB_URI=mongodb://localhost:27017/experiment_db
FLOODNS_ROOT=$(pwd)/floodns
MODEL_NAME=deepseek-r1:1.5b
OLLAMA_NUM_GPU=0
OLLAMA_DEBUG=true
CUDA_VISIBLE_DEVICES=""
EOF

# 5. Start Ollama (optional, for LLM features)
OLLAMA_NUM_GPU=0 OLLAMA_DEBUG=true CUDA_VISIBLE_DEVICES="" ollama serve &
ollama pull deepseek-r1:1.5b

# 6. Launch application
streamlit run app.py
```

---

## Installation & Setup

### Prerequisites

**System Requirements:**
- Python 3.12 or higher
- Java 8 or higher (for FloodNS simulation engine)
- MongoDB 4.0 or higher
- 4GB+ RAM (8GB+ recommended for large simulations)
- Linux/Unix environment (WSL supported on Windows)

**Software Dependencies:**
- Maven 3+ (for Java compilation)
- Poetry (Python package manager)
- Git (for version control)

### Step-by-Step Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd simulations-platform
```

#### 2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 3. MongoDB Setup
```bash
# Option 1: Local MongoDB installation
sudo apt-get install mongodb-community
sudo systemctl start mongod

# Option 2: Docker MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

#### 4. FloodNS Engine Setup

**Option 1: Using Makefile (Recommended):**
```bash
cd floodns

# Install Python dependencies
make install-python-requirements

# Maven compilation
make compile-maven

cd ..
```

**Option 2: Manual compilation:**
```bash
cd floodns

# Install Python dependencies
poetry install

# Maven compilation
mvn clean compile assembly:single
mv target/floodns-*-jar-with-dependencies.jar floodns-basic-sim.jar

# Optional: Install in system maven repository
mvn source:jar javadoc:jar install

cd ..
```

#### 5. Environment Variables
Create a `.env` file in the project root:
```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/experiment_db

# LLM Configuration (optional)
MODEL_NAME=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434

# Ollama Environment Variables (for CPU-only usage)
OLLAMA_NUM_GPU=0
OLLAMA_DEBUG=true
CUDA_VISIBLE_DEVICES=""

# Application Settings
FLOODNS_ROOT=/path/to/your/simulations-platform/floodns
```

#### 6. Setup Ollama LLM (Optional)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download and run the model (CPU-only setup)
OLLAMA_NUM_GPU=0 \
OLLAMA_DEBUG=true \
CUDA_VISIBLE_DEVICES="" \
ollama run deepseek-r1:1.5b

# Alternative: Run Ollama in the background
OLLAMA_NUM_GPU=0 OLLAMA_DEBUG=true CUDA_VISIBLE_DEVICES="" ollama serve &
ollama pull deepseek-r1:1.5b
```

#### 7. Verify Installation
```bash
# Test MongoDB connection
python -c "from db_client import db_client; print('MongoDB:', 'Connected' if db_client else 'Failed')"

# Test FloodNS engine (using Makefile)
cd floodns && make run-basic-sim

# Or test manually
cd floodns && java -jar floodns-basic-sim.jar test_data/1_to_1_capacity_10.properties

# Test Ollama connection
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-r1:1.5b", "prompt": "Hello, are you working?"}'
```

### Development Setup

For development environments, additional setup is recommended:

```bash
# Install development dependencies
pip install black isort pytest mypy

# Setup pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
pytest tests/
```

---

## Core Components

### 1. FloodNS Simulation Engine

The FloodNS engine forms the computational core of the platform:

**Key Concepts:**
- **Network(V, E, F)**: Network with nodes (V), links (E), and flows (F)
- **Flow**: Stream from source to target with bandwidth allocation
- **Connection**: Abstraction for desired data transport requirements
- **Event**: User-defined simulation events
- **Aftermath**: State consistency enforcement (e.g., max-min fair allocation)

**Flow Simulation Process:**
1. Initialize network topology
2. Schedule connection events
3. Execute time-driven simulation
4. Apply routing algorithms
5. Generate detailed logs

### 2. Web Interface Components

#### Dashboard (`routes/dashboard.py`)
- **Experiment Management**: Create, edit, delete simulations
- **Real-time Monitoring**: Track simulation progress and status
- **Parameter Validation**: Ensure valid simulation configurations
- **Bulk Operations**: Handle multiple experiments efficiently

#### Configuration Management (`routes/configurations.py`)
- **Parameter Templates**: Pre-defined simulation configurations
- **Validation Rules**: Enforce parameter constraints
- **Export/Import**: Save and load configuration sets

#### Experiment Details (`routes/experiment_details.py`)
- **Detailed Views**: Comprehensive experiment information
- **Log Analysis**: Browse and analyze simulation outputs
- **Performance Metrics**: Extract key performance indicators
- **Data Export**: Download results in various formats

### 3. LLM Integration

#### Query Processing (`llm/generate.py`)
The LLM system provides intelligent analysis of simulation data:

**Supported Query Types:**
- Bandwidth analysis questions
- Performance comparisons
- Statistical queries
- Multi-experiment analysis

**Key Features:**
- **Context-Aware**: Uses FloodNS framework knowledge
- **Multi-Model Support**: DeepSeek, Ollama integration
- **Document Retrieval**: Vector-based search through simulation data
- **Reasoning Chain**: Step-by-step analysis explanations

#### Bandwidth Analysis (`llm/bandwidth_analysis.py`)
Specialized component for bandwidth-related queries:
- Automatic CSV parsing
- Statistical calculations (mean, median, min, max)
- Query-specific responses
- Detailed reasoning explanations

### 4. Data Management

#### Database Layer (`db_client.py`)
- **Connection Management**: Cached MongoDB connections
- **Error Handling**: Robust connection failure recovery
- **Collections**: Experiments and chat data persistence

#### File System Management
- **Simulation Outputs**: CSV logs, analysis results
- **Directory Structure**: Organized by seeds, jobs, and parameters
- **Log Rotation**: Automatic cleanup of old simulation data

---

## Usage Guide

### Running Your First Simulation

#### 1. Start the Application
```bash
# Ensure MongoDB is running
sudo systemctl start mongod

# Start Ollama service (if using LLM features)
OLLAMA_NUM_GPU=0 OLLAMA_DEBUG=true CUDA_VISIBLE_DEVICES="" ollama serve &

# Activate virtual environment
source .venv/bin/activate  # or: source venv/bin/activate

# Launch the web application
streamlit run app.py
```

#### 2. Create a New Simulation
1. Navigate to the Dashboard
2. Fill in simulation parameters:
   - **Jobs**: Number of concurrent training jobs (1-5)
   - **Core Failures**: Number of failed cores (0, 1, 4, 8)
   - **Ring Size**: Data parallelism dimension (2, 4, 8, or "different")
   - **Routing Algorithm**: ECMP, ILP Solver, Simulated Annealing, etc.
   - **Seed**: Random seed for reproducibility
   - **Model**: For single jobs (BLOOM, GPT_3, LLAMA2_70B)

3. Click "Run Simulation"

#### 3. Monitor Progress
- Check the dashboard for simulation status
- View real-time updates
- Wait for completion (indicated by "Finished" status)

#### 4. Analyze Results
- Navigate to Experiment Details
- Browse generated CSV files
- Use the chat interface for AI-powered analysis
- Export data for further processing

### Advanced Usage

#### Batch Simulations

**Using Python API:**
```python
# Example: Run multiple parameter sweeps
from floodns.external.simulation.main import local_run_multiple_jobs

# Parameter combinations
seeds = [0, 42, 200, 404, 1234]
job_counts = [2, 3, 4, 5]
routing_algorithms = ['ecmp', 'ilp_solver', 'simulated_annealing']

for seed in seeds:
    for jobs in job_counts:
        for alg in routing_algorithms:
            # Run simulation with current parameters
            local_run_multiple_jobs(seed, jobs, 8, alg, 0)
```

**Using Makefile Commands:**
```bash
# Run simulation of DNN training job traffic
cd floodns

# Example: 3 jobs, 1 core failure, ring size 8, ECMP algorithm
make simulate-jobs-single-alg JOBS=3 CORES=1 RING=8 ALG=ecmp

# Example: Basic simulation
make run-basic-sim
```

**Using Command Line:**
```bash
# Using Python module directly
python -m floodns.external.simulation.main.local_run 3 64 1 8 ecmp

# Using JAR file directly
java -jar floodns/floodns-basic-sim.jar /path/to/run/directory
```

---

## API Reference

### Simulation Functions

#### `local_run_single_job(seed, n_core_failures, ring_size, model, alg)`
Runs a simulation with a single training job.

**Parameters:**
- `seed` (int): Random seed for reproducibility
- `n_core_failures` (int): Number of failed core switches
- `ring_size` (int|str): Data parallelism dimension or "different"
- `model` (str): ML model type (BLOOM, GPT_3, LLAMA2_70B)
- `alg` (Routing): Routing algorithm enum

**Returns:**
- `Popen`: Process object for the running simulation

#### `local_run_multiple_jobs(seed, n_jobs, ring_size, alg, n_core_failures)`
Runs a simulation with multiple concurrent training jobs.

**Parameters:**
- `seed` (int): Random seed
- `n_jobs` (int): Number of concurrent jobs (2-5)
- `ring_size` (int): Data parallelism dimension
- `alg` (Routing): Routing algorithm
- `n_core_failures` (int): Number of failed cores

### Database Functions

#### `fetch_all_experiments()`
Retrieves all experiments from MongoDB.

**Returns:**
- `list`: List of experiment dictionaries with converted ObjectIds

#### `create_new_simulation(simulation_name, params)`
Creates a new simulation entry in the database.

**Parameters:**
- `simulation_name` (str): Human-readable name
- `params` (str): Comma-separated parameter string

---

## Configuration

### Parameter Validation Rules

The platform enforces strict validation rules to ensure simulation validity:

**Valid Parameter Combinations:**
```python
VALID_PARAMETERS = {
    'num_jobs': [1, 2, 3, 4, 5],
    'num_cores': [0, 1, 4, 8],
    'ring_sizes': [2, 4, 8, "different"],
    'routing_algorithms': ["ecmp", "ilp_solver", "simulated_annealing", 
                          "edge_coloring", "mcvlc"],
    'seeds': [0, 42, 200, 404, 1234],
    'models': ["BLOOM", "GPT_3", "LLAMA2_70B"]  # Only for single jobs
}
```

**Constraint Rules:**
- Jobs 1-3: Ring sizes 2, 8, or "different"
- Jobs 4-5: Ring sizes 2, 4, or "different"
- Single job: Must specify model type
- Multiple jobs: Model parameter ignored

### Environment Configuration

**Required Environment Variables:**
```bash
# Database
MONGODB_URI=mongodb://localhost:27017/experiment_db

# Application
FLOODNS_ROOT=/absolute/path/to/floodns/directory

# Optional LLM Settings
MODEL_NAME=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. MongoDB Connection Failed
**Symptoms:**
- "Failed to connect to MongoDB" error
- Database operations failing

**Solutions:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Restart MongoDB
sudo systemctl restart mongod

# Verify port availability
netstat -tulpn | grep 27017

# Check environment variables
echo $MONGODB_URI
```

#### 2. FloodNS Simulation Errors
**Symptoms:**
- Java compilation errors
- Simulation hangs or crashes
- Missing JAR file

**Solutions:**
```bash
# Rebuild FloodNS JAR
cd floodns
mvn clean compile assembly:single

# Verify Java version
java -version  # Should be 8+

# Check file permissions
ls -la floodns-basic-sim.jar

# Test with sample data
java -jar floodns-basic-sim.jar test_data/1_to_1_capacity_10.properties
```

#### 3. LLM Integration Issues
**Symptoms:**
- AI queries returning errors
- Model not responding
- Bandwidth analysis failing

**Solutions:**
```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Restart Ollama
systemctl restart ollama

# Verify model availability
ollama list

# Test local model (CPU-only setup)
OLLAMA_NUM_GPU=0 OLLAMA_DEBUG=true CUDA_VISIBLE_DEVICES="" ollama run deepseek-r1:1.5b "Hello"

# Or if Ollama is already running as service
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-r1:1.5b", "prompt": "Hello"}'
```

---

## Best Practices

### Simulation Design

#### 1. Parameter Selection
- **Start Small**: Begin with single jobs and simple topologies
- **Systematic Exploration**: Use parameter sweeps for comprehensive analysis
- **Reproducibility**: Always use consistent seeds for comparable results
- **Documentation**: Record parameter rationale and expected outcomes

#### 2. Resource Management
- **Memory Monitoring**: Large simulations can consume significant RAM
- **Disk Space**: Simulation logs can grow quickly; implement rotation
- **Parallel Execution**: Limit concurrent simulations based on system capacity
- **Backup Strategy**: Regular backup of experiment database and results

### Development Practices

#### 1. Code Organization
- **Modular Design**: Separate concerns into distinct modules
- **Error Handling**: Implement comprehensive exception handling
- **Testing**: Write unit tests for critical components
- **Documentation**: Maintain inline documentation and docstrings

#### 2. Security Considerations
- **Environment Variables**: Never commit secrets to version control
- **Input Validation**: Sanitize all user inputs
- **Access Control**: Implement proper authentication if deploying publicly
- **Network Security**: Secure MongoDB connections in production

---

## Contributing

### Development Environment Setup

#### 1. Fork and Clone
```bash
git clone https://github.com/your-username/simulations-platform.git
cd simulations-platform
git remote add upstream https://github.com/original-repo/simulations-platform.git
```

#### 2. Development Dependencies
```bash
pip install -e ".[dev]"
pip install pre-commit black isort mypy pytest
pre-commit install
```

#### 3. Branch Strategy
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Regular commits with descriptive messages
git commit -m "feat: add bandwidth analysis visualization"

# Push and create PR
git push origin feature/your-feature-name
```

### Code Standards

#### 1. Python Style Guide
- Follow PEP 8 standards
- Use type hints where appropriate
- Maximum line length: 88 characters (Black default)
- Use descriptive variable and function names

#### 2. Documentation Standards
- Docstrings for all public functions
- Inline comments for complex logic
- README updates for new features
- API documentation for new endpoints

---

## FAQ

### General Questions

#### Q: What is the difference between FloodNS and packet-level simulators?
**A:** FloodNS is a flow-level simulator, meaning it models network flows and their bandwidth allocation over time without simulating individual packets. This makes it:
- **Faster**: Runtime depends on flow calculations, not packet processing
- **Scalable**: Can handle large-scale simulations efficiently
- **Limited**: Cannot model packet-level phenomena like queuing delay or congestion control

#### Q: How do I choose the right parameters for my simulation?
**A:** Parameter selection depends on your research goals:

**For Distributed Training Studies:**
- **Jobs**: Match your target training scenario (single vs. multi-job)
- **Ring Size**: Consider your model's data parallelism requirements
- **Core Failures**: Test resilience under failure conditions
- **Routing**: Compare different algorithms for your workload

**For Network Analysis:**
- **Topology**: Choose representative network architectures
- **Seeds**: Use multiple seeds for statistical significance
- **Algorithms**: Compare routing strategies systematically

#### Q: Can I use this platform for non-ML workloads?
**A:** Yes, while optimized for distributed training, the platform can simulate any network workload by:
- Modifying traffic patterns in `floodns/external/jobs_generator/`
- Creating custom topology files
- Implementing new routing strategies
- Adapting the analysis tools for your metrics

### Technical Questions

#### Q: How do I add a new routing algorithm?
**A:** To add a new routing algorithm:

1. **Implement the Algorithm:**
```python
# In floodns/external/routing/
class MyRoutingStrategy(RoutingStrategy):
    def route_connection(self, connection):
        # Your routing logic here
        paths = self.find_paths(connection.source, connection.destination)
        return self.select_best_paths(paths)
```

2. **Register the Algorithm:**
```python
# In floodns/external/schemas/routing.py
class Routing(Enum):
    MY_ALGORITHM = "my_algorithm"
```

3. **Update UI:**
Add the new algorithm to valid options in `routes/valid_options.py`

#### Q: How can I customize the analysis output?
**A:** You can customize analysis in several ways:

1. **Modify Existing Analysis:**
```python
# In llm/bandwidth_analysis.py
def custom_bandwidth_analysis(run_dir, query):
    stats = get_bandwidth_stats(run_dir)
    # Add your custom metrics
    custom_metrics = calculate_custom_metrics(stats)
    return format_custom_response(custom_metrics)
```

2. **Add New Analysis Types:**
```python
# Create new analysis modules
def latency_analysis(run_dir):
    # Analyze connection latency data
    pass

def utilization_analysis(run_dir):
    # Analyze link utilization patterns
    pass
```

### Troubleshooting FAQ

#### Q: My simulation hangs indefinitely. What should I check?
**A:** Common causes and solutions:

1. **Java Process Issues:**
```bash
# Check for hanging Java processes
ps aux | grep java

# Kill stuck processes
pkill -f floodns-basic-sim.jar
```

2. **Resource Exhaustion:**
```bash
# Monitor memory usage
free -h
# Check disk space
df -h
# Monitor CPU usage
top
```

3. **Invalid Parameters:**
- Verify parameter combinations against validation rules
- Check topology file syntax
- Ensure all required files exist

#### Q: The LLM analysis returns incorrect results. How do I debug this?
**A:** Debug LLM issues systematically:

1. **Data Verification:**
```python
# Check if simulation data exists
import os
data_files = ['flow_bandwidth.csv', 'connection_info.csv', 'link_utilization.csv']
for file in data_files:
    if os.path.exists(f"{run_dir}/{file}"):
        print(f"✓ {file} found")
    else:
        print(f"✗ {file} missing")
```

2. **LLM Service Check:**
```bash
# Test Ollama connection
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-r1:1.5b", "prompt": "test"}'
```

3. **Query Debugging:**
```python
# Enable debug logging
import logging
logging.getLogger('llm.generate').setLevel(logging.DEBUG)
```

---

## License and Support

### License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Support and Community

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Keep this documentation updated with changes
- **Community**: Contribute to discussions and share experiences
- **Maintainers**: Contact project maintainers for technical support

### Citation

If you use this platform in academic research, please cite:

```bibtex
@software{simulations_platform,
  title={Simulations Platform: AI-Powered Network Simulation Framework},
  author={Yosi Matatov and Ilan Shushan},
  year={2025},
  url={https://github.com/[repository-url]}
}
```

---

**Version**: 1.0.0  
**Last Updated**: July 2025  
**Authors**: Yosi Matatov and Ilan Shushan  