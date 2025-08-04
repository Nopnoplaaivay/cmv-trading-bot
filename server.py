import argparse
import uvicorn
from uvicorn.config import LOGGING_CONFIG
from backend.app import app

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-a", "--app", required=True, help="app name")
    ap.add_argument("-p", "--port", required=False, help="port", default="8000")
    ap.add_argument("-w", "--workers", required=False, help="number workers", default="1")
    args = vars(ap.parse_args())
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    uvicorn.run(args["app"], host="0.0.0.0", port=int(args["port"]), workers=int(args["workers"]))
