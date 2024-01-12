FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Docker
RUN sudo apt-get install -y docker.io

# Install AWS CLI
RUN curl "https://d1vvhvl2y92vvt.cloudfront.net/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    sudo ./aws/install
