#!/bin/bash
# SLURM batch script for a CASTEP job.
# Edit job name, resources, module version, and the seedname on the last line.
# Right-size --time: short jobs backfill into the schedule far sooner than long ones.

#SBATCH -J castep_job
#SBATCH -p multicore          # partition name (cluster-specific)
#SBATCH -n 32                 # MPI tasks
#SBATCH --mem=120G            # match to the job; check a similar run's peak first
#SBATCH -t 1-00:00:00         # walltime D-HH:MM:SS; keep it realistic
#SBATCH -o slurm-%j.out
#SBATCH -e slurm-%j.err

cd "$SLURM_SUBMIT_DIR"

module purge
module load apps/gcc/castep/25.1.1   # set to the version available on your cluster

# Seedname must match <seed>.cell / <seed>.param and have NO extension here.
mpirun -np $SLURM_NTASKS castep.mpi myseed
