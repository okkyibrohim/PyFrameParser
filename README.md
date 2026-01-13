# PyFrameParser

A Python Frame Parser Wrapper

## Frame Semantic Parser

This package provides a library for Frame Semantic Parsing.
Currently, its only support LOME frame semantic parser.

The frame parsing capability also available via HTTP API at ...

## Installation

To install the package, use pip:

```bash
pip install pyframeparser
```

As currently the package only support LOME implementation that requires Python 3.8, no other versions are supported at this time.  
It is recommended to use a virtual environment for installation.

## Usage

Here is a simple example of how to use the Frame Parser in your Python code:

```python
from pyframeparser import FrameParser, TextFrameResult

parser: FrameParser = FrameParser.load_frame_model(
    model_path="path/to/model/model.tar.gz",
    model_type="LOME", # optional, default to LOME
    gpu=-1, # optional, default to -1 (CPU only)
)

result: TextFrameResult = parser.text_frame_parser("input text to be parsed")
print(result)
```

## HTTP API Usage

The API is free to use for research purposes, but requires an API token.  
Please contact [muhammadokky@ut.ee](mailto:muhammadokky@ut.ee) to request access using an academic email (and CC your supervisor if you are a university student).

To use the Frame Parser via HTTP API, you can make a request to the following endpoint:

### POST /v1/parse

This endpoint accepts a JSON payload with the following structure:

```bash
curl -X POST http://localhost:8000/v1/parse \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer {TOKEN}" \
    -d '{"text": "input text to be parsed"}'
```

The response will contain the parsed frame semantic information in JSON format:

```json
{
    "text": "input text to be parsed",
    "frame_list": [
        [
            "FrameName1",
            "text"
        ]
    ],
    "frame_tree": [
        {
            "label": "FrameName1",
            "span": [2, 2],
            "confidence": 1.0,
            "children": [
                {
                    "label": "FrameChildName1",
                    "span": [3, 5],
                    "confidence": 0.9999394416809082,
                    "children": []
                }
            ]
        }
    ]
}
```

## Citation

If you use this library in your research, please cite the following paper:

```latex
@inproceedings{xia-etal-2021-lome,
    title = "{LOME}: Large Ontology Multilingual Extraction",
    author = "Xia, Patrick  and
      Qin, Guanghui  and
      Vashishtha, Siddharth  and
      Chen, Yunmo  and
      Chen, Tongfei  and
      May, Chandler  and
      Harman, Craig  and
      Rawlins, Kyle  and
      White, Aaron Steven  and
      Van Durme, Benjamin",
    editor = "Gkatzia, Dimitra  and
      Seddah, Djam{\'e}",
    booktitle = "Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations",
    month = apr,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.eacl-demos.19/",
    doi = "10.18653/v1/2021.eacl-demos.19",
    pages = "149--159",
    abstract = "We present LOME, a system for performing multilingual information extraction. Given a text document as input, our core system identifies spans of textual entity and event mentions with a FrameNet (Baker et al., 1998) parser. It subsequently performs coreference resolution, fine-grained entity typing, and temporal relation prediction between events. By doing so, the system constructs an event and entity focused knowledge graph. We can further apply third-party modules for other types of annotation, like relation extraction. Our (multilingual) first-party modules either outperform or are competitive with the (monolingual) state-of-the-art. We achieve this through the use of multilingual encoders like XLM-R (Conneau et al., 2020) and leveraging multilingual training data. LOME is available as a Docker container on Docker Hub. In addition, a lightweight version of the system is accessible as a web demo."
}
```

## Acknowledgements

- @okkyibrohim
- @fgarnadi

## License

This project is licensed under the terms of [Apache 2.0 License](LICENSE).
