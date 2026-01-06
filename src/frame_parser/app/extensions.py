import csv
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Literal, Tuple, TypedDict, Union

from flask import Flask

from frame_parser.core import SpanPredictor
from frame_parser.core.predictor import (
    FrameParsingResult,
    load_frame_model,
    text_frame_parser,
)

from .config import APIConfig, CredentialsConfig, PredictorConfig


class Credential(TypedDict):
    name: str
    email: str
    limit: int


class CredentialsStore:
    def __init__(self, path: Union[str, Path], ttl: int = 300):
        self.path = Path(path)
        self.ttl = ttl
        self._lock = threading.Lock()
        self._last_load = 0
        self._last_mtime = 0

        self.credentials = self._load_credentials()

    @classmethod
    def init_app(cls, app: Flask):
        cfg: CredentialsConfig = app.config["CREDENTIALS"]
        app.extensions["CREDENTIALS"] = cls(
            path=cfg.credentials_path,
            ttl=cfg.ttl,
        )

    def _load_credentials(self) -> Dict[str, Credential]:
        credentials: Dict[str, Credential] = {}

        with self.path.open("r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                credentials[row["token"]] = Credential(
                    name=row["name"],
                    email=row["email"],
                    limit=int(row["limit"]),
                )

        return credentials

    def validate(self, token: str, counter: int) -> Tuple[int, int]:
        with self._lock:
            try:
                mtime = self.path.stat().st_mtime
            except FileNotFoundError:
                mtime = 0

            now = time.time()
            should_reload = (
                now - self._last_load > self.ttl or mtime != self._last_mtime
            )

            if should_reload:
                self.credentials = self._load_credentials()
                self._last_load = now
                self._last_mtime = mtime

            if token not in self.credentials:
                return False, 401  # Unauthorized

            creds = self.credentials[token]
            if counter > creds["limit"] and creds["limit"] != -1:
                return False, 429  # Too Many Requests

            return True, 200  # OK


class PredictorStore:
    def __init__(
        self,
        model_path: Union[str, Path],
        model_type: Literal["LOME"] = "LOME",
        gpu: int = -1,
    ):
        self.model_path = Path(model_path)
        self.model_type = model_type
        self.gpu = gpu
        self.model: SpanPredictor = self._load_model()

    @classmethod
    def init_app(cls, app: Flask):
        cfg: PredictorConfig = app.config["PREDICTOR"]
        app.extensions["PREDICTOR"] = cls(
            model_path=cfg.model_path,
            model_type=cfg.model_type,
            gpu=cfg.gpu,
        )

    def _load_model(self):
        return load_frame_model(
            model_path=self.model_path,
            model_type=self.model_type,  # type: ignore
            gpu=self.gpu,
        )

    def parse(self, text: str) -> FrameParsingResult:
        return text_frame_parser(self.model, text)


class RateLimiterStore:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl

        self._lock = threading.Lock()
        self._token_counts: Dict[str, int] = defaultdict(int)
        self._token_timestamps: Dict[str, float] = defaultdict(float)

    @classmethod
    def init_app(cls, app: Flask):
        cfg: APIConfig = app.config["API"]
        app.extensions["RATE_LIMITER"] = cls(ttl=cfg.ttl)

    def increment(self, token: str) -> int:
        with self._lock:
            now = time.time()
            if now - self._token_timestamps[token] > self.ttl:
                self._token_counts[token] = 0
                self._token_timestamps[token] = now

            self._token_counts[token] += 1

            return self._token_counts[token]


def register_extensions(app: Flask):
    # register predictor
    PredictorStore.init_app(app)

    # register credentials
    CredentialsStore.init_app(app)

    # register rate limiter
    RateLimiterStore.init_app(app)
