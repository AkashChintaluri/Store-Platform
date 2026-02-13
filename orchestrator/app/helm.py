"""
Helm execution utility for the orchestrator service.
"""

import subprocess


def run_helm(cmd: list[str]) -> str:
    """Run a Helm command and return stdout, raising RuntimeError on failure."""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout
