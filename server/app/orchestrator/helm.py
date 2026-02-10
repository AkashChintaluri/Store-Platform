"""
You are writing a Helm execution utility for a FastAPI-based orchestrator.

Requirements:
- Run Helm commands using subprocess (no Helm SDK)
- Capture stdout/stderr
- Raise clear Python exceptions on failure
- Support install, upgrade, uninstall
- Be synchronous (async not required)
- Assume Helm is installed on the host
- Do NOT hardcode namespaces or values

Design choices:
- Helm is the source of truth
- subprocess keeps behavior identical to CLI
"""

import subprocess


def run_helm(cmd: list[str]) -> str:
    """
    Run a Helm command and return stdout.
    Raise RuntimeError with stderr on failure.
    """
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout