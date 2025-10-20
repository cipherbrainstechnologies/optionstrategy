import sys, os
from uvicorn import run

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from src.api.server import app

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8000)
