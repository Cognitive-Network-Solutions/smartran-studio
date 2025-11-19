#!/bin/bash
set -xe  # Debug mode, exit on error

# Update system packages
sudo apt-get update -y

#############
# Install Git 
#############
sudo apt-get install -y git


# Verify installations
git --version

################
# Install Docker 
################
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common 

# Add Docker’s GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg


# Add Docker's repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bullseye stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Install NVIDIA Comtainer Runtime

# Set up the package repository
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Add the GPG key
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
sudo apt-get update

# Install, set runtime, and restart docker
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker


# Install starship for shell
curl -sS https://starship.rs/install.sh | sh

# Add Starship initialization to bashrc if not already present
if ! grep -q 'eval "$(starship init bash)"' ~/.bashrc; then
    echo 'eval "$(starship init bash)"' >> ~/.bashrc
fi

# Verify installations
git --version
docker --version
docker compose version  # Check Docker Compose
sudo ls -l /root/.config/gcloud/application_default_credentials.json 