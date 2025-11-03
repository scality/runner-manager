# Packer Template for GitHub Runner Base Image (Ubuntu)
# This template creates a pre-built GCP VM image with common dependencies
# to accelerate GitHub Actions runner startup time.
# 
# Supports multiple Ubuntu versions: 22.04, 24.04, etc.
# 
# Example usage:
#   Ubuntu 22.04: packer build -var="ubuntu_version=2204" template.pkr.hcl
#   Ubuntu 24.04: packer build -var="ubuntu_version=2404" template.pkr.hcl

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

variable "ubuntu_version" {
  type        = string
  description = "Ubuntu version (2204 for 22.04, 2404 for 24.04, etc.)"
  default     = "2204"
}

variable "source_image_family" {
  type        = string
  description = "Base image family to build from (will be constructed from ubuntu_version if not set)"
  default     = ""
}

variable "source_image_project" {
  type        = string
  description = "GCP project containing the source image"
  default     = "ubuntu-os-cloud"
}

variable "image_name" {
  type        = string
  description = "Name for the output image (will be auto-generated if not set)"
  default     = ""
}

variable "image_family" {
  type        = string
  description = "Image family for the output image (will be constructed from ubuntu_version if not set)"
  default     = ""
}

# Local variables for dynamic naming
locals {
  # Construct source image family from version if not explicitly set
  actual_source_image_family = var.source_image_family != "" ? var.source_image_family : "ubuntu-${var.ubuntu_version}-lts"
  
  # Construct image family from version if not explicitly set
  actual_image_family = var.image_family != "" ? var.image_family : "github-runner-base-ubuntu-${var.ubuntu_version}"
  
  # Construct image name with timestamp if not explicitly set
  actual_image_name = var.image_name != "" ? var.image_name : "github-runner-base-ubuntu-${var.ubuntu_version}-${formatdate("YYYYMMDD-hhmmss", timestamp())}"
  
  # Formatted version for display (2204 -> 22.04)
  version_display = "${substr(var.ubuntu_version, 0, 2)}.${substr(var.ubuntu_version, 2, 2)}"
}

variable "machine_type" {
  type        = string
  description = "Machine type for the build VM"
  default     = "n2-standard-2"
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
source "googlecompute" "runner-base" {
  project_id          = var.project_id
  source_image_family = local.actual_source_image_family
  source_image_project_id = [var.source_image_project]
  zone                = var.zone
  
  # Output image configuration
  image_name          = local.actual_image_name
  image_family        = local.actual_image_family
  image_description   = "Pre-built GitHub Actions runner base image (Ubuntu ${local.version_display}) with common dependencies"
  image_labels        = merge(var.image_labels, {
    os_version = var.ubuntu_version
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
  name = "github-runner-base"
  
  sources = ["source.googlecompute.runner-base"]
  
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
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
      "echo 'System update completed'"
    ]
  }
  
  # Install base dependencies - EXACTLY matching startup.sh init() function
  provisioner "shell" {
    inline = [
      "echo 'Installing base dependencies (matching startup.sh init function)...'",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \\",
      "  apt-transport-https \\",
      "  ca-certificates \\",
      "  curl \\",
      "  gnupg \\",
      "  lsb-release",
      "echo 'Base dependencies installed'"
    ]
  }
  
  # Install Docker - EXACTLY matching startup.sh install_docker() function
  provisioner "shell" {
    inline = [
      "echo 'Installing Docker (matching startup.sh install_docker function)...'",
      "sudo install -m 0755 -d /etc/apt/keyrings",
      "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
      "sudo chmod a+r /etc/apt/keyrings/docker.gpg",
      "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
      "sudo apt-get update --yes",
      "sudo apt-get install --yes docker-ce docker-ce-cli containerd.io",
      "echo 'Docker installed successfully'"
    ]
  }
  
  # Configure Docker to start on boot
  provisioner "shell" {
    inline = [
      "echo 'Configuring Docker service...'",
      "sudo systemctl enable docker",
      "sudo systemctl start docker",
      "# Verify Docker is running",
      "sudo docker version",
      "echo 'Docker service configured'"
    ]
  }
  
  # Pre-create docker group (startup.sh will add actions user to it)
  provisioner "shell" {
    inline = [
      "echo 'Pre-creating docker group...'",
      "sudo groupadd -f docker",
      "echo 'Docker group ready'"
    ]
  }
  
  # Clean up to reduce image size
  provisioner "shell" {
    inline = [
      "echo 'Cleaning up to reduce image size...'",
      "sudo apt-get autoremove -y",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*",
      "# Clear bash history (if exists)",
      "rm -f ~/.bash_history",
      "touch ~/.bash_history",
      "echo 'Cleanup completed'"
    ]
  }
  
  # Final system preparation
  provisioner "shell" {
    inline = [
      "echo 'Final system preparation...'",
      "sudo sync",
      "echo '========================================='",
      "echo 'Image build completed successfully!'",
      "echo '========================================='",
      "echo 'Pre-installed components:'",
      "echo '  - Ubuntu 22.04 LTS (updated)'",
      "echo '  - Docker CE with containerd'",
      "echo '  - Base dependencies (curl, gnupg, etc.)'",
      "echo ''",
      "echo 'To be installed at runtime by startup.sh:'",
      "echo '  - actions user and permissions'",
      "echo '  - GitHub Actions runner agent'",
      "echo '  - Runner hooks and configuration'",
      "echo '  - Runner service'",
      "echo '========================================='",
      "sudo docker --version",
      "df -h /"
    ]
  }
  
  # Optional: Post-processor to create a manifest file
  post-processor "manifest" {
    output = "packer-manifest.json"
    strip_path = true
    custom_data = {
      source_image_family = var.source_image_family
      build_time = timestamp()
    }
  }
}
