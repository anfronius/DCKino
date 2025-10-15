#!/bin/bash

# Set script to exit on any errors
set -e

# Base directory (location of this script)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI text colors, styles, and backgrounds
default="$(printf '\033[0m')"
BLUE="$(printf '\033[1;34m')"
GREEN="$(printf '\033[1;32m')"
YELLOW="$(printf '\033[1;33m')"
MAGENTA="$(printf '\033[1;35m')"
RED="$(printf '\033[1;31m')"
BOLD="$(printf '\033[1m')"
UNDERLINE="$(printf '\033[4m')"
BLINK="$(printf '\033[5m')"
GREEN_BG="$(printf '\033[42m')"
BLUE_BG="$(printf '\033[44m')"
MAGENTA_BG="$(printf '\033[45m')"

# Function to clean up old containers
cleanup_containers() {
    echo -e "${BLUE}Cleaning up old containers... ${default}"
    docker compose down --volumes
    echo -e "${GREEN}Containers cleaned up ${default}"
}

# Function to build containers
build_containers() {
    echo -e "${BLUE}Building containers... ${default}"
    docker compose build
    echo -e "${GREEN}Containers built successfully ${default}"
}

# Function to start backend services
start_backend() {
    echo -e "${BLUE}Starting backend services... ${default}"
    docker compose up -d backend
    echo -e "${GREEN}Backend services started ${default}"
}

# Function to run scraper
run_scraper() {
    echo -e "${BLUE}Running scraper container... ${default}"
    docker compose run --rm scraper python utils/run_spiders.py
    echo -e "${GREEN}Scraper completed ${default}"
}

# Function to process data in backend
process_data() {
    echo -e "${BLUE}Processing scraped data... ${default}"
    docker compose exec backend python utils/process_data.py
    echo -e "${GREEN}Data processing completed ${default}"
}

# Function to backup data in backend
backup_data() {
    echo -e "${BLUE}Backing up processed data... ${default}"
    docker compose exec backend python utils/backup_data.py
    echo -e "${GREEN}Data backup completed ${default}"
}

# Function to combine showings in backend
combine_showings() {
    echo -e "${BLUE}Combining showings for frontend... ${default}"
    docker compose exec backend python utils/combine_showings.py
    echo -e "${GREEN}Showings combined successfully ${default}"
}

# Function for frontend options
frontend_options() {
    cd "$BASE_DIR/frontend"
    echo -e "\n\n${BLUE_BG}What would you like to do with the frontend?${default}\n"
    echo -e "${MAGENTA}  1. Build and run with Docker ${default}"
    echo -e "${MAGENTA}  2. Build frontend container only ${default}"
    echo -e "${MAGENTA}  3. Run local dev server (npm run dev) ${default}"
    echo -e "${MAGENTA}  4. Nothing ${default}\n"
    read -p "${BLUE}${BLINK}Enter your choice (1-4):${default} " choice
    case $choice in
        1)
            echo -e "\n\n${BLUE}Starting frontend container...${YELLOW}"
            cd "$BASE_DIR"
            docker compose up -d frontend
            echo -e "${GREEN}Frontend is running at http://localhost:80 ${default}"
            ;;
        2)
            echo -e "\n\n${BLUE}Building frontend container...${YELLOW}"
            cd "$BASE_DIR"
            docker compose build frontend
            echo -e "${GREEN}Frontend container built successfully ${default}"
        ;;
        3)
            echo -e "\n\n${BLUE}Starting local dev server... This will block the terminal. Press Ctrl+C to exit.${YELLOW}"
            npm run dev
            echo -e "${default}"
            ;;
        4)
            echo -e "\n\n${GREEN}No action taken.${default}"
            ;;
        *)
            echo -e "\n\n${RED}Invalid choice. No action taken.${default}"
            ;;
    esac
}

echo -e "\n\n${MAGENTA_BG}${BOLD}${UNDERLINE} ///// DCKino Docker Pipeline ///// ${default}\n\n"

# Clean up any existing containers
cleanup_containers

# Build all containers
build_containers

# Start backend services
start_backend

# Wait for backend to be ready
echo -e "${BLUE}Waiting for backend to be ready... ${default}"
sleep 10

# Run scraper (writes raw data to shared volume)
run_scraper

# Process data (reads raw data, outputs processed data)
process_data

# Backup processed data
backup_data

# Combine showings (outputs to frontend data directory)
combine_showings

# Frontend options
frontend_options

echo -e "\n\n${GREEN_BG}${BOLD} ///// DCKino Docker Pipeline Complete ///// ${default}\n\n"