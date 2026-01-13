from pathlib import Path
from typing import Any, Dict, List, Literal, Union

import pandas as pd

from pyframeparser import FrameParser, TextFrameResult


def parse(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    model_path: Union[str, Path] = "lome-en-spanbert-large",
    model_type: Literal["LOME"] = "LOME",
    gpu: int = -1,
    column_to_parse: str = "text",
):
    # load texts from input file
    input_path = Path(input_path)
    if input_path.suffix == ".jsonl":
        try:
            texts = pd.read_json(input_path, lines=True, orient="records")[
                column_to_parse
            ].tolist()
        except Exception as e:
            raise ValueError(f"Error reading JSONL file: {e}")
    elif input_path.suffix == ".csv":
        try:
            texts = pd.read_csv(input_path, usecols=[column_to_parse])[
                column_to_parse
            ].tolist()
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    else:
        raise ValueError(
            "Unsupported input file format. Please provide a .jsonl or .csv file."
        )

    parser: FrameParser = FrameParser.load_frame_model(
        model_path=model_path,
        model_type=model_type,
        gpu=gpu,
    )

    # parse and collect results
    records: List[Dict[str, Any]] = []
    for text in texts:
        result: TextFrameResult = parser.text_frame_parser(text)
        records.append(result.to_dict())

    results = pd.DataFrame.from_records(records)

    # save results to output file
    output_path = Path(output_path)
    if output_path.suffix == ".jsonl":
        results.to_json(output_path, lines=True, orient="records")
    elif output_path.suffix == ".csv":
        results.to_csv(output_path, index=False)
    else:
        raise ValueError(
            "Unsupported output file format. Please provide a .jsonl or .csv file."
        )
