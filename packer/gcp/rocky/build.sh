#!/bin/bash
# Interactive script to build Rocky Linux 8 GitHub Runner base image with Packer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "   Rocky Linux 8 Runner Image Builder"
echo "=========================================="
echo

# Check prerequisites
echo "Checking prerequisites..."

# Check if packer is installed
if ! command -v packer &>/dev/null; then
	echo "❌ Error: Packer is not installed"
	echo "   Install from: https://www.packer.io/downloads"
	exit 1
fi
echo "✅ Packer found: $(packer version)"

# Check if gcloud is installed
if ! command -v gcloud &>/dev/null; then
	echo "❌ Error: gcloud CLI is not installed"
	echo "   Install from: https://cloud.google.com/sdk/docs/install"
	exit 1
fi
echo "✅ gcloud CLI found"

# Check gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
	echo "❌ Error: No active gcloud authentication"
	echo "   Run: gcloud auth login"
	exit 1
fi
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
# trunk-ignore-all(shellcheck)
echo "✅ Authenticated as: ${ACTIVE_ACCOUNT}"

echo
echo "Prerequisites check passed!"
echo

# Get configuration
read -p "Enter GCP Project ID [scality-prod-ga-runners]: " PROJECT_ID
PROJECT_ID=${PROJECT_ID:-scality-prod-ga-runners}

read -p "Enter GCP Zone [europe-west1-b]: " ZONE
ZONE=${ZONE:-europe-west1-b}

# Choose Rocky Linux version
echo
echo "Available Rocky Linux versions:"
echo "  1) Rocky Linux 8 (recommended)"
echo "  2) Rocky Linux 9"
echo "  3) Custom version"
read -p "Select Rocky Linux version (1/2/3): " VERSION_CHOICE

case ${VERSION_CHOICE} in
1)
	ROCKY_VERSION="8"
	echo "✅ Selected: Rocky Linux 8"
	;;
2)
	ROCKY_VERSION="9"
	echo "✅ Selected: Rocky Linux 9"
	;;
3)
	read -p "Enter Rocky Linux version (e.g., 8 or 9): " ROCKY_VERSION
	echo "✅ Selected: Rocky Linux ${ROCKY_VERSION}"
	;;
*)
	ROCKY_VERSION="8"
	echo "⚠️  Invalid choice, defaulting to Rocky Linux 8"
	;;
esac

read -p "Enter disk size in GB [80]: " DISK_SIZE
DISK_SIZE=${DISK_SIZE:-80}

# Generate image name with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_NAME="github-runner-base-rocky-${ROCKY_VERSION}-${TIMESTAMP}"

echo
echo "=========================================="
echo "Build Configuration:"
echo "=========================================="
echo "Project ID:    ${PROJECT_ID}"
echo "Zone:          ${ZONE}"
echo "Rocky Version: ${ROCKY_VERSION}"
echo "Disk Size:     ${DISK_SIZE}GB"
echo "Image Name:    ${IMAGE_NAME}"
echo "Image Family:  github-runner-base-rocky-${ROCKY_VERSION}"
echo "=========================================="
echo

read -p "Proceed with build? (yes/no): " CONFIRM
if [[ ${CONFIRM} != "yes" ]]; then
	echo "Build cancelled."
	exit 0
fi

echo
echo "Starting Packer build..."
echo "This will take approximately 10-15 minutes."
echo

# Initialize Packer
echo "Initializing Packer plugins..."
packer init template.pkr.hcl

# Validate template
echo "Validating Packer template..."
packer validate \
	-var="project_id=${PROJECT_ID}" \
	-var="zone=${ZONE}" \
	-var="image_name=${IMAGE_NAME}" \
	-var="rocky_version=${ROCKY_VERSION}" \
	-var="disk_size=${DISK_SIZE}" \
	template.pkr.hcl

# Build image
echo
echo "Building image (this will take several minutes)..."
packer build \
	-var="project_id=${PROJECT_ID}" \
	-var="zone=${ZONE}" \
	-var="image_name=${IMAGE_NAME}" \
	-var="rocky_version=${ROCKY_VERSION}" \
	-var="disk_size=${DISK_SIZE}" \
	template.pkr.hcl | tee "packer-build-rocky-${TIMESTAMP}.log"

echo
echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="
echo
echo "Image Details:"
echo "  Name:   ${IMAGE_NAME}"
echo "  Family: github-runner-base-rocky-${ROCKY_VERSION}"
echo
echo "To use this image in runner-manager, update your config.yaml:"
echo "  runner_groups:"
echo "    - name: rocky-${ROCKY_VERSION}-packer-gcloud"
echo "      cloud_provider: gcloud"
echo "      image_family: github-runner-base-rocky-${ROCKY_VERSION}"
echo "      image_project: ${PROJECT_ID}"
echo
echo "Build log saved to: packer-build-rocky-${TIMESTAMP}.log"
echo "Manifest saved to: manifest-rocky.json"
echo
