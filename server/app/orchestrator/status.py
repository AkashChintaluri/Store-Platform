"""
Store status checking utilities.

This module provides functions to check the readiness and status of deployed stores.
"""

import subprocess
from typing import Literal

from ..adapters import get_store_adapter


def get_store_password(
    namespace: str, 
    store_name: str, 
    engine: Literal["woocommerce", "medusa"]
) -> str | None:
    """
    Retrieve the admin password for a store using the appropriate adapter.
    
    Args:
        namespace: Kubernetes namespace
        store_name: Name of the store (Helm release name)
        engine: Store platform engine
        
    Returns:
        Optional[str]: Admin password or None if not available
    """
    adapter = get_store_adapter(engine)
    return adapter.get_admin_password(namespace, store_name)


# Backward compatibility - keep old function name for WooCommerce
def get_wordpress_password(namespace: str, store_name: str) -> str | None:
    """
    Legacy function for retrieving WordPress password.
    
    This is kept for backward compatibility. New code should use get_store_password().
    """
    return get_store_password(namespace, store_name, "woocommerce")



def namespace_ready(namespace: str) -> bool:
    cmd = [
        "kubectl",
        "get",
        "pods",
        "-n",
        namespace,
        "--no-headers",
    ]
    out = subprocess.check_output(cmd, text=True)

    for line in out.splitlines():
        if "woo-ready" in line:
            continue
        if "Running" not in line or "1/1" not in line:
            return False
    return True
    """Return True if the Kubernetes job has succeeded at least once."""
    cmd = [
        "kubectl",
        "get",
        "job",
        job_name,
        "-n",
        namespace,
        "-o",
        "jsonpath={.status.succeeded}",
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        return out not in ("", "0")
    except subprocess.CalledProcessError:
        return False


def job_failed_message(namespace: str, job_name: str) -> str | None:
    """Return the failure message for a job if it failed."""
    failed_cmd = [
        "kubectl",
        "get",
        "job",
        job_name,
        "-n",
        namespace,
        "-o",
        "jsonpath={.status.failed}",
    ]
    try:
        failed_out = subprocess.check_output(failed_cmd, text=True).strip()
    except subprocess.CalledProcessError:
        return None

    if failed_out in ("", "0"):
        return None

    message_cmd = [
        "kubectl",
        "get",
        "job",
        job_name,
        "-n",
        namespace,
        "-o",
        "jsonpath={.status.conditions[?(@.type==\"Failed\")].message}",
    ]

    try:
        return subprocess.check_output(message_cmd, text=True).strip() or "Job failed"
    except subprocess.CalledProcessError:
        return "Job failed"
