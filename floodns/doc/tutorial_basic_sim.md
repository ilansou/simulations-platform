# Tutorial: basic simulation

## Getting started

1. In the README tutorial you generated the executable jar `floodns-basic-sim.jar`. This is
   now used as our primary executable.

2. The executable jar takes one argument, the run directory:

   ```
   java -jar floodns-basic-sim.jar [run directory]
   ```

   As an example, execute:

   ```
   # (cd to the root floodns folder)
   java -jar floodns-basic-sim.jar ./examples/leaf_spine_k16
   ```
   Also, you can use the Makefile to run the simulation:

   ```
    # (cd to the root floodns folder)
   make run-basic-sim FOLDER=./examples/leaf_spine_k16
   ```

3. Now you can find log files as output:

   ```
   # (cd to the root floodns folder)
   cd examples/leaf_spine_k16/logs_floodns
   ls
   ```

4. You can also make the connection log a bit more human-readable for convenience:

   ```
   # (cd to the root floodns folder)
   python -m external.convert_connection_info_to_human_readable basic_sim ./examples/leaf_spine_k16/logs_floodns
   ```

    5. Now `examples/leaf_spine_k16/logs_floodns/connection_info.log.txt` will have similar content:

       ```
       Conn. ID   Source   Target   Size           Sent           Flows' IDs     Start time (ns)    End time (ns)      Duration         Progress     Avg. rate        Finished?     Metadata
       0          X        y        A Gbit         B Gbit         0              0                  T                  t s              PP.PP%       RR.RR Gbit/s     YES 
       ... 
       ```

## Run folder

The run folder must contain the input of a simulation.

**config.properties**

General properties of the simulation. The following must be defined:

* `simulation_end_time_ns` : How long to run the simulation in simulation time (ns)
* `simulation_seed` : If there is randomness present in the simulation, this guarantees reproducibility (exactly the
  same outcome) if the seed is the same
* `filename_topology` : Topology filename (relative to run folder)
* `filename_schedule` : Schedule filename (relative to run folder)
* `job_base_dir_schedule` : Base directory for DNN training jobs (relative to run folder). If you don't use DNN training
  jobs, you can leave this with empty string.
* `routing_strategy` : Routing strategy to use.
* `link_failure_rate` : Link failure rate (0.0 means no link failures, 1.0 means all links fail)
* `num_failed_nodes` : Number of nodes which fail at the beginning of the simulation (0 means no node failures)

**connectionSchedule.csv**

Simple connection arrival connectionSchedule. Each line defines a connection (= typically, a routing strategy supplies 1
flow / connection, but it can be any number of its lifetime) as follows:

```
[connection_id],[from_node_id],[to_node_id],[size_byte],[start_time_ns],[additional_parameters],[metadata]
```

Notes: connection_id must increment each line. All values except additional_parameters and metadata are
mandatory. `additional_parameters` should be set if you want to configure something special for each
connection. `metadata` you can use for identification later on in the connection logs (e.g., to indicate the workload it
was part of). If you simulating DNN training jobs, you can leave this file empty.

**topology.properties**

The topological layout of the network. The following properties must be defined:

* `num_nodes` (type: positive integer)

  Number of nodes.

* `num_undirected_edges` (type: positive integer)

  Number of undirected edges (each undirected edge will be expressed into two links).

* `switches` (type: set of node identifiers or range of node identifiers)

  All node identifiers which are switches expressed as `set(a, b, c)`, e.g.: `set(5, 6)` means node 5 and 6 are
  switches. If you want to express a range, you can use `incl_range(a, b)`, e.g.: `incl_range(0, 3)` means nodes 0, 1, 2
  and 3 are switches.

* `switches_which_are_tors` (type: set of node identifiers or range of node identifiers)

  All node identifiers which are also ToRs expressed as `set(a, b, c)` (type: set of node identifiers). If you want to
  express a range, you can use `incl_range(a, b)`.

* `cores` (type: set of node identifiers or range of node identifiers)

  All node identifiers which are cores expressed as `set(a, b, c)`. If you want to express a range, you can
  use `incl_range(a, b)`.

* `servers` (type: set of node identifiers or range of node identifiers)

  All node identifiers which are servers expressed as `set(a, b, c)`. If you want to express a range, you can
  use `incl_range(a, b)`.

* `undirected_edges` (type: set of undirected edges or range of undirected edges)

  All undirected edges, expressed as `set(a-b, b-c)`, e.g.: `set(0-2, 2-3)` means two undirected edges, between 0 and 2,
  and between 2 and 3. If you want to express a range, you can use `incl_range(a:b-c:d, x:y-z)`,
  e.g.: `incl_range(0:31-32:47,48:63-0)`
  means each node in range [0,31] is connected to node in range [32,47] via undirected edge, and each node in
  range [48,63] is connected to node 0 via undirected edge.

* `link_data_rate_bit_per_ns` (type: double (global value) or mapping of directed edge (link) to double)

  One undirected edge is translated into two links. Data rate set for all links (bit/ns = Gbit/s) (expressed as a
  number `double`, e.g.: `4.5` means 4.5 Gbit/s if you want the same rate for all links, else you express it
  as `map(a->b: c, d->e: f)`, e.g.: `map(0->1: 10.0, 1->0: 8.4)` link 0->1 has 10.0 Gbit/s and link 1->0 has 8.4 Gbit/s
  capacity. If you choose to express as a map, you have to give it individually for every link.)

Please see the examples to understand each property. Besides it just defining a graph, the following rules apply:

* If there are servers defined, they can only have edges to a ToR.
* There is only a semantic difference between switches, switches which are ToRs and servers. If there are servers, only
  servers should be valid endpoints for applications. If there are no servers, ToRs should be valid endpoints instead.
