# Rocky Linux Packer Template

This directory contains the Packer template and scripts to build optimized Rocky Linux 8 base images for GitHub Actions self-hosted runners on GCP.

## 📊 Performance

- **Standard spawn time:** 4min37s (277s)
- **With Packer image:** 2min21s (141s)
- **Improvement:** 49% faster ⚡
- **Time saved per instance:** 136 seconds (2min16s)

## 📦 What's Pre-installed

- Docker CE + containerd.io
- EPEL repository (Extra Packages for Enterprise Linux)
- System updates (yum update)
- Base development tools (bind-utils, yum-utils)
- Docker service enabled
- Optimized for GitHub Actions runner deployment

## 🚀 Quick Start

### Build Locally

```bash
./build.sh
```

The script will interactively prompt you for:

- GCP Project ID
- GCP Zone
- Disk size (default: 80 GB)
- Image name (auto-generated with timestamp)

### Manual Build

```bash
# Initialize Packer
packer init template.pkr.hcl

# Validate
packer validate \
  -var="project_id=YOUR_PROJECT" \
  -var="zone=europe-west1-b" \
  -var="disk_size=80" \
  -var="image_name=github-runner-base-rocky-8-$(date +%Y%m%d-%H%M%S)" \
  template.pkr.hcl

# Build
packer build \
  -var="project_id=YOUR_PROJECT" \
  -var="zone=europe-west1-b" \
  -var="disk_size=80" \
  -var="image_name=github-runner-base-rocky-8-$(date +%Y%m%d-%H%M%S)" \
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
    "sudo yum install -y your-package",
  ]
}
```

## 💡 Why EPEL?

EPEL (Extra Packages for Enterprise Linux) provides most GitHub Actions runner dependencies:

- `lttng-ust`
- `openssl-libs`
- `krb5-libs`
- `zlib`
- `libicu`

By pre-installing EPEL in the Packer image, the runner's `installdependencies.sh` script finds these packages already available, significantly reducing startup time.

## 📝 Notes

- Build machine: e2-standard-2 (2 vCPU, 8 GB RAM)
- Build time: ~10-15 minutes
- Disk size: 80 GB SSD
- Image family: `github-runner-base-rocky-8`
- Source image: `rocky-linux-8` from `rocky-linux-cloud`

## ⚠️ Important

Rocky Linux 8 runners show the **best performance improvement** (49% vs 35% for Ubuntu) because:

1. Standard Rocky VMs take much longer to provision (4min37s vs 2min09s)
2. EPEL installation eliminates most dependency installation time
3. Docker pre-installation is more impactful on Rocky

## 🔗 See Also

- [Main Packer README](../README.md)
- [Runner Manager Documentation](../../README.md)
- [Rocky Linux Documentation](https://docs.rockylinux.org/)
- [Packer GCP Builder Documentation](https://developer.hashicorp.com/packer/integrations/hashicorp/googlecompute)
