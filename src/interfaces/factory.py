"""
Factory pattern for creating interface implementations.

This module provides a factory for creating appropriate interface implementations
based on the presentation layer being used (CLI, web API, GUI, etc.).
"""

from __future__ import annotations

from enum import Enum
from typing import Type

from .base import ConfigurationProvider, ErrorHandler, ProgressReporter, ResultHandler


class InterfaceType(Enum):
    """Supported interface types."""
    
    CLI = "cli"
    WEB = "web"
    GUI = "gui"
    LIBRARY = "library"


class InterfaceFactory:
    """Factory for creating interface implementations."""
    
    _config_providers: dict[InterfaceType, Type[ConfigurationProvider]] = {}
    _result_handlers: dict[InterfaceType, Type[ResultHandler]] = {}
    _progress_reporters: dict[InterfaceType, Type[ProgressReporter]] = {}
    _error_handlers: dict[InterfaceType, Type[ErrorHandler]] = {}
    
    @classmethod
    def register_configuration_provider(
        self, 
        interface_type: InterfaceType, 
        provider_class: Type[ConfigurationProvider]
    ) -> None:
        """Register a configuration provider for an interface type.
        
        Args:
            interface_type: The interface type to register for
            provider_class: The configuration provider class
        """
        self._config_providers[interface_type] = provider_class
    
    @classmethod
    def register_result_handler(
        self, 
        interface_type: InterfaceType, 
        handler_class: Type[ResultHandler]
    ) -> None:
        """Register a result handler for an interface type.
        
        Args:
            interface_type: The interface type to register for
            handler_class: The result handler class
        """
        self._result_handlers[interface_type] = handler_class
    
    @classmethod
    def register_progress_reporter(
        self, 
        interface_type: InterfaceType, 
        reporter_class: Type[ProgressReporter]
    ) -> None:
        """Register a progress reporter for an interface type.
        
        Args:
            interface_type: The interface type to register for
            reporter_class: The progress reporter class
        """
        self._progress_reporters[interface_type] = reporter_class
    
    @classmethod
    def register_error_handler(
        self, 
        interface_type: InterfaceType, 
        handler_class: Type[ErrorHandler]
    ) -> None:
        """Register an error handler for an interface type.
        
        Args:
            interface_type: The interface type to register for
            handler_class: The error handler class
        """
        self._error_handlers[interface_type] = handler_class
    
    @classmethod
    def create_configuration_provider(
        cls._error_handlers[interface_type] = handler_class
    
    @classmethod
    def create_configuration_provider(
        cls, 
        interface_type: InterfaceType, 
        *args, 
        **kwargs
    ) -> ConfigurationProvider:
        """Create a configuration provider for the given interface type.
        
        Args:
            interface_type: The interface type to create for
            *args: Arguments to pass to the provider constructor
            **kwargs: Keyword arguments to pass to the provider constructor
            
        Returns:
            A configuration provider instance
            
        Raises:
            KeyError: If no provider is registered for the interface type
        """
        if interface_type not in self._config_providers:
            raise KeyError(f"No configuration provider registered for {interface_type}")
        
        provider_class = self._config_providers[interface_type]
        return provider_class(*args, **kwargs)
    
    @classmethod
    def create_result_handler(
        self, 
        interface_type: InterfaceType, 
        *args, 
        **kwargs
    ) -> ResultHandler:
        """Create a result handler for the given interface type.
        
        Args:
            interface_type: The interface type to create for
            *args: Arguments to pass to the handler constructor
            **kwargs: Keyword arguments to pass to the handler constructor
            
        Returns:
            A result handler instance
            
        Raises:
            KeyError: If no handler is registered for the interface type
        """
        if interface_type not in self._result_handlers:
            raise KeyError(f"No result handler registered for {interface_type}")
        
        handler_class = self._result_handlers[interface_type]
        return handler_class(*args, **kwargs)
    
    @classmethod
    def create_progress_reporter(
        self, 
        interface_type: InterfaceType, 
        *args, 
        **kwargs
    ) -> ProgressReporter:
        """Create a progress reporter for the given interface type.
        
        Args:
            interface_type: The interface type to create for
            *args: Arguments to pass to the reporter constructor
            **kwargs: Keyword arguments to pass to the reporter constructor
            
        Returns:
            A progress reporter instance
            
        Raises:
            KeyError: If no reporter is registered for the interface type
        """
        if interface_type not in self._progress_reporters:
            raise KeyError(f"No progress reporter registered for {interface_type}")
        
        reporter_class = self._progress_reporters[interface_type]
        return reporter_class(*args, **kwargs)
    
    @classmethod
    def create_error_handler(
        self, 
        interface_type: InterfaceType, 
        *args, 
        **kwargs
    ) -> ErrorHandler:
        """Create an error handler for the given interface type.
        
        Args:
            interface_type: The interface type to create for
            *args: Arguments to pass to the handler constructor
            **kwargs: Keyword arguments to pass to the handler constructor
            
        Returns:
            An error handler instance
            
        Raises:
            KeyError: If no handler is registered for the interface type
        """
        if interface_type not in self._error_handlers:
            raise KeyError(f"No error handler registered for {interface_type}")
        
        if interface_type not in cls._error_handlers:
            raise KeyError(f"No error handler registered for {interface_type}")
        
        handler_class = cls._error_handlers[interface_type]
        return handler_class(*args, **kwargs)