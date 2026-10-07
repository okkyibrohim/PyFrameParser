from __future__ import annotations

from flask import Blueprint
from pydantic import BaseModel

from pyframeparser import TextFrameResult

from .constants import (
    EXTENSION_CREDENTIALS,
    EXTENSION_PREDICTOR,
    EXTENSION_RATE_LIMITER,
)
from .errors import APIError
from .extensions import CredentialsStore, PredictorStore, RateLimiterStore

bp = Blueprint("routes", __name__)


@bp.route("/health", methods=["GET"])
def health_check():
    from flask import jsonify

    return jsonify({"status": "ok"}), 200


class TextParseRequest(BaseModel):
    text: str


class TextParseResponse(TextFrameResult):
    pass


@bp.route("/v1/parse", methods=["POST"])
def parse_text():
    try:
        from flask import current_app, jsonify, request

        try:
            body: TextParseRequest = TextParseRequest.parse_obj(request.get_json())
        except Exception as e:
            err = APIError(status_code=400, message=str(e))
            return (jsonify(err.to_dict()), 400)

        limiter: RateLimiterStore = current_app.extensions[EXTENSION_RATE_LIMITER]
        credentials: CredentialsStore = current_app.extensions[EXTENSION_CREDENTIALS]

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        counter = limiter.increment(token)

        valid, status_code = credentials.validate(token, counter)
        if not valid:
            err = APIError(status_code=status_code)
            return jsonify(err.to_dict()), status_code

        text: str = body.text

        predictor: PredictorStore = current_app.extensions[EXTENSION_PREDICTOR]
        result: TextFrameResult = predictor.parse(text)

        response = TextParseResponse.parse_obj(result.dict())

        return jsonify(response.dict()), 200
    except Exception as e:
        from flask import jsonify

        err = APIError(status_code=500, message=str(e))
        return jsonify(err.to_dict()), 500
