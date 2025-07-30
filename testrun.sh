#!/bin/bash

# Set script to exit on any errors
set -e

# Base directory (location of this script)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Paths
FRONTEND_DIR="$BASE_DIR/frontend"
BACKEND_DIR="$BASE_DIR/backend"

# ANSI text colors, styles, and backgrounds
default="$(printf '\033[0m')"
BLUE="$(printf '\033[1;34m')"
GREEN="$(printf '\033[1;32m')"
YELLOW="$(printf '\033[1;33m')"
BOLD="$(printf '\033[1m')"
UNDERLINE="$(printf '\033[4m')"
BLINK="$(printf '\033[5m')"
GREEN_BG="$(printf '\033[42m')"
BLUE_BG="$(printf '\033[44m')"
MAGENTA_BG="$(printf '\033[45m')"

# Function for backing up old JSONs
backup_json_data() {
    cd "$BACKEND_DIR/DCKinoSites/utils"
    echo -e "${BLUE}Backing up old JSONs... ${default}"
    python3 backup_data.py
    echo -e "${GREEN}Backup script ran${default}"
}

# Function for activating virtual environment
activate_venv() {
    echo -e "${BLUE}Activating virtual environment... ${default}"
    source "$BACKEND_DIR/venv/bin/activate"
    echo -e "${GREEN}Virtual environment activated successfully ${default}"
}

# Function for deactivating virtual environment
deactivate_venv() {
    echo -e "${BLUE}Deactivating virtual environment... ${default}"
    deactivate
    echo -e "${GREEN}Virtual environment deactivated successfully ${default}"
}

# Function for running Spiders
run_movie_spiders() {
    cd "$BACKEND_DIR/DCKinoSites"
    declare -A spiders=(
        [afisilver]="AFI"
        [miracle]="Miracle"
        [suns]="Suns"
        [avalon]="Avalon"
        [landmark]="Landmark"
    )
    echo -e "${BLUE_BG}Running spiders...${default}"
    for spider_name in "${!spiders[@]}"; do
        display_name="${spiders[$spider_name]}"
        echo -e "${BLUE}Running ${display_name} spider... ${YELLOW}\n"
        scrapy crawl "$spider_name"
        echo -e "\n${GREEN}${BLINK}${display_name} spider finished ${default}"
    done
}

# Function for combining and filtering showings
combine_showings() {
    cd "$BACKEND_DIR/DCKinoSites/utils"
    echo -e "${BLUE}Combining and filtering showings... ${default}"
    python combine_showings.py
    echo -e "${GREEN}Combine script ran successfully ${default}"
}

# Function for test running site
run_dckino_site() {
    cd "$FRONTEND_DIR"
    echo -e "${BLUE}Starting dev server for DCKino site... ${default}"
    npm run dev
    echo -e "${GREEN_BG}DCKino site dev server started successfully${default}"
}

echo -e "\n\n${MAGENTA_BG}${BOLD}${UNDERLINE} ///// Beginning DCKino Testrun Script ///// ${default}\n\n"

# Backup old JSONs
backup_json_data

# Activate virtual environment
activate_venv

# Run spiders
run_movie_spiders

# Run combining script
combine_showings

# Deactivate venv
deactivate_venv

# Run DCKino site dev server
run_dckino_site

echo -e "\n\n${GREEN_BG}${BOLD} ///// DCKino Testrun Complete ///// ${default}\n\n"