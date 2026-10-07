import multiprocessing as mp

bind = "127.0.0.1:8000"
proc_name = "parser-app"

workers = 1  # hard requirement for direct model serving
worker_class = "gthread"
threads = mp.cpu_count() // 2

loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"  # stderr

# production settings
# accesslog = f"/var/log/{proc_name}/access.log"  # stdout
# errorlog = f"/var/log/{proc_name}/error.log"  # stderr
