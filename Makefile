.PHONY: build up down logs test clean

# Build all containers
build:
	docker-compose build

# Start the system
up:
	docker-compose up -d

# Stop the system
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Run tests
test:
	docker-compose run orchestrator pytest

# Clean up
clean:
	docker-compose down -v
	rm -rf cache/*
	find . -type d -name __pycache__ -exec rm -r {} +

# Initialize Jetson Nano
init-jetson:
	@echo "Initializing Jetson Nano..."
	sudo nvpmodel -m 0
	sudo jetson_clocks
	sudo sysctl -w vm.swappiness=10

# Start development environment
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up 