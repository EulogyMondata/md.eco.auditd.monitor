"""Configuration management for Auditd Monitor."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    """Manage configuration for Auditd Monitor."""

    DEFAULT_CONFIG_PATHS = [
        "/etc/auditd-monitor/config.yaml",
        "/etc/auditd-monitor.yaml",
        str(Path.home() / ".config" / "auditd-monitor" / "config.yaml"),
        "config.yaml",
    ]

    DEFAULT_CONFIG = {
        "log_file": "/var/log/syslog",
        "audit_service": "auditd",
        "check_interval": 60,
        "inactivity_threshold": 300,
        "audit_pattern": r"type=(EXECVE|CWD|PATH|SYSCALL|USER_AUTH|USER_CMD|CRED_ACQ|CRED_DISP|LOGIN|USER_START|USER_END|SERVICE_START|SERVICE_STOP|DAEMON_START|DAEMON_END|CONFIG_CHANGE|ANOM_PROMISCUOUS|AVC|SELINUX_ERR|USER_ACCT)",
        "monitor_log_file": "/var/log/auditd-monitor.log",
        "log_level": "INFO",
        "dry_run": False,
    }

    def __init__(self, config_path: str = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, searches default locations.
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()

    def _find_config(self) -> str:
        """Find configuration file in default locations.

        Returns:
            Path to configuration file, or None if not found.
        """
        for path in self.DEFAULT_CONFIG_PATHS:
            if os.path.exists(path):
                return path
        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults.

        Returns:
            Configuration dictionary.
        """
        config = self.DEFAULT_CONFIG.copy()

        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        config.update(user_config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}", file=sys.stderr)
                print("Using default configuration.", file=sys.stderr)

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value.
        """
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax.

        Args:
            key: Configuration key.

        Returns:
            Configuration value.
        """
        return self.config[key]

    def validate(self) -> bool:
        """Validate configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        errors = []

        # Check log file
        log_file = self.get("log_file")
        if not log_file:
            errors.append("log_file is required")
        elif not os.path.exists(log_file):
            errors.append(f"log_file does not exist: {log_file}")

        # Check audit service
        if not self.get("audit_service"):
            errors.append("audit_service is required")

        # Check intervals
        check_interval = self.get("check_interval")
        if not isinstance(check_interval, (int, float)) or check_interval <= 0:
            errors.append("check_interval must be a positive number")

        inactivity_threshold = self.get("inactivity_threshold")
        if not isinstance(inactivity_threshold, (int, float)) or inactivity_threshold <= 0:
            errors.append("inactivity_threshold must be a positive number")

        if errors:
            print("Configuration errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return False

        return True
