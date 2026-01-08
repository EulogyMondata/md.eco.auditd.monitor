"""Example output demonstrating auditd-monitor logging."""

# Normal operation - no issues

"""
2026-01-08 10:30:00 - auditd-monitor - INFO - Checking audit log activity...
2026-01-08 10:30:00 - auditd-monitor - INFO - Last audit entry was 45 seconds ago (threshold: 300s)
2026-01-08 10:30:00 - auditd-monitor - INFO - Auditd is writing to logs normally
"""

# Inactivity detected and service restarted successfully

"""
2026-01-08 11:15:00 - auditd-monitor - INFO - Checking audit log activity...
2026-01-08 11:15:00 - auditd-monitor - INFO - Last audit entry was 450 seconds ago (threshold: 300s)
2026-01-08 11:15:00 - auditd-monitor - WARNING - ================================================================================
2026-01-08 11:15:00 - auditd-monitor - WARNING - ⚠️  AUDITD INACTIVITY DETECTED - No audit logs for 450 seconds (threshold: 300s)
2026-01-08 11:15:00 - auditd-monitor - WARNING - Last audit entry was at: 2026-01-08 11:07:30
2026-01-08 11:15:00 - auditd-monitor - WARNING - ================================================================================
2026-01-08 11:15:00 - auditd-monitor - INFO - Current auditd status: RUNNING
2026-01-08 11:15:00 - auditd-monitor - WARNING - 🔄 ATTEMPTING TO RESTART AUDITD SERVICE...
2026-01-08 11:15:01 - auditd-monitor - WARNING - ✅ SUCCESS: Successfully restarted auditd
2026-01-08 11:15:01 - auditd-monitor - WARNING - auditd has been restarted and should resume logging
"""

# Failed restart attempt

"""
2026-01-08 12:00:00 - auditd-monitor - INFO - Checking audit log activity...
2026-01-08 12:00:00 - auditd-monitor - INFO - Last audit entry was 350 seconds ago (threshold: 300s)
2026-01-08 12:00:00 - auditd-monitor - WARNING - ================================================================================
2026-01-08 12:00:00 - auditd-monitor - WARNING - ⚠️  AUDITD INACTIVITY DETECTED - No audit logs for 350 seconds (threshold: 300s)
2026-01-08 12:00:00 - auditd-monitor - WARNING - Last audit entry was at: 2026-01-08 11:54:10
2026-01-08 12:00:00 - auditd-monitor - WARNING - ================================================================================
2026-01-08 12:00:00 - auditd-monitor - INFO - Current auditd status: NOT RUNNING
2026-01-08 12:00:00 - auditd-monitor - WARNING - 🔄 ATTEMPTING TO RESTART AUDITD SERVICE...
2026-01-08 12:00:01 - auditd-monitor - ERROR - ================================================================================
2026-01-08 12:00:01 - auditd-monitor - ERROR - ❌ FAILED TO RESTART AUDITD
2026-01-08 12:00:01 - auditd-monitor - ERROR - Error: Failed to restart auditd: Job for auditd.service failed
2026-01-08 12:00:01 - auditd-monitor - ERROR - ================================================================================
"""

# Commands to view these logs

"""

# View in real-time

sudo journalctl -u auditd-monitor -f

# View last 50 lines

sudo journalctl -u auditd-monitor -n 50

# View only WARNING and ERROR messages

sudo journalctl -u auditd-monitor -p warning

# View logs from the last hour

sudo journalctl -u auditd-monitor --since "1 hour ago"

# View logs for a specific date

sudo journalctl -u auditd-monitor --since "2026-01-08 10:00:00" --until "2026-01-08 12:00:00"

# View logs in the monitor's own log file

sudo tail -f /var/log/auditd-monitor.log

# Search for restart events

sudo journalctl -u auditd-monitor | grep "RESTART"
sudo journalctl -u auditd-monitor | grep "INACTIVITY"
"""
