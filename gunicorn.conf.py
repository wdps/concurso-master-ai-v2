import os

bind = "0.0.0.0:" + os.environ.get("PORT", "5001")
workers = 2
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
