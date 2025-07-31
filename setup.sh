#!/bin/bash

# Set script to exit on any errors
set -e

# Base directory (location of this script)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Paths
FRONTEND_DIR="$BASE_DIR/frontend"
BACKEND_DIR="$BASE_DIR/backend"

# ANSI text styles and colors
default="$(printf '\033[0m')"
BLUE="$(printf '\033[1;34m')"
GREEN="$(printf '\033[1;32m')"
YELLOW="$(printf '\033[1;33m')"
RED="$(printf '\033[1;31m')"
MAGENTA="$(printf '\033[1;35m')"
BLINK="$(printf '\033[5m')"
BOLD="$(printf '\033[1m')"
UNDERLINE="$(printf '\033[4m')"
GREEN_BG="$(printf '\033[42m')"
BLUE_BG="$(printf '\033[44m')"
MAGENTA_BG="$(printf '\033[45m')"

# Function to check Node.js version
check_nodejs_version() {
    echo -e "${BLUE}Checking Node.js version... ${default}"
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
        if (( NODE_VERSION >= 20 )); then
            echo -e "${GREEN}Node.js version $NODE_VERSION found, which is >= 20. ${default}"
        else
            echo -e "${RED}Error: Node.js version $NODE_VERSION found, but Node.js version 20 or higher is required. On Ubuntu, install Node Version Manager (NVM) 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash' and run 'nvm install 20'. ${default}"
            exit 1
        fi
    else
        echo -e "${RED}Error: Node.js is not installed. Please install Node.js version 20 or higher. On Ubuntu, install Node Version Manager (NVM) 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash' and run 'nvm install 20'. ${default}"
        exit 1
    fi
}

# Function to set up venv for backend
setup_venv() {
    echo -e "${BLUE}Setting up virtual environment for backend... ${YELLOW}\n"
    python3 -m venv "$BACKEND_DIR/venv"
    source "$BACKEND_DIR/venv/bin/activate"
    pip install -r "$BACKEND_DIR/requirements.txt"
    deactivate
    echo -e "\n${GREEN}Virtual environment setup complete. ${default}"
}

# Function to set up DCKino site frontend
setup_dckino_site() {
    cd "$FRONTEND_DIR"
    echo -e "${BLUE}Setting up DCKino site... ${YELLOW}"
    npm install
    echo -e "\n${GREEN}DCKino site setup complete. ${default}"
}

# Function to set up .env file
setup_env() {
    echo -e "${BLUE}Setting up frontend environment file...${default}\n\n"
    ENV_FILE="$FRONTEND_DIR/.env"
    read -p "${MAGENTA_BG}Please enter your TMDB API Key:${default} " TMDB_API_KEY
    if [ -z "$TMDB_API_KEY" ]; then
        echo -e "\n\n${RED}Error: TMDB API Key cannot be empty.${default}"
        exit 1
    fi
    echo "VITE_TMDB_API_KEY=$TMDB_API_KEY" > "$ENV_FILE"
    echo -e "\n\n${GREEN}.env file created successfully at $ENV_FILE ${default}"
}

# Function for NPM Options
site_start_options() {
    cd "$FRONTEND_DIR"
    echo -e "\n\n${BLUE_BG}What would you like to do now?${default}\n"
    echo -e "${MAGENTA}  1. Run DCKino pipeline (full production)"
    echo -e "${MAGENTA}  2. Run basic dev server ${default}"
    echo -e "${MAGENTA}  3. Nothing ${default}\n"
    read -p "${BLUE}${BLINK}Enter your choice (1-3):${default} " choice
    case $choice in
        1)
            echo -e "\n\n${BLUE}Running testrun pipeline... ${default}"
            cd "$BASE_DIR"
            ./run_dckino.sh
            ;;
        2)
            echo -e "\n\n${BLUE}Starting dev server... This will block the terminal. Press Ctrl+C to exit.${YELLOW}"
            npm run dev
            echo -e "${default}"
            ;;
        3)
            echo -e "\n\n${GREEN}No action taken. You can start the site later by running 'npm run dev' or 'npm run build' in the '$FRONTEND_DIR' directory.${default}"
            ;;
        *)
            echo -e "\n\n${RED}Invalid choice. No action taken.${default}"
            ;;
    esac
}

echo -e "\n\n${MAGENTA_BG}${BOLD}${UNDERLINE} ///// Beginning DCKino Installation Script ///// ${default}\n\n"

# Check Node.js version
check_nodejs_version

# Setup virtual environment for backend
setup_venv

# Setup DCKino site
setup_dckino_site

# Set up .env file
setup_env

# Ask user what to do with the site
site_start_options

echo -e "\n\n${GREEN_BG}${BOLD} ///// DCKino Installation Complete ///// ${default}\n\n"