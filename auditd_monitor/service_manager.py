"""Service management utilities for different Linux distributions."""

import os
import subprocess
from typing import Tuple


class ServiceManager:
    """Manage system services across different Linux distributions."""

    def __init__(self, service_name: str, dry_run: bool = False):
        """Initialize service manager.

        Args:
            service_name: Name of the service to manage.
            dry_run: If True, only log actions without executing them.
        """
        self.service_name = service_name
        self.dry_run = dry_run
        self.service_system = self._detect_service_system()

    def _detect_service_system(self) -> str:
        """Detect which service management system is in use.

        Returns:
            'systemd', 'sysvinit', or 'unknown'.
        """
        if os.path.exists("/bin/systemctl") or os.path.exists("/usr/bin/systemctl"):
            return "systemd"
        elif os.path.exists("/sbin/service") or os.path.exists("/usr/sbin/service"):
            return "sysvinit"
        return "unknown"

    def _run_command(self, command: list) -> Tuple[bool, str]:
        """Run a system command.

        Args:
            command: Command to run as list of strings.

        Returns:
            Tuple of (success, output).
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"{e.stdout}\n{e.stderr}"
        except Exception as e:
            return False, str(e)

    def restart_service(self) -> Tuple[bool, str]:
        """Restart the service.

        Returns:
            Tuple of (success, message).
        """
        if self.dry_run:
            return True, f"DRY RUN: Would restart service '{self.service_name}'"

        if self.service_system == "systemd":
            command = ["systemctl", "restart", self.service_name]
        elif self.service_system == "sysvinit":
            command = ["service", self.service_name, "restart"]
        else:
            return False, f"Unknown service system, cannot restart {self.service_name}"

        success, output = self._run_command(command)
        if success:
            return True, f"Successfully restarted {self.service_name}"
        else:
            return False, f"Failed to restart {self.service_name}: {output}"

    def is_service_running(self) -> bool:
        """Check if the service is running.

        Returns:
            True if service is running, False otherwise.
        """
        if self.service_system == "systemd":
            command = ["systemctl", "is-active", self.service_name]
        elif self.service_system == "sysvinit":
            command = ["service", self.service_name, "status"]
        else:
            return False

        success, _ = self._run_command(command)
        return success

    def get_service_status(self) -> Tuple[bool, str]:
        """Get detailed service status.

        Returns:
            Tuple of (is_running, status_output).
        """
        if self.service_system == "systemd":
            command = ["systemctl", "status", self.service_name]
        elif self.service_system == "sysvinit":
            command = ["service", self.service_name, "status"]
        else:
            return False, "Unknown service system"

        success, output = self._run_command(command)
        return success, output
