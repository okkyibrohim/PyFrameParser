from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Union

from yaml import safe_load


@dataclass
class PredictorConfig:
    model_path: str
    model_type: Literal["LOME"] = "LOME"
    gpu: int = -1


@dataclass
class CredentialsConfig:
    credentials_path: str
    ttl: int = 300


@dataclass
class APIConfig:
    ttl: int = 300


@dataclass
class Config:
    PREDICTOR: PredictorConfig
    CREDENTIALS: CredentialsConfig
    API: APIConfig

    def to_dict(self) -> dict:
        return asdict(self)


def load_config(path: Union[str, Path]) -> Config:
    with Path(path).open("r") as f:
        config_dict = safe_load(f)

    predictor_cfg = PredictorConfig(**config_dict.get("predictor", {}))
    credentials_cfg = CredentialsConfig(**config_dict.get("credentials", {}))
    api_cfg = APIConfig(**config_dict.get("api", {}))

    return Config(
        PREDICTOR=predictor_cfg,
        CREDENTIALS=credentials_cfg,
        API=api_cfg,
    )
