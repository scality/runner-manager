# Packer Template for GitHub Runner Base Image (Rocky Linux)
# This template creates a pre-built GCP VM image with common dependencies
# to accelerate GitHub Actions runner startup time.
# 
# Supports multiple Rocky Linux versions: 8, 9, etc.
# 
# Example usage:
#   Rocky 8: packer build -var="rocky_version=8" template.pkr.hcl
#   Rocky 9: packer build -var="rocky_version=9" template.pkr.hcl

# Variables for configuration
variable "project_id" {
  type        = string
  description = "GCP project ID where the image will be built and stored"
}

variable "zone" {
  type        = string
  description = "GCP zone for the build VM"
  default     = "europe-west1-b"
}

variable "rocky_version" {
  type        = string
  description = "Rocky Linux version (8, 9, etc.)"
  default     = "8"
}

variable "source_image_family" {
  type        = string
  description = "Base image family to build from (will be constructed from rocky_version if not set)"
  default     = ""
}

variable "source_image_project" {
  type        = string
  description = "GCP project containing the source image"
  default     = "rocky-linux-cloud"
}

variable "image_name" {
  type        = string
  description = "Name for the output image (will be auto-generated if not set)"
  default     = ""
}

variable "image_family" {
  type        = string
  description = "Image family for the output image (will be constructed from rocky_version if not set)"
  default     = ""
}

# Local variables for dynamic naming
locals {
  # Construct source image family from version if not explicitly set
  actual_source_image_family = var.source_image_family != "" ? var.source_image_family : "rocky-linux-${var.rocky_version}"
  
  # Construct image family from version if not explicitly set
  actual_image_family = var.image_family != "" ? var.image_family : "github-runner-base-rocky-${var.rocky_version}"
  
  # Construct image name with timestamp if not explicitly set
  actual_image_name = var.image_name != "" ? var.image_name : "github-runner-base-rocky-${var.rocky_version}-${formatdate("YYYYMMDD-hhmmss", timestamp())}"
}

variable "machine_type" {
  type        = string
  description = "Machine type for the build VM"
  default     = "e2-standard-2"
}

variable "disk_size" {
  type        = number
  description = "Disk size in GB for the image"
  default     = 80
}

variable "disk_type" {
  type        = string
  description = "Disk type for the build VM"
  default     = "pd-ssd"
}

variable "network" {
  type        = string
  description = "Network to use for the build VM"
  default     = "default"
}

variable "subnetwork" {
  type        = string
  description = "Subnetwork to use for the build VM"
  default     = ""
}

variable "tags" {
  type        = list(string)
  description = "Network tags for the build VM"
  default     = ["packer-build"]
}

variable "image_labels" {
  type        = map(string)
  description = "Labels to apply to the output image"
  default = {
    created_by = "packer"
    purpose    = "github-actions-runner"
    os         = "rocky-linux-8"
  }
}

# Packer configuration
packer {
  required_version = ">= 1.9.0"
  required_plugins {
    googlecompute = {
      version = ">= 1.1.1"
      source  = "github.com/hashicorp/googlecompute"
    }
  }
}

# Source configuration
source "googlecompute" "runner-base-rocky" {
  project_id          = var.project_id
  source_image_family = local.actual_source_image_family
  source_image_project_id = [var.source_image_project]
  zone                = var.zone
  
  # Output image configuration
  image_name          = local.actual_image_name
  image_family        = local.actual_image_family
  image_description   = "Pre-built GitHub Actions runner base image (Rocky Linux ${var.rocky_version}) with common dependencies"
  image_labels        = merge(var.image_labels, {
    os_version = var.rocky_version
  })
  
  # Build VM configuration
  machine_type        = var.machine_type
  disk_size           = var.disk_size
  disk_type           = var.disk_type
  network             = var.network
  subnetwork          = var.subnetwork
  tags                = var.tags
  
  # SSH configuration
  ssh_username        = "packer"
  
  # Use internal IP if on a private network
  use_internal_ip     = false
  
  # Don't create a default service account
  omit_external_ip    = false
}

# Build configuration
build {
  name = "github-runner-base-rocky"
  
  sources = ["source.googlecompute.runner-base-rocky"]
  
  # Wait for cloud-init to complete
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "cloud-init status --wait || true",
      "echo 'Cloud-init completed'"
    ]
  }
  
  # Update system packages
  provisioner "shell" {
    inline = [
      "echo 'Updating system packages...'",
      "sudo yum update -y",
      "echo 'System update completed'"
    ]
  }
  
  # Install base dependencies (from startup.sh init() function)
  provisioner "shell" {
    inline = [
      "echo 'Installing base dependencies...'",
      "sudo yum install -y bind-utils yum-utils",
      "echo 'Base dependencies installed'"
    ]
  }
  
  # Install Docker CE (from startup.sh install_docker() function for Rocky Linux)
  provisioner "shell" {
    inline = [
      "echo 'Installing Docker CE...'",
      "sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo",
      "sudo yum install -y epel-release docker-ce docker-ce-cli containerd.io",
      "echo 'Docker CE installed'"
    ]
  }
  
  # Configure Docker
  provisioner "shell" {
    inline = [
      "echo 'Configuring Docker...'",
      "sudo systemctl enable docker",
      "sudo groupadd -f docker",
      "echo 'Docker configured (will start on first boot)'"
    ]
  }
  
  # Clean up
  provisioner "shell" {
    inline = [
      "echo 'Cleaning up...'",
      "sudo yum clean all",
      "sudo rm -rf /var/cache/yum",
      "sudo rm -rf /tmp/*",
      "sudo rm -f ~/.bash_history",
      "echo 'Cleanup completed'"
    ]
  }
  
  # Post-processor: print image information
  post-processor "manifest" {
    output = "manifest-rocky.json"
    strip_path = true
  }
}
