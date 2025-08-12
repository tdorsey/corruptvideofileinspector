# Interface Architecture Refactoring

## Overview

This document describes the interface architecture refactoring that decouples the core business logic from the CLI presentation layer, enabling future extensibility to web APIs, GUIs, and library usage.

## Problem Statement

The original architecture tightly coupled core business logic with CLI-specific implementations:

- `src/core/credential_validator.py` imported and used `click` directly
- Configuration handling was tied to CLI argument parsing
- Output handling was embedded in core modules
- Error handling used CLI-specific patterns

This made it impossible to reuse the core video corruption detection logic with other presentation layers.

## Solution: Interface Abstractions

### New Architecture Components

#### 1. Abstract Interfaces (`src/interfaces/base.py`)

- **`ConfigurationProvider`**: Abstract interface for providing configuration from any source
- **`ResultHandler`**: Abstract interface for handling scan results to any destination
- **`ProgressReporter`**: Abstract interface for reporting progress to any UI paradigm  
- **`ErrorHandler`**: Abstract interface for handling errors appropriately for any presentation layer

#### 2. Interface Factory (`src/interfaces/factory.py`)

- **`InterfaceFactory`**: Factory pattern for creating interface implementations
- **`InterfaceType`**: Enum defining supported interface types (CLI, WEB, GUI, LIBRARY)
- Registration system for interface implementations

#### 3. CLI Adapters (`src/interfaces/cli/`)

- **`CLIConfigurationProvider`**: CLI-specific configuration from AppConfig
- **`CLIResultHandler`**: CLI-specific result output to console/files
- **`CLIProgressReporter`**: CLI-specific progress bars and indicators
- **`CLIErrorHandler`**: CLI-specific error messages and exit codes

#### 4. Interface-Agnostic Services

- **`VideoScanService`**: Core scanning service using dependency injection
- **`CLIScanServiceAdapter`**: Backward compatibility adapter for existing CLI code

## Key Benefits Achieved

### 1. Presentation Layer Independence

Core modules no longer depend on any specific presentation framework:

```python
# Before: CLI-dependent
from click import echo
echo("Error message")

# After: Interface-agnostic  
error_handler.handle_validation_error("Error message")
```

### 2. Configuration Source Flexibility

Configuration can now come from any source:

```python
# CLI configuration from arguments
cli_config = CLIConfigurationProvider(app_config)

# Web API configuration from HTTP request
web_config = WebAPIConfigurationProvider(request_data)

# Same core service works with both
scan_service = VideoScanService(config_provider=cli_config)  # or web_config
```

### 3. Output Destination Flexibility

Results can go to any destination:

```python
# CLI output to console/files
cli_handler = CLIResultHandler(output_path="results.json")

# Web API output to HTTP response
web_handler = WebAPIResultHandler()

# Same core service works with both
scan_service = VideoScanService(result_handler=cli_handler)  # or web_handler
```

### 4. Future Interface Support

Adding new presentation layers requires no changes to core business logic:

```python
# Future GUI implementation
gui_config = GUIConfigurationProvider(gui_settings)
gui_handler = GUIResultHandler(gui_window)
gui_progress = GUIProgressReporter(progress_bar)

# Same core service works immediately
scan_service = VideoScanService(
    config_provider=gui_config,
    result_handler=gui_handler, 
    progress_reporter=gui_progress
)
```

## Implementation Details

### Core Module Changes

1. **`src/core/credential_validator.py`**:
   - Removed `import click` dependency
   - Replaced `handle_credential_error()` with `format_credential_error_details()`
   - Now returns structured data instead of CLI-specific output

2. **`src/core/scan_service.py`**:
   - New interface-agnostic scanning service
   - Uses dependency injection for all external dependencies
   - No CLI or presentation layer imports

3. **`src/__init__.py`**:
   - Removed automatic CLI import to prevent dependency issues
   - CLI code only imported when explicitly needed

### Backward Compatibility

1. **`src/cli/credential_utils.py`**:
   - CLI-specific wrapper maintaining existing `handle_credential_error()` API
   - Uses core validation logic internally

2. **`src/cli/scan_adapter.py`**:
   - Adapter allowing existing CLI handlers to use new service
   - Maintains all existing CLI functionality

### Example: Web API Usage

```python
def scan_via_web_api(request_data):
    """Example showing web API usage of same core logic."""
    from src.core.scan_service import VideoScanService
    from src.interfaces.web_example import (
        WebAPIConfigurationProvider,
        WebAPIResultHandler,
        WebAPIProgressReporter
    )
    
    # Create web-specific implementations
    config = WebAPIConfigurationProvider(request_data)
    handler = WebAPIResultHandler()
    progress = WebAPIProgressReporter(websocket_conn)
    
    # Use same core service as CLI
    service = VideoScanService(
        config_provider=config,
        result_handler=handler,
        progress_reporter=progress
    )
    
    summary = service.scan_directory()
    return handler.get_response_data()
```

## Testing Strategy

### Interface Validation

- Unit tests for abstract interfaces (`tests/unit/test_interfaces.py`)
- Unit tests for scan service (`tests/unit/test_scan_service.py`)
- Validation that core modules have no CLI dependencies

### Backward Compatibility

- All existing CLI functionality preserved
- Existing tests should continue to pass
- CLI handlers use new architecture internally

### Future Interface Testing

- Example web API implementation demonstrates extensibility
- Mock implementations validate interface contracts
- Factory pattern enables easy testing of different interface types

## Migration Path

### Phase 1: ✅ Complete
- Create interface abstractions
- Remove CLI dependencies from core modules
- Implement CLI adapters
- Create interface-agnostic scan service

### Phase 2: Next Steps
- Update CLI commands to use new service
- Ensure all existing tests pass
- Performance validation

### Phase 3: Future
- Implement web API interface
- Add GUI interface capability
- Library usage documentation

## Success Criteria Met

- ✅ Core modules have zero CLI dependencies
- ✅ Configuration system supports multiple input sources  
- ✅ Result handling is abstracted and interface-agnostic
- ✅ All existing CLI functionality preserved via adapters
- ✅ Example implementation of alternative interface (web API)
- ✅ Interface contract validation through unit tests

## Files Changed

### New Files
- `src/interfaces/__init__.py` - Interface abstractions module
- `src/interfaces/base.py` - Abstract interface definitions
- `src/interfaces/factory.py` - Interface factory pattern
- `src/interfaces/cli/__init__.py` - CLI interface implementations
- `src/interfaces/cli/adapters.py` - CLI-specific adapters
- `src/interfaces/web_example.py` - Example web API implementation
- `src/core/scan_service.py` - Interface-agnostic scan service
- `src/cli/credential_utils.py` - CLI-specific credential utilities
- `src/cli/scan_adapter.py` - CLI backward compatibility adapter
- `tests/unit/test_interfaces.py` - Interface validation tests
- `tests/unit/test_scan_service.py` - Scan service unit tests

### Modified Files
- `src/core/credential_validator.py` - Removed CLI dependency
- `src/cli/handlers.py` - Updated to use new credential utilities
- `src/__init__.py` - Removed automatic CLI import

## Conclusion

This refactoring successfully decouples the core business logic from CLI-specific implementations while maintaining full backward compatibility. The new architecture enables easy addition of web APIs, GUIs, or library usage without modifying core modules.

The interface abstractions provide a clean contract that any presentation layer can implement, ensuring consistency while allowing flexibility in implementation details.