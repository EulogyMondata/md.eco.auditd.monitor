"""Tests for service manager."""

import subprocess
from unittest.mock import MagicMock, patch


from auditd_monitor.service_manager import ServiceManager


class TestServiceManager:
    """Test service management functionality."""

    def test_detect_systemd(self):
        """Test detection of systemd."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/bin/systemctl"
            manager = ServiceManager("test-service")
            assert manager.service_system == "systemd"

    def test_detect_sysvinit(self):
        """Test detection of sysvinit."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/sbin/service"
            manager = ServiceManager("test-service")
            assert manager.service_system == "sysvinit"

    def test_restart_service_systemd(self):
        """Test restarting service with systemd."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/bin/systemctl"

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="", returncode=0)

                manager = ServiceManager("auditd")
                success, message = manager.restart_service()

                assert success is True
                assert "Successfully restarted" in message
                mock_run.assert_called_once()
                assert mock_run.call_args[0][0] == ["systemctl", "restart", "auditd"]

    def test_restart_service_sysvinit(self):
        """Test restarting service with sysvinit."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/sbin/service"

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="", returncode=0)

                manager = ServiceManager("auditd")
                success, message = manager.restart_service()

                assert success is True
                mock_run.assert_called_once()
                assert mock_run.call_args[0][0] == ["service", "auditd", "restart"]

    def test_restart_service_dry_run(self):
        """Test dry run mode doesn't actually restart."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/bin/systemctl"

            with patch("subprocess.run") as mock_run:
                manager = ServiceManager("auditd", dry_run=True)
                success, message = manager.restart_service()

                assert success is True
                assert "DRY RUN" in message
                mock_run.assert_not_called()

    def test_restart_service_failure(self):
        """Test handling of service restart failure."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/bin/systemctl"

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, "systemctl", stderr="Error restarting service"
                )

                manager = ServiceManager("auditd")
                success, message = manager.restart_service()

                assert success is False
                assert "Failed to restart" in message

    def test_is_service_running_systemd(self):
        """Test checking if service is running with systemd."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/bin/systemctl"

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="active", returncode=0)

                manager = ServiceManager("auditd")
                assert manager.is_service_running() is True

                mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")
                assert manager.is_service_running() is False

    def test_get_service_status(self):
        """Test getting service status."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "/bin/systemctl"

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="active (running)", returncode=0)

                manager = ServiceManager("auditd")
                is_running, status = manager.get_service_status()

                assert is_running is True
                assert "active" in status
