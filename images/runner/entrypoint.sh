#!/bin/sh

echo "Starting runner..."
echo "RUNNER_ORG: ${RUNNER_ORG}"
echo "RUNNER_TOKEN: ${RUNNER_TOKEN}"
echo "RUNNER_NAME: ${RUNNER_NAME}"
echo "RUNNER_LABELS: ${RUNNER_LABELS}"
echo "RUNNER_GROUP: ${RUNNER_GROUP}"


./config.sh --url https://github.com/${RUNNER_ORG} \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --runnergroup "${RUNNER_GROUP}" \
    --work _work \
    --replace \
    --unattended \
    --ephemeral

./run.sh
