import sys
import os

BACKEND = r"F:\\Projects\\Github Projects\\optionstrategy\\institutional_ai_trade_engine"
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from src.api.server import app  # noqa: E402
import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
