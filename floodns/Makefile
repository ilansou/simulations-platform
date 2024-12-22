CODE_DIRS=external

green_terminal_output=`tput setaf 2`
reset_terminal_output=`tput sgr0`

ring_sizes=2 4 8
num_concurrent_jobs=2 3 4 5
num_jobs=1 2 3 4 5
num_core_failures=0 1 4 8
algorithms=ecmp mcvlc edge_coloring simulated_annealing ilp_solver
centralized_controller_algorithms=mcvlc edge_coloring simulated_annealing ilp_solver
models=BLOOM GPT_3 LLAMA2_70B
seeds=0 42 200 404 1234

install-python-requirements:
	@echo "${green_terminal_output}Installing requirements...${reset_terminal_output}"
	poetry install
	@echo "${green_terminal_output}Finished installing requirements...${reset_terminal_output}"

compile-maven:
	@echo "${green_terminal_output}Compiling maven...${reset_terminal_output}"
	mvn clean compile assembly:single; mv target/floodns-*-jar-with-dependencies.jar floodns-basic-sim.jar
	@echo "${green_terminal_output}Finished compiling maven...${reset_terminal_output}"

format:
	poetry run black -l 100 ${CODE_DIRS}

lint:
	poetry run ruff ${CODE_DIRS} --fix
	poetry run mypy --install-types ${CODE_DIRS}
	poetry run black --check -l 100 ${CODE_DIRS}

run-basic-sim:
	java -jar floodns-basic-sim.jar $(FOLDER)


##########################
# Training jobs generation
##########################
generate-single-training-job:
	for seed in $(seeds); do \
  		for ring_size in $(ring_sizes); do \
  			for model in $(models); do \
  				echo "${green_terminal_output}Starting generation of training jobs for seed $$seed...${reset_terminal_output}"; \
  				poetry run python -m external.jobs_generator.main gen-single-job-ddp-pairs A100 $$model 64 $$ring_size $$seed; \
  				echo "${green_terminal_output}Finished generation of training jobs for seed $$seed...${reset_terminal_output}"; \
  			done \
  		done \
	done

generate-training-jobs-similar-dp-dim:
	for seed in $(seeds); do \
		for ring_size in $(ring_sizes); do \
		  	for num_jobs in $(num_concurrent_jobs); do \
				echo "${green_terminal_output}Starting generation of training jobs for seed $$seed...${reset_terminal_output}"; \
				poetry run python -m external.jobs_generator.main gen-ddp-pairs A100 64 $$num_jobs $$ring_size $$seed; \
				echo "${green_terminal_output}Finished generation of training jobs for seed $$seed...${reset_terminal_output}"; \
		  	done \
		done \
	done

generate-training-jobs-different-dp-dim:
	for seed in $(seeds); do \
		for ring_size in $(ring_sizes); do \
		  	for num_jobs in $(num_concurrent_jobs); do \
				echo "${green_terminal_output}Starting generation of training jobs for seed $$seed...${reset_terminal_output}"; \
				poetry run python -m external.jobs_generator.main gen-ddp-pairs-different-sizes A100 64 $$num_jobs $$seed; \
				echo "${green_terminal_output}Finished generation of training jobs for seed $$seed...${reset_terminal_output}"; \
		  	done \
		done \
	done

##########################
# Run directory generation
##########################
generate-run-directory-concurrent-jobs:
	for seed in $(seeds); do \
		for n_jobs in $(num_jobs); do \
			echo "${green_terminal_output}Starting generation of run directory for seed $$seed...${reset_terminal_output}"; \
			poetry run python -m external.runs_generator.main create-concurrent-jobs-dir 64 $$n_jobs $$seed; \
			echo "${green_terminal_output}Finished generation of run directory for seed $$seed...${reset_terminal_output}"; \
		done \
	done

generate-run-directory-different-ring-sizes:
	for seed in $(seeds); do \
		for n_jobs in $(num_jobs); do \
			echo "${green_terminal_output}Starting generation of run directory for seed $$seed...${reset_terminal_output}"; \
			poetry run python -m external.runs_generator.main create-concurrent-jobs-different-ring-sizes 64 $$n_jobs $$seed; \
			echo "${green_terminal_output}Finished generation of run directory for seed $$seed...${reset_terminal_output}"; \
		done \
	done

####################################
# Simulation of different algorithms
####################################
simulate-jobs:
	@$(foreach seed,$(seeds),\
		$(foreach job,$(num_jobs),\
			$(foreach core_failure,$(num_core_failures),\
				$(foreach ring_size,$(ring_sizes),\
					$(foreach alg,$(algorithms),\
						echo "Starting simulation of $(alg)..."; \
						java -jar floodns-basic-sim.jar ./runs/seed_$(seed)/concurrent_jobs_$(job)/$(core_failure)_core_failures/ring_size_$(ring_size)/$(alg); \
						echo "Finished simulation of $(alg)..."; \
					)\
				)\
			)\
		)\
	)

simulate-single-job:
	@$(foreach seed,$(seeds),\
		$(foreach ring_size,$(ring_sizes),\
			$(foreach core_failure,$(num_core_failures),\
				$(foreach alg,$(algorithms),\
					$(foreach model,$(models),\
						echo "Starting simulation of $(alg) with $(model)..."; \
						java -jar floodns-basic-sim.jar ./runs/seed_$(seed)/concurrent_jobs_1/$(core_failure)_core_failures/ring_size_$(ring_size)/$(model)/$(alg); \
						echo "Finished simulation of $(alg) with $(model)..."; \
					)\
				)\
			)\
		)\
	)

simulate-jobs-different-ring-sizes:
	@$(foreach seed,$(seeds),\
		$(foreach job,$(num_jobs),\
			$(foreach core_failure,$(num_core_failures),\
				$(foreach alg,$(algorithms),\
					echo "Starting simulation of $(alg)..."; \
					java -jar floodns-basic-sim.jar ./runs/seed_$(seed)/concurrent_jobs_$(job)/$(core_failure)_core_failures/different_ring_sizes/$(alg); \
					echo "Finished simulation of $(alg)..."; \
				)\
			)\
		)\
	)

simulate-jobs-single-alg:
	java -jar floodns-basic-sim.jar ./runs/seed_$(SEED)/concurrent_jobs_$(JOBS)/$(CORES)_core_failures/ring_size_$(RING)/$(MODEL)/$(ALG)

##################################
# Analysis of different algorithms
##################################
convert-human-readable-concurrent-jobs:
	echo "${green_terminal_output}Starting analysis of $$alg...${reset_terminal_output}"
	poetry run python -m external.analysis.convert_to_human_readable concurrent-jobs $(JOBS) $(SEED)
	echo "${green_terminal_output}Finished analysis of $$alg...${reset_terminal_output}"

convert-human-readable-different-ring-sizes:
	echo "${green_terminal_output}Starting analysis of $$alg...${reset_terminal_output}"
	poetry run python -m external.analysis.convert_to_human_readable different-ring-sizes $(JOBS) $(SEED)
	echo "${green_terminal_output}Finished analysis of $$alg...${reset_terminal_output}"

####################################
# Comparison of different algorithms
####################################
compare-routing-strategies-concurrent-jobs:
	echo "${green_terminal_output}Starting comparing various routing strategies...${reset_terminal_output}"
	poetry run python -m external.analysis.routing_strategy_comparison concurrent-jobs $(JOBS) $(SEED)
	echo "${green_terminal_output}Finished comparing various routing strategies...${reset_terminal_output}"

compare-routing-strategies-different-ring-sizes:
	echo "${green_terminal_output}Starting comparing various routing strategies...${reset_terminal_output}"
	poetry run python -m external.analysis.routing_strategy_comparison different-ring-sizes $(JOBS) $(SEED)
	echo "${green_terminal_output}Finished comparing various routing strategies...${reset_terminal_output}"

################
# CDF Generation
################
generate-controller-computation-cdf:
	for alg in $(centralized_controller_algorithms); do \
		poetry run python -m external.cdf_generation.controller_computation $$alg; \
	done

generate-cdfs:
	for alg in $(algorithms); do \
		poetry run python -m external.cdf_generation.data_parallelism_time $$alg; \
		poetry run python -m external.cdf_generation.fct_throughput $$alg; \
	done
