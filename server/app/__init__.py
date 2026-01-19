from pathlib import Path
from typing import Union

from flask import Flask

from .config import Config as AppConfig
from .config import load_config
from .extensions import register_extensions
from .routes import bp


def create_app(config_path: Union[Path, str]) -> Flask:
    app = Flask(__name__)

    app_config: AppConfig = load_config(config_path)
    app.config.from_object(app_config)

    # register extensions
    register_extensions(app)

    # register routes
    app.register_blueprint(bp)

    return app
