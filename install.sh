#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Auditd Monitor Installation ===${NC}\n"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root${NC}"
   echo "Please run: sudo ./install.sh"
   exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo -e "${GREEN}Installation script location: $SCRIPT_DIR${NC}"

# Change to script directory to ensure relative paths work
cd "$SCRIPT_DIR"

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    echo -e "${GREEN}Detected OS: $PRETTY_NAME${NC}"
else
    echo -e "${YELLOW}Warning: Cannot detect OS, assuming Debian-based${NC}"
    OS="unknown"
fi

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH (it gets installed in different locations depending on user)
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:/root/.cargo/bin:/root/.local/bin:$PATH"
    
    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: uv installation failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}uv installed successfully${NC}"
else
    echo -e "${GREEN}uv is already installed${NC}"
fi

# Ensure uv has correct ownership when running as root
if [ -f "/root/.local/bin/uv" ]; then
    chown root:root /root/.local/bin/uv /root/.local/bin/uvx 2>/dev/null || true
fi

# Create installation directory
INSTALL_DIR="/opt/auditd-monitor"
echo -e "\n${GREEN}Creating installation directory: $INSTALL_DIR${NC}"
mkdir -p "$INSTALL_DIR"

# Copy files
echo -e "${GREEN}Copying project files...${NC}"

# Verify files exist before copying
if [ ! -d "auditd_monitor" ]; then
    echo -e "${RED}Error: auditd_monitor directory not found in $SCRIPT_DIR${NC}"
    echo -e "${RED}Please make sure you're running this script from the project root directory${NC}"
    exit 1
fi

cp -r auditd_monitor "$INSTALL_DIR/"
cp pyproject.toml "$INSTALL_DIR/"
cp config.example.yaml "$INSTALL_DIR/"
cp auditd-monitor.service "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/" 2>/dev/null || true

# Create config directory
CONFIG_DIR="/etc/auditd-monitor"
echo -e "${GREEN}Creating configuration directory: $CONFIG_DIR${NC}"
mkdir -p "$CONFIG_DIR"

# Copy or create config file
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo -e "${GREEN}Creating default configuration...${NC}"
    cp config.example.yaml "$CONFIG_DIR/config.yaml"
    
    # Detect appropriate log file based on distribution
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        LOG_FILE="/var/log/syslog"
    elif [ "$OS" = "rhel" ] || [ "$OS" = "centos" ] || [ "$OS" = "rocky" ] || [ "$OS" = "fedora" ]; then
        LOG_FILE="/var/log/messages"
    else
        LOG_FILE="/var/log/syslog"
    fi
    
    # Update config with detected log file
    sed -i "s|log_file: /var/log/syslog|log_file: $LOG_FILE|" "$CONFIG_DIR/config.yaml"
    
    echo -e "${YELLOW}Configuration file created at: $CONFIG_DIR/config.yaml${NC}"
    echo -e "${YELLOW}Please review and adjust settings as needed.${NC}"
else
    echo -e "${YELLOW}Configuration file already exists, skipping${NC}"
fi

# Install dependencies
echo -e "\n${GREEN}Installing Python dependencies...${NC}"
cd "$INSTALL_DIR"
uv sync

# Install systemd service
echo -e "\n${GREEN}Installing systemd service...${NC}"
cp "$INSTALL_DIR/auditd-monitor.service" /etc/systemd/system/
systemctl daemon-reload

# Enable and start service
echo -e "${GREEN}Enabling and starting service...${NC}"
systemctl enable auditd-monitor
systemctl start auditd-monitor

echo -e "\n${GREEN}=== Installation Complete ===${NC}\n"

echo -e "Configuration file: ${YELLOW}$CONFIG_DIR/config.yaml${NC}"
echo -e "Installation directory: ${YELLOW}$INSTALL_DIR${NC}"
echo -e "\n${GREEN}Service is enabled and running!${NC}"
echo -e "\nTo check status:"
echo -e "  ${GREEN}sudo systemctl status auditd-monitor${NC}"
echo -e "\nTo view logs:"
echo -e "  ${GREEN}sudo journalctl -u auditd-monitor -f${NC}"
echo -e "\nTo edit configuration:"
echo -e "  ${GREEN}sudo nano $CONFIG_DIR/config.yaml${NC}"
echo -e "  ${GREEN}sudo systemctl restart auditd-monitor${NC}"

echo -e "\n${YELLOW}Note: Please review the configuration file and adjust settings for your system.${NC}"
