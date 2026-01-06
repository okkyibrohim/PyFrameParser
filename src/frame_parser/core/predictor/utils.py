import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple, Union, cast

from ..utils import Span
from .span_predictor import SpanPredictor


def load_frame_model(
    model_path: Union[str, Path],
    model_type: Literal["LOME"] = "LOME",
    gpu: int = -1,
) -> SpanPredictor:
    """
    Load frame parsing model.

    Args:
        model_path (Union[str, Path]): Path to the model file.
        model_type (Literal["LOME"], optional): Type of the model. Default is "LOME".
        gpu (int, optional): GPU device id. Default is -1 (CPU).

    Returns:
        SpanPredictor: Loaded frame parsing model.
    """
    if model_type == "LOME":
        predictor: SpanPredictor = SpanPredictor.from_path(
            str(model_path),
            cuda_device=gpu,
        )  # type: ignore
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    return predictor


@dataclass
class FrameParsingResult:
    text: str
    frame_list: List[Tuple[str, str]]
    frame_tree: List[Dict[str, Any]]

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def text_frame_parser(
    predictor: SpanPredictor,
    text: str,
) -> FrameParsingResult:
    result = predictor.predict_sentence(text)

    sentence: List[str] = result.sentence
    span: Span = cast(Span, result.span)
    frame_tree: List[Dict[str, Any]] = cast(
        List[Dict[str, Any]], span.to_json().get("children")
    )

    frame_list: List[Tuple[str, str]] = []
    for frame in frame_tree:
        # get the label name
        label = str(frame.get("label"))

        # get the span text
        span_text = ""
        start_span, end_span = frame.get("span", (None, None))
        if start_span and end_span:
            span_text = " ".join(sentence[start_span : end_span + 1])

        frame_list.append((label, span_text))

    return FrameParsingResult(
        text=text,
        frame_list=frame_list,
        frame_tree=frame_tree,
    )
