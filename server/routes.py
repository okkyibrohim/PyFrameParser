from typing import Any, Dict

from flask import Blueprint

from .extensions import CredentialsStore, PredictorStore, RateLimiterStore

bp = Blueprint("routes", __name__)


class APIError(Exception):
    def __init__(self, status_code: int = 400):
        # hardcode message for simplicity
        if status_code == 401:
            message = "Unauthorized"
        elif status_code == 429:
            message = "Too Many Requests"
        else:
            message = "Bad Request"

        super().__init__(message)

        self.message = message
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.message}


@bp.route("/health", methods=["GET"])
def health_check():
    from flask import jsonify

    return jsonify({"status": "ok"}), 200


@bp.route("/v1/parse", methods=["POST"])
def parse_text():
    from flask import Response, current_app, jsonify, request

    limiter: RateLimiterStore = current_app.extensions["RATE_LIMITER"]
    credentials: CredentialsStore = current_app.extensions["CREDENTIALS"]

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    counter = limiter.increment(token)

    valid, code = credentials.validate(token, counter)
    if not valid:
        return jsonify(APIError(status_code=code).to_dict()), code

    data = request.get_json()
    text: str = data.get("text", "")

    predictor: PredictorStore = current_app.extensions["PREDICTOR"]
    result = predictor.parse(text)

    return Response(result.to_json(), mimetype="application/json"), 200
