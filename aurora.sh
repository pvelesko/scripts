#!/bin/bash

# Check if a job script is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <job_script>"
  exit 1
fi

JOB_SCRIPT="$1"
EMAIL_ADDRESS=pvelesko@gmail.com
REMOTE_HOST="aurora"
REMOTE_DIR="~/jobs"

# Ensure the job script exists
if [ ! -f "$JOB_SCRIPT" ]; then
  echo "Error: Job script '$JOB_SCRIPT' not found."
  exit 1
fi

# Get the base name of the job script
JOB_SCRIPT_NAME=$(basename "$JOB_SCRIPT")

# Construct the remote command
# 1. Create directory
# 2. Write script content from stdin to file
# 3. Submit job
REMOTE_CMD="mkdir -p $REMOTE_DIR && cat > $REMOTE_DIR/$JOB_SCRIPT_NAME && cd $REMOTE_DIR && /opt/pbs/bin/qsub -m e"

# Add email address if provided
if [ -n "$EMAIL_ADDRESS" ]; then
  REMOTE_CMD="$REMOTE_CMD -M $EMAIL_ADDRESS"
fi

# Add resource requests (preserved from user edits)
# select=1 -l walltime=04:00:00 -A chipStar_test  -q prod -l filesystems=flare
REMOTE_CMD="$REMOTE_CMD -l select=1 -l walltime=01:00:00 -A chipStar_test -q debug -l filesystems=flare"

# Append the job script name
REMOTE_CMD="$REMOTE_CMD $JOB_SCRIPT_NAME"

echo "Transferring and submitting '$JOB_SCRIPT_NAME' to '$REMOTE_HOST' in a single connection..."

# Execute via SSH, piping the local script to the remote 'cat'
cat "$JOB_SCRIPT" | ssh "$REMOTE_HOST" "$REMOTE_CMD"

if [ $? -eq 0 ]; then
  echo "Job submitted successfully."
else
  echo "Error: Failed to submit job."
  exit 1
fi
