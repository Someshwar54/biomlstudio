FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-22.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git ca-certificates python3 python3-venv python3-pip \
    nodejs npm jq sudo unzip apt-transport-https gnupg2 lsb-release

# Install docker CLI inside the container (talks to host Docker)
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list \
 && apt-get update && apt-get install -y docker-ce-cli

# Install debugpy and minimal Python tooling
RUN python3 -m pip install --upgrade pip && pip3 install debugpy

# Node global tools (eslint)
RUN npm install -g eslint

# Create non-root user similar to devcontainers defaults
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
 && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
 && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME

WORKDIR /workspace
USER $USERNAME
