# Gunicorn configuration for production

bind = "0.0.0.0:5000"
workers = 2  # 2 workers for 2 CPU cores
threads = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process naming
proc_name = 'chemopad-flask'

# Server mechanics
daemon = False
pidfile = '/var/run/gunicorn/chemopad.pid'
user = None
group = None
tmp_upload_dir = None