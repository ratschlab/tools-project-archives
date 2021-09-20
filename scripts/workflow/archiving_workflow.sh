#!/usr/bin/env bash

usage()
{
    echo ""
    echo "Running archiving workflow (create filelist, create tar and create compressed-tar) on a cluster or locally"
    echo "Usage: $0 [-h] [-l] [-m MIN_WORKERS] [-n MAX_WORKERS [-p PART_SIZE] [-w WORKDIR] DIR_TO_BE_ARCHIVED DEST_DIR"
    echo "  -h  Help. Display this message and quit."
    echo "  -k  Adding path to gpg public key file, if archives should be encrypted. Several keys can be given separated by a comma"
    echo "  -l  Run locally on current host instead of submitting to cluster"
    echo "  -m  minimum number of workers, typically set for IO bound tasks"
    echo "  -n  maximum number of workers, typically set for CPU bound tasks like compression"
    echo "  -p  size of an archive part, see archiver archive --help"
    echo "  -w  working directory"
    echo ""
}

WORKDIR=""
ENCRYPTION_KEYS=""

while getopts 'hk:lm:n:p:w:' opt; do
    case $opt in
        (h)
            usage
            exit 0
            ;;
        (k)   ENCRYPTION_KEYS=$OPTARG;;
        (l)   RUN_LOCALLY=1;;
        (m)   MIN_WORKERS=$OPTARG;;
        (n)   MAX_WORKERS=$OPTARG;;
        (p)   PART_SIZE=$OPTARG;;
        (w)   WORKDIR="${OPTARG}";;
        (*)
            usage
            exit 1
            ;;
    esac
done

shift "$(($OPTIND -1))"

ARGS="$@"

if [ "$#" -lt 2 ]; then
    echo "need source and destination arguments!"
    usage
    exit 1
fi

if [ -z ${MIN_WORKERS} ]; then
    echo "WARNING: -m no set. Using 1 for minimum number of workers"
    MIN_WORKERS=1
fi

if [ -z ${MAX_WORKERS} ]; then
    echo "WARNING: -n no set. Using 1 for maximum number of workers"
    MAX_WORKERS=1
fi


SRC_DIR=$1
ARCHIVE_DIR=$2
shift 2

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SNAKEFILE=${SCRIPT_DIR}/Snakefile

source ${SCRIPT_DIR}/archiving_workflow_env.sh

NR_JOBS=1 # value for --jobs parameter of snakemake
if [ ${RUN_LOCALLY} ]; then
    SK_CLUSTER_CMD=""
    NR_JOBS=${MAX_WORKERS} # in local execution --jobs is an alias for --cores
fi


if [ -z "${WORKDIR}" ]; then
    if [ ! -z "${DEFAULT_WORKDIR}" ]; then
        WORKDIR="${DEFAULT_WORKDIR}"
    else
        WORKDIR="/tmp"
    fi
fi

WORKDIR_OPT="wdir_root=$(realpath ${WORKDIR})"

PART_SIZE_OPT=""
if [ ! -z ${PART_SIZE} ]; then
    PART_SIZE_OPT="part_size=${PART_SIZE}"
fi

ENCRYPTION_KEYS_OPT=""
if [ ! -z ${ENCRYPTION_KEYS} ]; then
    ENCRYPTION_KEYS_OPT="encryption_keys=${ENCRYPTION_KEYS}"
fi

snakemake --directory $(realpath ${WORKDIR})/snakemake_dir_${USER} \
          --snakefile ${SCRIPT_DIR}/Snakefile \
          --cluster "${SK_CLUSTER_CMD}" \
          --config src_dir=$(realpath ${SRC_DIR}) \
          archive_dir=$(realpath ${ARCHIVE_DIR}) \
          ${WORKDIR_OPT} ${ENCRYPTION_KEYS_OPT} ${PART_SIZE_OPT} \
          min_workers=${MIN_WORKERS} \
          max_workers=${MAX_WORKERS} \
          --jobs ${NR_JOBS} \
          --keep-going --printshellcmds \
          ${SK_ADDITIONAL_OPTS} $@


