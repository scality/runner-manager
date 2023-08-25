#!/bin/sh

echo "Starting runner..."
echo "RUNNER_ORG: ${RUNNER_ORG}"
echo "RUNNER_JIT_CONFIG: ${RUNNER_JIT_CONFIG}"
echo "RUNNER_NAME: ${RUNNER_NAME}"
echo "RUNNER_LABELS: ${RUNNER_LABELS}"
echo "RUNNER_GROUP: ${RUNNER_GROUP}"

./run.sh --jitconfig "${RUNNER_JIT_CONFIG}"
