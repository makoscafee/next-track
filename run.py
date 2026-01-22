#!/usr/bin/env python
"""
NextTrack API - Application Entry Point
"""

import os

from app import create_app

# Get configuration from environment or default to development
config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.getenv("PORT", 5000))
    debug = config_name == "development"

    print(f"Starting NextTrack API in {config_name} mode")
    print(f"Running on http://localhost:{port}")

    app.run(host="0.0.0.0", port=port, debug=debug)
