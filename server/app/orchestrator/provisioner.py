"""
This module provisions and deletes stores using Helm.

Responsibilities:
- Translate store metadata into Helm values
- Call Helm install / uninstall
- Configure WooCommerce via wp-cli
- Be safe to retry (idempotent)
- Do NOT talk to MongoDB directly
"""

import os
import subprocess
import tempfile
from pathlib import Path

import yaml

from .helm import run_helm


CHART_PATH = str(Path(__file__).resolve().parents[3] / "charts" / "store")
DEFAULT_VALUES_FILE = str(Path(__file__).resolve().parents[3] / "charts" / "store" / "values.yaml")
PROD_VALUES_FILE = str(Path(__file__).resolve().parents[3] / "charts" / "store" / "values-prod.yaml")


def get_values_file() -> str:
    env_values_file = os.getenv("STORE_VALUES_FILE", "").strip()
    if env_values_file:
        return env_values_file
    environment = os.getenv("APP_ENV", "development").lower()
    return PROD_VALUES_FILE if environment == "production" else DEFAULT_VALUES_FILE


def generate_values(store_name: str, host: str) -> str:
    """
    Generate a temporary Helm values file for a store.
    Returns path to the temp file.
    """
    values = {
        "store": {
            "name": store_name,
            "host": host,
        },
        "ingress": {
            "enabled": True,
            "className": "nginx",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml", encoding="utf-8") as tmp:
        yaml.safe_dump(values, tmp)
        return tmp.name


def install_store(store_name: str, namespace: str, values_file: str | None = None):
    """
    Install or upgrade a store Helm release.
    """
    values_file = values_file or get_values_file()
    cmd = [
        "helm",
        "upgrade",
        "--install",
        store_name,
        CHART_PATH,
        "--namespace",
        namespace,
        "--create-namespace",
        "-f",
        values_file,
    ]
    return run_helm(cmd)


def delete_store(store_name: str, namespace: str):
    """
    Delete a store and all Kubernetes resources.
    """
    cmd = [
        "helm",
        "uninstall",
        store_name,
        "-n",
        namespace,
    ]
    return run_helm(cmd)


def configure_woocommerce(namespace: str, release_name: str) -> tuple[bool, str | None]:
    """
    Configure WooCommerce in the WordPress pod using wp-cli.
    Returns (success, error_message).
    """
    # Find the WordPress pod
    get_pod_cmd = [
        "kubectl",
        "get",
        "pods",
        "-n",
        namespace,
        "-l",
        f"app.kubernetes.io/name=wordpress,app.kubernetes.io/instance={release_name}",
        "-o",
        "jsonpath={.items[0].metadata.name}",
    ]
    try:
        pod_name = subprocess.check_output(get_pod_cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if not pod_name:
            return False, "WordPress pod not found"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to find WordPress pod: {e}"
    
    # Check if WordPress core is installed
    check_cmd = [
        "kubectl",
        "exec",
        "-n",
        namespace,
        pod_name,
        "--",
        "bash",
        "-c",
        "cd /opt/bitnami/wordpress && wp core is-installed --allow-root",
    ]
    try:
        subprocess.check_output(check_cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False, "WordPress core not installed"
    
    # Install/activate WooCommerce
    woo_cmd = [
        "kubectl",
        "exec",
        "-n",
        namespace,
        pod_name,
        "--",
        "bash",
        "-c",
        "cd /opt/bitnami/wordpress && "
        "(wp plugin is-installed woocommerce --allow-root || wp plugin install woocommerce --activate --allow-root) && "
        "(wp plugin is-active woocommerce --allow-root || wp plugin activate woocommerce --allow-root)",
    ]
    try:
        subprocess.check_output(woo_cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install/activate WooCommerce: {e}"
    
    # Create test product if none exist
    product_cmd = [
        "kubectl",
        "exec",
        "-n",
        namespace,
        pod_name,
        "--",
        "bash",
        "-c",
        "cd /opt/bitnami/wordpress && "
        "PRODUCTS=$(wp post list --post_type=product --format=ids --allow-root) && "
        "[[ -z \"$PRODUCTS\" ]] && wp wc product create --name='Test Product' --type=simple --status=publish --regular_price='10.00' --user=1 --allow-root || true",
    ]
    try:
        subprocess.check_output(product_cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        return False, f"Failed to create product: {e}"
    
    # Enable COD payment
    cod_cmd = [
        "kubectl",
        "exec",
        "-n",
        namespace,
        pod_name,
        "--",
        "bash",
        "-c",
        "cd /opt/bitnami/wordpress && "
        "wp wc payment_gateway update cod --enabled=true --user=1 --allow-root",
    ]
    try:
        subprocess.check_output(cod_cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        return False, f"Failed to enable COD: {e}"
    
    return True, None