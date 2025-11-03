#!/bin/bash
# Rocky Linux provisioning script for GitHub Actions runner base image
# This script is called by Packer to configure the image

set -e

echo "=========================================="
echo "Rocky Linux Provisioning Starting"
echo "=========================================="

# Update system packages
echo "Step 1/4: Updating system packages..."
yum update -y

# Install base dependencies
echo "Step 2/4: Installing base dependencies..."
yum install -y bind-utils yum-utils

# Install Docker CE
echo "Step 3/4: Installing Docker CE..."
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y epel-release docker-ce docker-ce-cli containerd.io

# Configure Docker
systemctl enable docker
groupadd -f docker

# Clean up
echo "Step 4/4: Cleaning up..."
yum clean all
rm -rf /var/cache/yum
rm -rf /tmp/*
rm -f ~/.bash_history

echo "=========================================="
echo "Rocky Linux Provisioning Completed"
echo "=========================================="
