#!/bin/bash
# Quick Start Script for Building Packer Image Locally
# This script helps you build a GCP runner image using Packer
# trunk-ignore-all(shellcheck/SC2310): command_exists used in conditions is intentional
# trunk-ignore-all(shellcheck/SC2155): declare and assign pattern is acceptable here
# trunk-ignore-all(shellcheck/SC1003): backslash escaping in examples is intentional

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
	echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
	echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
	echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
	echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if a command exists
command_exists() {
	command -v "$1" >/dev/null 2>&1
}

# Main script
print_info "Starting Packer build script for GCP runner images"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists packer; then
	print_error "Packer is not installed. Please install it from: https://www.packer.io/downloads"
	exit 1
fi
print_success "Packer is installed ($(packer version))"

if ! command_exists gcloud; then
	print_error "Google Cloud SDK is not installed. Please install it from: https://cloud.google.com/sdk/docs/install"
	exit 1
fi
print_success "Google Cloud SDK is installed"

# Check GCP authentication
print_info "Checking GCP authentication..."
if gcloud auth application-default print-access-token >/dev/null 2>&1; then
	print_success "GCP authentication is configured"
else
	print_warning "GCP authentication not found. Running 'gcloud auth application-default login'..."
	gcloud auth application-default login
fi

# Get GCP project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [[ -z ${CURRENT_PROJECT} ]]; then
	print_error "No GCP project is configured. Please run: gcloud config set project YOUR_PROJECT_ID"
	exit 1
fi

echo ""
print_info "Current GCP project: ${CURRENT_PROJECT}"

# Prompt for confirmation or custom project
read -p "Use this project? (y/n/custom): " -r
if [[ ${REPLY} =~ ^[Nn]$ ]]; then
	exit 0
elif [[ ${REPLY} =~ ^[Cc]ustom$ ]]; then
	read -p "Enter GCP project ID: " -r CUSTOM_PROJECT
	GCP_PROJECT=${CUSTOM_PROJECT}
else
	GCP_PROJECT=${CURRENT_PROJECT}
fi

# Get zone
print_info "Current GCP zone: $(gcloud config get-value compute/zone 2>/dev/null || echo 'not set')"
read -p "Enter GCP zone (or press Enter for europe-west1-b): " -r
GCP_ZONE=${REPLY:-europe-west1-b}

# Choose Ubuntu version
echo ""
print_info "Available Ubuntu versions:"
echo "  1) Ubuntu 22.04 LTS (recommended)"
echo "  2) Ubuntu 24.04 LTS"
echo "  3) Custom version"
read -p "Select Ubuntu version (1/2/3): " -r VERSION_CHOICE

case ${VERSION_CHOICE} in
1)
	UBUNTU_VERSION="2204"
	print_success "Selected: Ubuntu 22.04 LTS"
	;;
2)
	UBUNTU_VERSION="2404"
	print_success "Selected: Ubuntu 24.04 LTS"
	;;
3)
	read -p "Enter Ubuntu version (e.g., 2204 for 22.04): " -r UBUNTU_VERSION
	print_success "Selected: Ubuntu ${UBUNTU_VERSION:0:2}.${UBUNTU_VERSION:2:2}"
	;;
*)
	UBUNTU_VERSION="2204"
	print_warning "Invalid choice, defaulting to Ubuntu 22.04 LTS"
	;;
esac

# Generate image name with timestamp
IMAGE_NAME="github-runner-base-ubuntu-${UBUNTU_VERSION}-$(date +%Y%m%d-%H%M%S)"
print_info "Generated image name: ${IMAGE_NAME}"

read -p "Use this image name? (y/n): " -r
if [[ ${REPLY} =~ ^[Nn]$ ]]; then
	read -p "Enter custom image name: " -r CUSTOM_IMAGE_NAME
	IMAGE_NAME=${CUSTOM_IMAGE_NAME}
fi

echo ""
print_info "Build Configuration:"
echo "  Project ID:     ${GCP_PROJECT}"
echo "  Zone:           ${GCP_ZONE}"
echo "  Ubuntu Version: ${UBUNTU_VERSION:0:2}.${UBUNTU_VERSION:2:2}"
echo "  Image Name:     ${IMAGE_NAME}"
echo "  Image Family:   github-runner-base-ubuntu-${UBUNTU_VERSION}"
echo ""

read -p "Proceed with build? (y/n): " -r
if [[ ! ${REPLY} =~ ^[Yy]$ ]]; then
	print_info "Build cancelled"
	exit 0
fi

echo ""
print_info "Initializing Packer..."
packer init template.pkr.hcl
print_success "Packer initialized"

echo ""
print_info "Validating Packer template..."
packer validate \
	-var="project_id=${GCP_PROJECT}" \
	-var="zone=${GCP_ZONE}" \
	-var="image_name=${IMAGE_NAME}" \
	-var="ubuntu_version=${UBUNTU_VERSION}" \
	template.pkr.hcl
print_success "Packer template is valid"

echo ""
print_info "Starting Packer build..."
print_warning "This will take approximately 10-15 minutes"
echo ""

# Set Packer log level
export PACKER_LOG=1
export PACKER_LOG_PATH="packer-build-$(date +%Y%m%d-%H%M%S).log"

# Run Packer build
if packer build \
	-var="project_id=${GCP_PROJECT}" \
	-var="zone=${GCP_ZONE}" \
	-var="image_name=${IMAGE_NAME}" \
	-var="ubuntu_version=${UBUNTU_VERSION}" \
	template.pkr.hcl; then

	echo ""
	print_success "Packer build completed successfully!"
	print_info "Image name: ${IMAGE_NAME}"
	print_info "Image family: github-runner-base"
	print_info "Logs saved to: ${PACKER_LOG_PATH}"

	echo ""
	print_info "Verifying image creation..."
	gcloud compute images describe "${IMAGE_NAME}" \
		--project="${GCP_PROJECT}" \
		--format="table(name,family,diskSizeGb,status,creationTimestamp)"

	echo ""
	print_success "Image verification complete!"

	echo ""
	print_info "Next steps:"
	echo "  1. Test the image by creating a VM:"
	echo '     gcloud compute instances create test-runner \'
	echo "       --image=${IMAGE_NAME} \\"
	echo "       --image-project=${GCP_PROJECT} \\"
	echo "       --zone=${GCP_ZONE} \\"
	echo "       --machine-type=n2-standard-4"
	echo ""
	echo "  2. Update your config.yaml:"
	echo "     instance_config:"
	echo "       image_family: github-runner-base"
	echo "       image_project: ${GCP_PROJECT}"
	echo ""
	echo "  3. See docs/development/prebuilt-images.md for detailed setup"

else
	echo ""
	print_error "Packer build failed!"
	print_info "Check logs at: ${PACKER_LOG_PATH}"
	exit 1
fi
