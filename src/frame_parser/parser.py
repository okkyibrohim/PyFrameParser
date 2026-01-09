from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple, Union, cast

from allennlp.predictors import Predictor

from .predictor import SpanPredictor
from .utils import Span


@dataclass
class TextFrameResult:
    text: str
    frame_list: List[Tuple[str, str]]
    frame_tree: List[Dict[str, Any]]

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FrameParser:
    """
    Frame parsing utility class that provides methods to load frame parsing models
    and parse text to extract frame information.
    """

    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    @classmethod
    def load_frame_model(
        cls,
        model_path: Union[str, Path],
        model_type: Literal["LOME"] = "LOME",
        gpu: int = -1,
    ) -> FrameParser:
        """
        Load frame parsing model.

        Args:
            model_path (Union[str, Path]): Path to the model file.
            model_type (Literal["LOME"], optional): Type of the model. Default is "LOME".
            gpu (int, optional): GPU device id. Default is -1 (CPU).

        Returns:
            FrameParser: An instance of FrameParser with the loaded model.
        """
        if model_type == "LOME":
            predictor = SpanPredictor.from_path(
                str(model_path),
                cuda_device=gpu,
            )  # type: ignore

            return cls(predictor)

        raise ValueError(f"Unsupported model type: {model_type}")

    def text_frame_parser(
        self,
        text: str,
    ) -> TextFrameResult:
        if not isinstance(self.predictor, SpanPredictor):
            raise ValueError(
                f"Predictor model {type(self.predictor)} is not supported."
            )

        result = self.predictor.predict_sentence(text)

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

        return TextFrameResult(
            text=text,
            frame_list=frame_list,
            frame_tree=frame_tree,
        )
