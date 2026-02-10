import subprocess


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
