import os

if os.environ.get("ENV") == "dev":
    reload = True
    timeout = 100000
