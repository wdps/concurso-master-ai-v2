﻿import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
