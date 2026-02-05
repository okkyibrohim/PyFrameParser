import tempfile

from pathlib import Path

from app import create_app

# force tmp dir
tempfile.tempdir = "/home/admin/tmp"

CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"

# run with: gunicorn -c gunicorn.config.py wsgi:app
app = create_app(CONFIG_PATH)

# run with: python wsgi.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
