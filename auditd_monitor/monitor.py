#!/usr/bin/env python3
"""Main monitoring script for Auditd Monitor."""

import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta

from auditd_monitor.config import Config
from auditd_monitor.service_manager import ServiceManager


class AuditdMonitor:
    """Monitor audit logs and restart auditd when inactive."""

    def __init__(self, config: Config):
        """Initialize the monitor.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.service_manager = ServiceManager(
            config["audit_service"], dry_run=config.get("dry_run", False)
        )
        self.last_audit_entry_time = None
        self.audit_pattern = re.compile(config["audit_pattern"])
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = getattr(logging, self.config.get("log_level", "INFO").upper())
        log_file = self.config.get("monitor_log_file")

        # Create log directory if it doesn't exist
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except PermissionError:
                    print(f"Warning: Cannot create log directory {log_dir}", file=sys.stderr)
                    log_file = None

        handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(console_handler)

        # File handler
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                )
                handlers.append(file_handler)
            except PermissionError:
                print(f"Warning: Cannot write to log file {log_file}", file=sys.stderr)

        logging.basicConfig(level=log_level, handlers=handlers)
        self.logger = logging.getLogger("auditd-monitor")

    def _get_last_audit_entry_time(self) -> datetime:
        """Get the timestamp of the last audit entry in the log file.

        Returns:
            Datetime of last audit entry, or None if no entry found.
        """
        log_file = self.config["log_file"]

        if not os.path.exists(log_file):
            self.logger.error(f"Log file not found: {log_file}")
            return None

        try:
            # Read the last N lines of the log file
            # Use tail for efficiency on large files and compatibility with logrotate
            # Using tail command ensures we don't hold file locks that would interfere with logrotate
            tail_lines = 1000
            result = os.popen(f"tail -n {tail_lines} {log_file}").read()
            lines = result.strip().split("\n")

            # Search backwards for the most recent audit entry
            for line in reversed(lines):
                if self.audit_pattern.search(line):
                    # Try to extract timestamp
                    timestamp = self._extract_timestamp(line)
                    if timestamp:
                        return timestamp

            self.logger.warning(f"No audit entries found in last {tail_lines} lines")
            return None

        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return None

    def _extract_timestamp(self, log_line: str) -> datetime:
        """Extract timestamp from a log line.

        Args:
            log_line: Line from the log file.

        Returns:
            Datetime object, or None if timestamp cannot be extracted.
        """
        # Common syslog format: "Jan  8 10:30:45"
        # RFC3339 format: "2026-01-08T10:30:45.123456+00:00"

        # Try syslog format first
        try:
            # Extract the first part that looks like a date
            parts = log_line.split()
            if len(parts) >= 3:
                # Try "Jan  8 10:30:45" format
                date_str = " ".join(parts[:3])
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {date_str}", "%Y %b %d %H:%M:%S")
                return timestamp
        except ValueError:
            pass

        # Try ISO format
        try:
            # Look for ISO timestamp pattern
            iso_pattern = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
            match = re.search(iso_pattern, log_line)
            if match:
                timestamp_str = match.group()
                timestamp = datetime.strptime(
                    timestamp_str.replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S"
                )
                return timestamp
        except ValueError:
            pass

        # If we can't parse the timestamp, use current time
        # This is better than returning None as it prevents false positives
        self.logger.debug(f"Could not parse timestamp from line: {log_line[:100]}")
        return datetime.now()

    def check_and_restart(self):
        """Check if auditd is writing to logs and restart if necessary."""
        self.logger.info("Checking audit log activity...")

        last_entry_time = self._get_last_audit_entry_time()

        if last_entry_time is None:
            self.logger.warning("No audit entries found in log file")
            # Don't restart on first run or if we can't determine status
            if self.last_audit_entry_time is not None:
                self.logger.info("Cannot determine audit activity, skipping restart")
            self.last_audit_entry_time = datetime.now()
            return

        # Calculate time since last entry
        time_since_last_entry = datetime.now() - last_entry_time
        threshold = timedelta(seconds=self.config["inactivity_threshold"])

        self.logger.info(
            f"Last audit entry was {time_since_last_entry.total_seconds():.0f} seconds ago "
            f"(threshold: {threshold.total_seconds():.0f}s)"
        )

        if time_since_last_entry > threshold:
            self.logger.warning("=" * 80)
            self.logger.warning(
                f"⚠️  AUDITD INACTIVITY DETECTED - No audit logs for "
                f"{time_since_last_entry.total_seconds():.0f} seconds "
                f"(threshold: {threshold.total_seconds():.0f}s)"
            )
            self.logger.warning(f"Last audit entry was at: {last_entry_time}")
            self.logger.warning("=" * 80)

            # Check service status before restarting
            is_running, status = self.service_manager.get_service_status()
            self.logger.info(
                f"Current {self.config['audit_service']} status: "
                f"{'RUNNING' if is_running else 'NOT RUNNING'}"
            )

            # Attempt restart
            self.logger.warning(
                f"🔄 ATTEMPTING TO RESTART {self.config['audit_service'].upper()} SERVICE..."
            )
            success, message = self.service_manager.restart_service()

            if success:
                self.logger.warning(f"✅ SUCCESS: {message}")
                self.logger.warning(
                    f"{self.config['audit_service']} has been restarted and should resume logging"
                )
            else:
                self.logger.error("=" * 80)
                self.logger.error(f"❌ FAILED TO RESTART {self.config['audit_service'].upper()}")
                self.logger.error(f"Error: {message}")
                self.logger.error("=" * 80)
        else:
            self.logger.info("Auditd is writing to logs normally")

        self.last_audit_entry_time = last_entry_time

    def run(self):
        """Run the monitoring loop."""
        self.logger.info("Starting Auditd Monitor")
        self.logger.info(f"Monitoring log file: {self.config['log_file']}")
        self.logger.info(f"Audit service: {self.config['audit_service']}")
        self.logger.info(f"Check interval: {self.config['check_interval']}s")
        self.logger.info(f"Inactivity threshold: {self.config['inactivity_threshold']}s")

        if self.config.get("dry_run"):
            self.logger.warning("Running in DRY RUN mode - will not restart services")

        try:
            while True:
                self.check_and_restart()
                time.sleep(self.config["check_interval"])
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping monitor")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor audit logs and restart auditd when inactive"
    )
    parser.add_argument("-c", "--config", help="Path to configuration file", default=None)
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without actually restarting services"
    )
    parser.add_argument(
        "--check-config", action="store_true", help="Validate configuration and exit"
    )

    args = parser.parse_args()

    # Load configuration
    config = Config(args.config)

    # Override dry-run from command line
    if args.dry_run:
        config.config["dry_run"] = True

    # Validate configuration
    if not config.validate():
        sys.exit(1)

    if args.check_config:
        print("Configuration is valid")
        print(f"Config file: {config.config_path or 'using defaults'}")
        print("\nCurrent configuration:")
        for key, value in config.config.items():
            print(f"  {key}: {value}")
        sys.exit(0)

    # Check if running as root
    if os.geteuid() != 0 and not config.get("dry_run"):
        print("Warning: Not running as root. May not be able to restart services.", file=sys.stderr)
        print("Use --dry-run to test without root privileges.", file=sys.stderr)

    # Start monitoring
    monitor = AuditdMonitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
