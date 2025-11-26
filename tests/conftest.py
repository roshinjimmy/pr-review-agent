"""Pytest configuration and fixtures."""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variable for testing
os.environ["OPENROUTER_API_KEY"] = "test-key-for-unit-tests"
