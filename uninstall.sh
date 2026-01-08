#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Auditd Monitor Uninstallation ===${NC}\n"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root${NC}"
   echo "Please run: sudo ./uninstall.sh"
   exit 1
fi

# Confirm uninstallation
echo -e "${YELLOW}This will uninstall Auditd Monitor from your system.${NC}"
read -p "Are you sure you want to continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uninstallation cancelled.${NC}"
    exit 0
fi

# Stop and disable service
if systemctl is-active --quiet auditd-monitor; then
    echo -e "\n${GREEN}Stopping auditd-monitor service...${NC}"
    systemctl stop auditd-monitor
fi

if systemctl is-enabled --quiet auditd-monitor 2>/dev/null; then
    echo -e "${GREEN}Disabling auditd-monitor service...${NC}"
    systemctl disable auditd-monitor
fi

# Reset failed state before removing service file
echo -e "${GREEN}Cleaning systemd state...${NC}"
systemctl reset-failed auditd-monitor 2>/dev/null || true

# Remove systemd service file
if [ -f /etc/systemd/system/auditd-monitor.service ]; then
    echo -e "${GREEN}Removing systemd service file...${NC}"
    rm -f /etc/systemd/system/auditd-monitor.service
    systemctl daemon-reload
fi

# Remove installation directory
if [ -d /opt/auditd-monitor ]; then
    echo -e "${GREEN}Removing installation directory /opt/auditd-monitor...${NC}"
    rm -rf /opt/auditd-monitor
fi

# Ask about configuration files
if [ -d /etc/auditd-monitor ]; then
    echo -e "\n${YELLOW}Configuration files found in /etc/auditd-monitor${NC}"
    read -p "Do you want to remove configuration files? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Removing configuration directory...${NC}"
        rm -rf /etc/auditd-monitor
    else
        echo -e "${YELLOW}Configuration files kept in /etc/auditd-monitor${NC}"
    fi
fi

# Ask about log files
if [ -f /var/log/auditd-monitor.log ]; then
    echo -e "\n${YELLOW}Log files found${NC}"
    read -p "Do you want to remove log files? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Removing log files...${NC}"
        rm -f /var/log/auditd-monitor.log*
    else
        echo -e "${YELLOW}Log files kept in /var/log/auditd-monitor.log${NC}"
    fi
fi

# Optional: Remove uv if it was installed by this script
echo -e "\n${YELLOW}Note: uv package manager was not removed as it may be used by other projects.${NC}"
echo -e "If you want to remove it manually, run: rm -rf ~/.local/bin/uv ~/.local/bin/uvx"

echo -e "\n${GREEN}=== Uninstallation Complete ===${NC}\n"
echo -e "Auditd Monitor has been removed from your system."
echo -e "Thank you for using Auditd Monitor!"
