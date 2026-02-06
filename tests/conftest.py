"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def reset_database_singleton():
    """Reset the global database singleton to ensure test isolation"""
    from app.storage import db as db_module

    db_module._db = None
