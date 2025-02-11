# floodns: temporal routed flow simulation

[![Build Status](https://travis-ci.com/snkas/floodns.svg?branch=master)](https://travis-ci.com/snkas/floodns) [![codecov](https://codecov.io/gh/snkas/floodns/branch/master/graph/badge.svg)](https://codecov.io/gh/snkas/floodns)

This is a flow-level simulator to simulate routed flows over time. The abstraction is between a flow optimization (e.g.,
via a linear program) and a packet-level simulation (e.g., ns-3). It does not model packets, but it calculates the rate
of flows over time.

As a consequence, simulating large flows is generally quicker because the runtime is determined by the calculation of
rate assignment rather than individual packet interactions as is the case for packet-level simulation. On the other
side, this means that because packets are not modeled, (a) latency, (b) queueing, and (c) end-point congestion control
cannot be directly modeled. Additionally, because flows must be routed along acyclic paths in the current model
abstraction, you cannot apply perfect-split traffic engineering.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. (see also the MIT License in
./LICENSE).**

## Overview

### Requirements

* Java 8 or higher (check: `java -version`)
* Maven 3 or higher (check: `mvn --version`)
* Python 3.7 or higher (check: `python --version`)
* Poetry (python package manager) (check: `poetry --version`)
* Gnuplot 4.4 or higher (check: `gnuplot --version`)

### Installation & Building

All installations can be done using Makefile commands, or manually.

- Using Makefile commands:
    1. Install Python dependencies:
       ```bash
       make install-python-requirements
       ```
    2. Maven compilation:
       ```bash
       make compile-maven
       ```
- Manually:
    1. Install Python dependencies:
       ```bash
       poetry install
       ```
    2. Maven compilation:
       ```bash
       mvn clean compile assembly:single
       mv target/floodns-*-jar-with-dependencies.jar floodns-basic-sim.jar
       ```
    3. Install in your system's maven repository:
       ```bash
       mvn source:jar javadoc:jar install
       ```

### Running

- Using Makefile commands:
    1. Run basic simulation:
        ```bash
          make run-basic-sim
        ```
    2. Run simulation of DNN training job traffic:
        ```bash
          make simulate-jobs-single-alg JOBS=X CORES=Y RING=Z ALG=W
        ```
- Manually:
    1. Using the jar file:
        ```bash
          java -jar floodns-basic-sim.jar FOLDER
        ```
    2. Using the python script:
        ```bash
          python -m external.simulation.main.local_run NUM_JOBS NUM_TORS NUM_FAILED_CORES RING_SIZE ROUTING_ALGORITHM
        ```

### Getting started

There are two possible ways to get started:

(A) **Basic simulation** which limits you to a simple static topology and a simple flow arrival connectionSchedule. You
only have to generate simple intuitive files to use the simulator. Please follow the
tutorial `doc/tutorial_basic_sim.md`

(B) **Programmatically** make use of floodns yourself and extend it to fit your particular use case. Basic simulation is
still a good example of good experimental practice and separation of concerns. Please follow the
tutorial `doc/tutorial_code_yourself.md`

Beyond that, there is further documentation found in `doc/`, including:

* An overview of the entire framework: `doc/framework.md`

### Testing (optional)

Run all tests:

```bash
mvn test
```

Coverage report can be found in: `target/site/jacoco`
