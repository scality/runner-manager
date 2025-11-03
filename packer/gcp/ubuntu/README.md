# Ubuntu LTS Packer Template

This directory contains the Packer template and scripts to build optimized Ubuntu 22.04 LTS base images for GitHub Actions self-hosted runners on GCP.

## 📊 Performance

- **Standard spawn time:** 2min09s (129s)
- **With Packer image:** 1min24s (84s)
- **Improvement:** 35% faster ⚡
- **Time saved per instance:** 45 seconds

## 📦 What's Pre-installed

- Docker CE + docker-compose
- containerd.io
- System updates (apt update + upgrade)
- Base development tools
- Optimized for GitHub Actions runner deployment

## 🚀 Quick Start

### Build Locally

```bash
./build.sh
```

The script will interactively prompt you for:

- GCP Project ID
- GCP Zone
- Image name (auto-generated with timestamp)

### Manual Build

```bash
# Initialize Packer
packer init template.pkr.hcl

# Validate
packer validate \
  -var="project_id=YOUR_PROJECT" \
  -var="zone=europe-west1-b" \
  -var="image_name=github-runner-base-ubuntu-2204-$(date +%Y%m%d-%H%M%S)" \
  template.pkr.hcl

# Build
packer build \
  -var="project_id=YOUR_PROJECT" \
  -var="zone=europe-west1-b" \
  -var="image_name=github-runner-base-ubuntu-2204-$(date +%Y%m%d-%H%M%S)" \
  template.pkr.hcl
```

## 📋 Files

- **template.pkr.hcl** - Packer template definition
- **build.sh** - Interactive build script
- **provision.sh** - Shell provisioning script (if used)
- **variables.pkrvars.hcl.example** - Example variables file
- **config-example.yaml** - Runner-manager configuration example

## 🛠️ Customization

To customize the image, edit:

1. **template.pkr.hcl** - Modify build configuration, machine type, disk size
2. **provisioners** - Add/remove provisioning steps

Example: Add additional packages

```hcl
provisioner "shell" {
  inline = [
    "sudo apt-get install -y your-package",
  ]
}
```

## 📝 Notes

- Build machine: n2-standard-4 (4 vCPU, 16 GB RAM)
- Build time: ~8-10 minutes
- Disk size: 80 GB SSD
- Image family: `github-runner-base-ubuntu-2204`
- Source image: `ubuntu-2204-lts` from `ubuntu-os-cloud`

## 🔗 See Also

- [Main Packer README](../README.md)
- [Runner Manager Documentation](../../README.md)
- [Packer GCP Builder Documentation](https://developer.hashicorp.com/packer/integrations/hashicorp/googlecompute)
