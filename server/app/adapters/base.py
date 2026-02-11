"""
Base adapter interface for store platforms.

This module defines the abstract interface that all store platform adapters must implement.
This enables type erasure - the orchestrator works with the StoreAdapter interface without
knowing the concrete platform implementation.
"""

from abc import ABC, abstractmethod
from typing import Optional


class StoreAdapter(ABC):
    """
    Abstract base class for store platform adapters.
    
    Each e-commerce platform (WooCommerce, Medusa, etc.) must implement this interface
    to provide platform-specific provisioning, configuration, and status checking.
    """
    
    @abstractmethod
    def get_chart_dependency(self) -> dict:
        """
        Get the Helm chart dependency configuration for this platform.
        
        Returns:
            dict: Helm chart dependency specification with name, version, repository, etc.
        """
        pass
    
    @abstractmethod
    def get_default_values(self, store_name: str, host: str) -> dict:
        """
        Generate platform-specific Helm values.
        
        Args:
            store_name: Name of the store
            host: Hostname for the store
            
        Returns:
            dict: Platform-specific Helm values
        """
        pass
    
    @abstractmethod
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        """
        Perform post-deployment configuration for the platform.
        
        This is called after the Helm chart is deployed and pods are ready.
        For example, WooCommerce needs plugin installation and product setup.
        
        Args:
            namespace: Kubernetes namespace
            release_name: Helm release name
            
        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        """
        Retrieve the admin password for the store.
        
        Args:
            namespace: Kubernetes namespace
            release_name: Helm release name
            
        Returns:
            Optional[str]: Admin password or None if not available
        """
        pass
    
    @abstractmethod
    def get_pod_selector(self, release_name: str) -> str:
        """
        Get the Kubernetes label selector for the main application pod.
        
        Args:
            release_name: Helm release name
            
        Returns:
            str: Label selector string (e.g., "app.kubernetes.io/name=wordpress")
        """
        pass
    
    @abstractmethod
    def get_store_url_path(self) -> str:
        """
        Get the URL path suffix for the store frontend.
        
        Returns:
            str: URL path (e.g., "/shop/" for WooCommerce, "/" for Medusa)
        """
        pass
    
    @abstractmethod
    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        """
        Check if the platform is fully initialized and ready.
        
        This goes beyond pod readiness - it checks if the application itself is ready.
        For example, checking if WordPress core is installed.
        
        Args:
            namespace: Kubernetes namespace
            release_name: Helm release name
            
        Returns:
            bool: True if platform is ready, False otherwise
        """
        pass
