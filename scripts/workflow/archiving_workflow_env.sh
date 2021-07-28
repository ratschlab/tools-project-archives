# Adapt the following variables to your environment

export ARCHIVER_MAX_CPUS_ENV_VAR="LSB_MAX_NUM_PROCESSORS" 

# '--cluster' parameter for snakemake
SK_CLUSTER_CMD='bsub -J archiving_{rule} -W "{resources.hours}:00" -n {threads} -R "rusage[mem={resources.mem_mb}]" -R "span[hosts=1]" -o logs/{rule}_%J.out -e logs/{rule}_%J.err'

# aditional options or snakemake
SK_ADDITIONAL_OPTS="--envvars ARCHIVER_MAX_CPUS_ENV_VAR --latency-wait 20 --default-resources hours=120 "

# default work directory, if user doesn't set one
# Has to be on a distributed filesytem in case of a cluster submission
DEFAULT_WORKDIR="${HOME}/tmp/tmp_archiving"

