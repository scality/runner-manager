# Packer Templates for GitHub Actions Runner Images

This directory contains Packer templates to build optimized base images for GitHub Actions self-hosted runners on GCP.

## 📁 Structure

```text
packer/gcp/
├── ubuntu/          # Ubuntu LTS templates and scripts
│   ├── template.pkr.hcl              # Packer template
│   ├── build.sh                      # Interactive build script
│   ├── provision.sh                  # Provisioning script
│   ├── variables.pkrvars.hcl.example # Variables example
│   └── config-example.yaml           # Runner-manager config example
│
├── rocky/           # Rocky Linux templates and scripts
│   ├── template.pkr.hcl              # Packer template
│   ├── build.sh                      # Interactive build script
│   ├── provision.sh                  # Provisioning script
│   ├── variables.pkrvars.hcl.example # Variables example
│   └── config-example.yaml           # Runner-manager config example
│
└── README.md        # This file
```

## 🚀 Quick Start

### Ubuntu

```bash
cd packer/gcp/ubuntu
./build.sh
```

### Rocky Linux

```bash
cd packer/gcp/rocky
./build.sh
```

## 📊 Performance Improvements

### Ubuntu 22.04

- **Standard spawn time:** 2min09s (129s)
- **With Packer image:** 1min24s (84s)
- **Improvement:** 35% faster ⚡

### Rocky Linux 8

- **Standard spawn time:** 4min37s (277s)
- **With Packer image:** 2min21s (141s)
- **Improvement:** 49% faster ⚡

### Combined Impact (222 instances/day)

- **Time saved per day:** 3h45min
- **Cost saved per month:** ~6,204€ (at 75€/h developer cost)
- **ROI:** 8,163× (Packer costs only 0.76€/month)

## 📦 What's Pre-installed

### Ubuntu Image

- Docker CE + docker-compose
- System updates and base packages
- Optimized for fast GitHub Actions runner deployment

### Rocky Image

- Docker CE + containerd
- EPEL repository (provides most runner dependencies)
- System updates and base packages
- Optimized for fast GitHub Actions runner deployment

## 🔧 Configuration

Each OS directory contains:

1. **template.pkr.hcl** - The Packer template
2. **build.sh** - Interactive build script with prompts
3. **provision.sh** - Shell provisioning script
4. **variables.pkrvars.hcl.example** - Example variables file
5. **config-example.yaml** - Runner-manager configuration example

## 📖 Usage

### Build an Image

```bash
cd packer/gcp/<ubuntu|rocky>
./build.sh
```

The script will prompt you for:

- GCP Project ID
- Image name (auto-generated with timestamp)
- Confirmation before building

## 🛠️ Manual Build

```bash
cd packer/gcp/<ubuntu|rocky>

# Validate template
packer validate \
  -var="project_id=YOUR_PROJECT" \
  -var="image_name=test-image" \
  template.pkr.hcl

# Build
packer build \
  -var="project_id=YOUR_PROJECT" \
  -var="image_name=github-runner-base-ubuntu-2204-$(date +%Y%m%d-%H%M%S)" \
  template.pkr.hcl
```

## 📝 Notes

- Images are built on GCP Compute Engine (e2-standard-2 for Ubuntu, e2-standard-2 for Rocky)
- Build time: ~8-15 minutes per image
- Images include security updates and are optimized for fast runner startup
- The `image_family` feature allows automatic use of the latest image version

## 🔗 Related Documentation

- [Packer Documentation](https://www.packer.io/docs)
- [GCP Compute Engine Images](https://cloud.google.com/compute/docs/images)
- [Runner Manager Configuration](../README.md)

## 💡 Tips

1. **Use image families** instead of specific image names for automatic updates
2. **Tag images** with meaningful names including dates
3. **Test new images** on a small runner group before full deployment
4. **Monitor startup times** in GCP Cloud Logging to validate improvements
5. **Rebuild regularly** (weekly recommended) to include security updates
