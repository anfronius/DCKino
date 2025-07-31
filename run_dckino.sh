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
MAGENTA="$(printf '\033[1;35m')"
RED="$(printf '\033[1;31m')"
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
dckino_site_options() {
    cd "$FRONTEND_DIR"
    echo -e "\n\n${BLUE_BG}What would you like to do with the frontend site now?${default}\n"
    echo -e "${MAGENTA}  1. Build and run production /dist/ ${default}"
    echo -e "${MAGENTA}  2. Build /dist/ for export ${default}"
    echo -e "${MAGENTA}  3. Run dev server ${default}"
    echo -e "${MAGENTA}  4. Nothing ${default}\n"
    read -p "${BLUE}${BLINK}Enter your choice (1-4):${default} " choice
    case $choice in
        1)
            echo -e "\n\n${BLUE}Building production /dist...${YELLOW}"
            npm run build
            echo -e "${BLUE}Build complete. Running Preview... This will block the terminal. Press Ctrl+C to exit.${YELLOW}"
            npm run preview
            echo -e "${default}"
            ;;
        2)
            echo -e "\n\n${BLUE}Building /dist...${YELLOW}"
            npm run build
            echo -e "${GREEN}Build complete. Run preview with 'npm run preview' in the '$FRONTEND_DIR' directory. ${default}"
        ;;
        3)
            echo -e "\n\n${BLUE}Starting dev server... This will block the terminal. Press Ctrl+C to exit.${YELLOW}"
            npm run dev
            echo -e "${default}"
            ;;
        4)
            echo -e "\n\n${GREEN}No action taken. You can start the site later by running 'npm run dev' or 'npm run build' then 'npm run preview' in the '$FRONTEND_DIR' directory.${default}"
            ;;
        *)
            echo -e "\n\n${RED}Invalid choice. No action taken.${default}"
            ;;
    esac
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

# Run DCKino NPM options
dckino_site_options

echo -e "\n\n${GREEN_BG}${BOLD} ///// DCKino Testrun Complete ///// ${default}\n\n"