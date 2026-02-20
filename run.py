"""
Launcher / process supervisor for the LED panel display manager.

Runs display_manager as a child process and automatically restarts it when
it exits with a non-zero code (e.g. after too many BLE reconnection failures).
A clean exit (code 0) or KeyboardInterrupt stops the supervisor.

Usage:
    python run.py
"""
import logging
import signal
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] launcher: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("launcher")

RESTART_DELAY = 3  # seconds to wait between restarts
CHILD_MODULE = "display_manager"


def main() -> None:
    child = None

    def _forward_signal(signum, _frame) -> None:
        """Forward Ctrl+C / SIGTERM to the child so it can clean up."""
        if child and child.poll() is None:
            child.send_signal(signum)

    signal.signal(signal.SIGINT, _forward_signal)
    signal.signal(signal.SIGTERM, _forward_signal)

    logger.info("Supervisor started (press Ctrl+C to stop)")

    while True:
        logger.info("Starting display manager...")
        child = subprocess.Popen([sys.executable, "-m", CHILD_MODULE])
        child.wait()

        code = child.returncode

        # Negative return code = killed by signal (e.g. SIGINT from Ctrl+C)
        if code in (0, -signal.SIGINT, -signal.SIGTERM):
            logger.info(f"Display manager exited cleanly (code {code}). Stopping.")
            break

        logger.warning(
            f"Display manager exited with code {code}. "
            f"Restarting in {RESTART_DELAY}s..."
        )
        time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    main()
