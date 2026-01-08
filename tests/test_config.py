"""Tests for configuration management."""

import yaml

from auditd_monitor.config import Config


class TestConfig:
    """Test configuration loading and validation."""

    def test_default_config(self):
        """Test that default config is loaded when no file exists."""
        config = Config(config_path="/nonexistent/path.yaml")
        assert config.get("check_interval") == 60
        assert config.get("inactivity_threshold") == 300
        assert config.get("audit_service") == "auditd"

    def test_load_from_file(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        test_config = {
            "log_file": "/var/log/test.log",
            "audit_service": "test-audit",
            "check_interval": 120,
            "inactivity_threshold": 600,
        }

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        config = Config(config_path=str(config_file))
        assert config.get("log_file") == "/var/log/test.log"
        assert config.get("audit_service") == "test-audit"
        assert config.get("check_interval") == 120
        assert config.get("inactivity_threshold") == 600

    def test_config_override(self, tmp_path):
        """Test that config file overrides defaults."""
        config_file = tmp_path / "config.yaml"
        test_config = {
            "check_interval": 30,
        }

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        config = Config(config_path=str(config_file))
        # Overridden value
        assert config.get("check_interval") == 30
        # Default values still present
        assert config.get("inactivity_threshold") == 300
        assert config.get("audit_service") == "auditd"

    def test_validate_valid_config(self, tmp_path):
        """Test validation of valid configuration."""
        # Create a test log file
        log_file = tmp_path / "test.log"
        log_file.touch()

        config_file = tmp_path / "config.yaml"
        test_config = {
            "log_file": str(log_file),
            "audit_service": "auditd",
            "check_interval": 60,
            "inactivity_threshold": 300,
        }

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        config = Config(config_path=str(config_file))
        assert config.validate() is True

    def test_validate_missing_log_file(self):
        """Test validation fails when log file doesn't exist."""
        config = Config()
        config.config["log_file"] = "/nonexistent/file.log"
        assert config.validate() is False

    def test_validate_invalid_interval(self, tmp_path):
        """Test validation fails with invalid intervals."""
        log_file = tmp_path / "test.log"
        log_file.touch()

        config = Config()
        config.config["log_file"] = str(log_file)
        config.config["check_interval"] = -1
        assert config.validate() is False

        config.config["check_interval"] = 60
        config.config["inactivity_threshold"] = 0
        assert config.validate() is False

    def test_get_with_default(self):
        """Test get method with default value."""
        config = Config()
        assert config.get("nonexistent_key", "default_value") == "default_value"
        assert config.get("check_interval", 999) == 60

    def test_getitem(self):
        """Test dictionary-style access."""
        config = Config()
        assert config["check_interval"] == 60
        assert config["audit_service"] == "auditd"
