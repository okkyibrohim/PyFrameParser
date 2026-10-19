# PyFrameParser

A Python Frame Parser Wrapper

## Frame Semantic Parser

This package provides a library for frame semantic parsing. It currently
supports the LOME frame parser.

Frame parsing is also available through the [deployed HTTP API](API_USAGE.md).

## Installation

To install the package, use pip:

```bash
pip install pyframeparser
```

The package requires Python 3.8. Use a virtual environment for installation.

## Development setup from this repository

The `pip install` command above installs the published package;
use [uv](https://docs.astral.sh/uv/getting-started/installation/) and `uv.lock`
for this checkout. Python 3.8 is required by `pyproject.toml`.

For library imports, linting, or work against the
[deployed API](API_USAGE.md), only the Python environment is needed. Running
inference locally also needs the model, a spaCy English pipeline, and enough
memory. Our WSL guest with 7.6 GiB RAM and 2 GiB swap was killed while loading
the model on CPU. **16 GiB RAM is a suggested starting point**, not a tested
minimum. A GPU is optional; the commands below use CPU (`gpu: -1`). Allow
at least 30 GB of free disk space for the Docker image, extracted model, and
Python environment.

### 1. Install the Python environment

Install uv, then run:

```bash
uv python install 3.8
uv sync --locked --all-packages --dev
uv run --no-sync python -c "import pyframeparser; print(pyframeparser.__version__)"
uv pip check --python .venv/bin/python
```

`uv sync` creates `.venv` and installs the library, the server's dependencies,
and the development tools from `uv.lock`. Point your editor at
`.venv/bin/python`, or run `source .venv/bin/activate` to use the environment
in a shell. On Linux, a C/C++ build toolchain may be needed for dependencies
without compatible wheels.

Run the configured linter with `uv run --no-sync ruff check .`. At the time of
writing, it reports two existing `E722` findings in
`src/pyframeparser/data_reader/better_reader.py`. There is no automated test
suite in this checkout; the import and dependency checks above verify the
environment, not parsing accuracy.

### 2. Install the English tokenizer pipeline

`SpanPredictor` loads spaCy's `en_core_web_sm` at startup. Install the
[official spaCy 3.3.0 pipeline](https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.3.0),
which is compatible with the spaCy 3.3.x version in this environment:

```bash
uv pip install --python .venv/bin/python \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.3.0/en_core_web_sm-3.3.0-py3-none-any.whl
.venv/bin/python -c "import spacy; spacy.load('en_core_web_sm'); print('spaCy model OK')"
```

The pipeline is an extra download outside `uv.lock`. If you later run
`uv sync`, install it again before local inference. Use `uv run --no-sync` or
`.venv/bin/python` for commands that need it.

### 3. Obtain the official LOME model

[JHU releases LOME as a Docker image](https://nlp.jhu.edu/demos/), not as a
standalone model download. The official
[`hltcoe/lome` image](https://hub.docker.com/r/hltcoe/lome) contains the
FrameNet parser archive and its XLM-RoBERTa encoder. On WSL, enable Docker
Desktop's WSL integration or use a Docker Engine available to the distro.
With Docker available,
copy the files out of the image. Creating the container does not run the model
and does not require a GPU. The digest pins the official image used for this
guide:

```bash
LOME_IMAGE=hltcoe/lome@sha256:b024f3b41c84acbe7892f4c7c7adb0cf4662fcb08c2e86e29575ea7644a3e416
docker pull "$LOME_IMAGE"
docker create --name lome-model "$LOME_IMAGE"
mkdir -p model/xlm-roberta-large
docker cp lome-model:/opt/models/spanfinder/model.tar.gz model/official-model.tar.gz
for file in config.json pytorch_model.bin sentencepiece.bpe.model tokenizer.json; do
  docker cp "lome-model:/opt/models/xlm-roberta-large/$file" model/xlm-roberta-large/
done
docker rm lome-model
```

The original archive refers to `/opt/models/xlm-roberta-large`, a path inside
the container. Create a copy with both encoder references updated to this
checkout's `model/xlm-roberta-large` directory. The model weights are copied
without modification:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import io
import json
import tarfile

root = Path('model').resolve()
encoder = str(root / 'xlm-roberta-large')
with tarfile.open(str(root / 'official-model.tar.gz'), 'r|gz') as source, \
     tarfile.open(str(root / 'model.tar.gz'), 'w|gz', compresslevel=1) as target:
    for member in source:
        contents = source.extractfile(member) if member.isfile() else None
        if member.name == 'config.json':
            config = json.load(contents)
            config['dataset_reader']['pretrained_model'] = encoder
            config['model']['word_embedding']['token_embedders']['pieces']['model_name'] = encoder
            data = (json.dumps(config, indent=2) + '\n').encode()
            member.size = len(data)
            contents = io.BytesIO(data)
        target.addfile(member, contents)
PY
```

Check the resulting archive and local tokenizer without loading model weights:

```bash
tar -tzf model/model.tar.gz | tail -5
.venv/bin/python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('model/xlm-roberta-large', local_files_only=True); print('XLM-R tokenizer OK')"
```

The archive should include `config.json`, `vocabulary/`, and `weights.th`.
`model/` is Git-ignored. Recreate `model/model.tar.gz` if you move the checkout,
because its encoder paths are absolute.

### 4. Run the local server

The tracked `server/config/config.yaml` and `server/wsgi.py` contain paths from
another machine. Create local configuration and a local-only test credential
inside the ignored `model/` directory instead:

```bash
cat > model/creds.csv <<'CSV'
name,email,token,limit
Local Developer,local@example.invalid,local-dev-token,-1
CSV

cat > model/server-config.yaml <<EOF
predictor:
  model_path: "$(pwd)/model/model.tar.gz"
  model_type: LOME
  gpu: -1
credentials:
  credentials_path: "$(pwd)/model/creds.csv"
  ttl: 10
api:
  ttl: 10
EOF

(cd server && ../.venv/bin/gunicorn -c gunicorn.config.py --threads 1 \
  'app:create_app("../model/server-config.yaml")')
```

The server binds to `127.0.0.1:8000` with one worker, as set in
`server/gunicorn.config.py`. Model loading happens before `/health` responds;
wait for startup to finish, then test from another terminal:

```bash
curl --fail-with-body --show-error http://127.0.0.1:8000/health
curl --fail-with-body --show-error http://127.0.0.1:8000/v1/parse \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer local-dev-token' \
  -d '{"text":"John gave Mary a book."}'
```

Stop Gunicorn with Ctrl+C. The example token is for a server bound to localhost;
set a private token before exposing a server to other users. If the process is
killed while loading the model, check available RAM and swap. The 7.6 GiB RAM
plus 2 GiB swap WSL environment used for this guide ran out of memory before
inference, so a successful local parse has not been verified here.

## Usage

Here is a simple example of how to use the Frame Parser in your Python code:

```python
from pyframeparser import FrameParser, TextFrameResult

parser: FrameParser = FrameParser.load_frame_model(
    model_path="model/model.tar.gz",  # from the repository root
    model_type="LOME", # optional, default to LOME
    gpu=-1, # optional, default to -1 (CPU only)
)

result: TextFrameResult = parser.text_frame_parser("input text to be parsed")
print(result)
```

## HTTP API Usage

The [local server instructions](#4-run-the-local-server) include a copyable
request using the local test token. For the deployed service, its token access,
and a Python client example, see the [API usage guide](API_USAGE.md).

A successful `/v1/parse` response has this JSON structure; actual labels and
scores depend on the input and model:

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

- [@okkyibrohim](https://github.com/okkyibrohim)
- [@fgarnadi](https://github.com/fgarnadi)
- [@mohamadarvin25](https://github.com/mohamadarvin25)
- [@kimnzh](https://github.com/kimnzh)

## License

This project is licensed under the terms of [Apache 2.0 License](LICENSE).
