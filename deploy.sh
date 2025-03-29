#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}AutoCoder Deployment Script${NC}"

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        return 1
    fi
}

# Function to initialize Jetson Nano
initialize_jetson() {
    echo -e "${BLUE}Initializing Jetson Nano...${NC}"
    
    # Create required directories
    mkdir -p models cache
    
    # Set optimal performance settings
    sudo nvpmodel -m 0
    sudo jetson_clocks
    sudo sysctl -w vm.swappiness=10
    
    # Install system dependencies if not present
    echo -e "${BLUE}Installing system dependencies...${NC}"
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        libopenblas-dev \
        docker.io \
        nvidia-docker2 \
        curl

    # Install Docker Compose v2
    echo -e "${BLUE}Installing Docker Compose...${NC}"
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p $DOCKER_CONFIG/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-aarch64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

    # Pull Nvidia L4T ML container
    echo -e "${BLUE}Pulling Nvidia L4T ML container...${NC}"
    docker pull nvcr.io/nvidia/l4t-ml:r35.2.1-py3

    # Install Python packages
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
}

# Function to check Docker installation
setup_docker() {
    echo -e "${BLUE}Setting up Docker...${NC}"
    
    # Start Docker service if not running
    if ! systemctl is-active --quiet docker; then
        sudo systemctl start docker
    fi
    
    # Add current user to docker group
    if ! groups | grep -q docker; then
        sudo usermod -aG docker $USER
        echo -e "${GREEN}Added user to docker group. Please log out and back in for changes to take effect.${NC}"
    fi
}

# Main deployment logic
main() {
    # Check for docker first, as it's needed everywhere
    check_command docker || exit 1

    # Check if we're on Jetson Nano
    if [ -f /etc/nv_tegra_release ]; then
        echo -e "${GREEN}Detected Jetson Nano platform${NC}"
        
        # Initialize Jetson specific settings (includes docker-compose install)
        initialize_jetson
        
        # Setup Docker
        setup_docker
        
        # NOW check for docker-compose after attempting installation
        check_command docker-compose || exit 1
        
        echo -e "${GREEN}Starting LLM Server on Jetson Nano...${NC}"
        # Build and start LLM server
        docker-compose build llm-server
        docker-compose up -d llm-server
        
        echo -e "${GREEN}LLM Server started on port 8080${NC}"
        
    else
        echo -e "${GREEN}Deploying Orchestrator and Frontend on Main PC...${NC}"
        
        # Check for docker-compose on Main PC
        check_command docker-compose || exit 1
        
        # Create necessary directories
        mkdir -p models cache projects
        
        # Build and start orchestrator and frontend
        docker-compose build orchestrator frontend
        docker-compose up -d orchestrator frontend
        
        echo -e "${GREEN}Services started:${NC}"
        echo "- Orchestrator on port 8000"
        echo "- Frontend on port 3000"
    fi
}

# Check if script is run with sudo (only needed for first run)
if [ "$EUID" -ne 0 ] && [ ! -f "/.dockerenv" ]; then
    echo -e "${RED}Please run with sudo for first-time setup${NC}"
    exit 1
fi

# Run main deployment
main

echo -e "${GREEN}Deployment completed!${NC}" 