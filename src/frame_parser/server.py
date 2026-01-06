from pathlib import Path

from frame_parser.app import create_app


def run_server(host="127.0.0.1", port=8000):
    app = create_app(Path(__file__).parent / "app" / "config.yaml")
    app.run(host=host, port=port)


if __name__ == "__main__":
    run_server()
