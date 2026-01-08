"""Tests for the main monitor functionality."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from auditd_monitor.config import Config
from auditd_monitor.monitor import AuditdMonitor


class TestAuditdMonitor:
    """Test the main monitoring functionality."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock configuration for testing."""
        log_file = tmp_path / "test.log"
        log_file.touch()

        config = Config()
        config.config.update(
            {
                "log_file": str(log_file),
                "audit_service": "test-auditd",
                "check_interval": 60,
                "inactivity_threshold": 300,
                "audit_pattern": r"type=(EXECVE|CWD|PATH|SYSCALL|USER_AUTH|USER_CMD|CRED_ACQ|CRED_DISP|LOGIN|USER_START|USER_END)",
                "monitor_log_file": str(tmp_path / "monitor.log"),
                "log_level": "INFO",
                "dry_run": True,
            }
        )
        return config

    def test_monitor_initialization(self, mock_config):
        """Test monitor initialization."""
        monitor = AuditdMonitor(mock_config)
        assert monitor.config == mock_config
        assert monitor.service_manager.service_name == "test-auditd"
        assert monitor.service_manager.dry_run is True

    def test_extract_timestamp_syslog_format(self, mock_config):
        """Test timestamp extraction from syslog format."""
        monitor = AuditdMonitor(mock_config)

        log_line = "Jan  8 10:30:45 hostname auditd[1234]: type=USER_AUTH"
        timestamp = monitor._extract_timestamp(log_line)

        assert timestamp is not None
        assert timestamp.month == 1
        assert timestamp.day == 8
        assert timestamp.hour == 10
        assert timestamp.minute == 30
        assert timestamp.second == 45

    def test_extract_timestamp_iso_format(self, mock_config):
        """Test timestamp extraction from ISO format."""
        monitor = AuditdMonitor(mock_config)

        log_line = "2026-01-08T10:30:45.123456+00:00 hostname auditd: type=USER_AUTH"
        timestamp = monitor._extract_timestamp(log_line)

        assert timestamp is not None
        assert timestamp.year == 2026
        assert timestamp.month == 1
        assert timestamp.day == 8

    def test_get_last_audit_entry_time(self, mock_config, tmp_path):
        """Test getting last audit entry time from log."""
        log_file = Path(mock_config["log_file"])

        # Write test log entries
        with open(log_file, "w") as f:
            f.write("Jan  8 10:00:00 host syslog: some message\n")
            f.write("Jan  8 10:05:00 host auditd[123]: type=USER_AUTH msg=test\n")
            f.write("Jan  8 10:10:00 host syslog: another message\n")

        monitor = AuditdMonitor(mock_config)
        last_time = monitor._get_last_audit_entry_time()

        assert last_time is not None
        assert last_time.hour == 10
        assert last_time.minute == 5

    def test_get_last_audit_entry_time_no_entries(self, mock_config, tmp_path):
        """Test when no audit entries found."""
        log_file = Path(mock_config["log_file"])

        with open(log_file, "w") as f:
            f.write("Jan  8 10:00:00 host syslog: some message\n")
            f.write("Jan  8 10:05:00 host other: another message\n")

        monitor = AuditdMonitor(mock_config)
        last_time = monitor._get_last_audit_entry_time()

        # Should return None when no audit entries found
        assert last_time is None

    def test_check_and_restart_inactive(self, mock_config, tmp_path):
        """Test restart when auditd is inactive."""
        log_file = Path(mock_config["log_file"])

        # Create old log entry (more than threshold ago)
        old_time = datetime.now() - timedelta(seconds=400)
        old_time_str = old_time.strftime("%b %d %H:%M:%S")

        with open(log_file, "w") as f:
            f.write(f"{old_time_str} host auditd[123]: type=USER_AUTH msg=test\n")

        with patch("os.popen") as mock_popen:
            mock_popen.return_value.read.return_value = (
                f"{old_time_str} host auditd[123]: type=USER_AUTH msg=test\n"
            )

            monitor = AuditdMonitor(mock_config)

            with patch.object(monitor.service_manager, "get_service_status") as mock_status:
                with patch.object(monitor.service_manager, "restart_service") as mock_restart:
                    mock_status.return_value = (True, "active")
                    mock_restart.return_value = (True, "DRY RUN: Would restart service")

                    monitor.check_and_restart()

                    # Should attempt restart due to inactivity
                    mock_restart.assert_called_once()

    def test_check_and_restart_active(self, mock_config, tmp_path):
        """Test no restart when auditd is active."""
        log_file = Path(mock_config["log_file"])

        # Create recent log entry
        recent_time = datetime.now() - timedelta(seconds=30)
        recent_time_str = recent_time.strftime("%b %d %H:%M:%S")

        with open(log_file, "w") as f:
            f.write(f"{recent_time_str} host auditd[123]: type=USER_AUTH msg=test\n")

        with patch("os.popen") as mock_popen:
            mock_popen.return_value.read.return_value = (
                f"{recent_time_str} host auditd[123]: type=USER_AUTH msg=test\n"
            )

            monitor = AuditdMonitor(mock_config)

            with patch.object(monitor.service_manager, "restart_service") as mock_restart:
                monitor.check_and_restart()

                # Should NOT restart - auditd is active
                mock_restart.assert_not_called()

    def test_check_and_restart_missing_log_file(self, mock_config):
        """Test handling of missing log file."""
        mock_config.config["log_file"] = "/nonexistent/log.file"

        monitor = AuditdMonitor(mock_config)

        # Should not crash, just log error
        monitor.check_and_restart()
