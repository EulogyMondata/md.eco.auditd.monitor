#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Auditd Monitor Quick Install ===${NC}\n"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root${NC}"
   echo "Please run: curl -sSL https://raw.githubusercontent.com/EulogyMondata/md.eco.auditd.monitor/main/quick-install.sh | sudo bash"
   exit 1
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo -e "${GREEN}Creating temporary directory: $TEMP_DIR${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${GREEN}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Download the project
echo -e "${GREEN}Downloading project from GitHub...${NC}"
cd "$TEMP_DIR"

# Try git clone first, fall back to wget/curl if git is not available
if command -v git &> /dev/null; then
    git clone https://github.com/EulogyMondata/md.eco.auditd.monitor.git
    cd md.eco.auditd.monitor
elif command -v wget &> /dev/null; then
    wget https://github.com/EulogyMondata/md.eco.auditd.monitor/archive/refs/heads/main.tar.gz
    tar -xzf main.tar.gz
    cd md.eco.auditd.monitor-main
elif command -v curl &> /dev/null; then
    curl -L https://github.com/EulogyMondata/md.eco.auditd.monitor/archive/refs/heads/main.tar.gz -o main.tar.gz
    tar -xzf main.tar.gz
    cd md.eco.auditd.monitor-main
else
    echo -e "${RED}Error: git, wget, or curl is required to download the project${NC}"
    exit 1
fi

echo -e "${GREEN}Project downloaded successfully${NC}\n"

# Run the installation script
echo -e "${GREEN}Running installation script...${NC}\n"
bash install.sh

echo -e "\n${GREEN}=== Quick Install Complete ===${NC}\n"
echo -e "The temporary files will be cleaned up automatically."
