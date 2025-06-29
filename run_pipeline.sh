#!/bin/bash

# Set script to exit on any errors
set -e

# Base directory (location of this script)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Paths
SCRAPER_DIR="$BASE_DIR/Scraper/DCKinoSites"
VENV_DIR="$BASE_DIR/Scraper/venv"
SITE_DIR="$BASE_DIR/Site/dc-kino-site"

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "Virtual environment activated successfully"

# Change to Scrapy project directory
cd "$SCRAPER_DIR"

# Run spiders
echo "Running AFI spider..."
scrapy crawl afisilver
echo "AFI spider ran sucessfully"

echo "Running Miracle spider..."
scrapy crawl miracle
echo "Miracle spider ran sucessfully"

# Run combining script
echo "Combining and filtering showings..."
python combine_showings.py
echo "Combine script ran successfully"

# Deactivate venv
echo "Deactivating virtual environment..."
deactivate
echo "Virtual environment deactivated"

# Run React site
echo "Starting React site..."
cd "$SITE_DIR"
npm run dev
echo "React site started successfully"