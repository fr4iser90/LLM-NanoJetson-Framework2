#!/bin/bash

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AutoCoder Deployment Script${NC}"

# Prüfe ob wir auf Jetson oder PC sind
if [ -f /etc/nv_tegra_release ]; then
    echo -e "${GREEN}Deploying LLM Server auf Jetson Nano...${NC}"
    
    # Nur LLM Server auf Jetson starten
    docker-compose -f docker-compose.yml up -d llm-server
    
    echo -e "${GREEN}LLM Server gestartet auf Port 8080${NC}"
else
    echo -e "${GREEN}Deploying Orchestrator und Frontend auf Main PC...${NC}"
    
    # Orchestrator und Frontend auf PC starten
    docker-compose -f docker-compose.yml up -d orchestrator frontend
    
    echo -e "${GREEN}Services gestartet:${NC}"
    echo "- Orchestrator auf Port 8000"
    echo "- Frontend auf Port 3000"
fi 