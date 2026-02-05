from pathlib import Path
from typing import Union

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

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

    # apply middleware
    app.wsgi_app = ProxyFix(  # ty:ignore[invalid-assignment]
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
        x_prefix=1,
    )

    return app
