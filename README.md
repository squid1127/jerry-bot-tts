# jerry-bot-tts

`jerry-bot-tts` is a Unix socket daemon that converts text to speech with the Kokoro TTS pipeline. It is intended to run as a child process of jerry-bot or another application that needs a small local TTS service. Each request writes one audio file to disk and receives a JSON response containing its filename.

## Installation

The package requires Python 3.11 or 3.12. Install it with Poetry:

```sh
poetry install
```

Kokoro also needs its normal runtime assets and dependencies available in the
selected Python environment.

## Configuration and startup

Start the daemon with the two required configuration values:

```sh
poetry run jerry-bot-tts \
  --socket-path build/tts.sock \
  --write-path build/out
```

The command-line options are generated from `TTSConfig`:

| Option             | Required | Default | Description                                                                                                    |
| ------------------ | -------- | ------- | -------------------------------------------------------------------------------------------------------------- |
| `--socket-path`    | Yes      | None    | Filesystem path for the Unix domain socket. An existing socket at this path is removed when the server starts. |
| `--write-path`     | Yes      | None    | Directory where generated audio files are written. It is created if necessary.                                 |
| `--file-extension` | No       | `.wav`  | Extension used when naming generated files.                                                                    |

Inspect the available options with:

```sh
poetry run jerry-bot-tts --help
```

The process keeps running until it receives `SIGINT` or `SIGTERM`. On shutdown,
it removes the socket file it created.

## Unix socket protocol

The service uses a Unix domain stream socket (`AF_UNIX`) with newline-delimited
JSON:

1. Connect to the configured socket path.
2. Send one JSON request followed by `\\n`.
3. Read one response line.
4. Repeat steps 2 and 3, or close the connection.

### Request

`TTSRequest` has three required fields and three optional fields:

| Field         | Type    | Default | Description                                                                         |
| ------------- | ------- | ------- | ----------------------------------------------------------------------------------- |
| `uuid`        | string  | None    | Unique request id. It is also used as the output filename stem.                     |
| `text`        | string  | None    | Text to synthesize.                                                                 |
| `voice`       | string  | None    | Kokoro voice id, such as `am_liam`.                                                 |
| `speed`       | number  | `1.0`   | Speech speed for this request.                                                      |
| `sample_rate` | integer | `24000` | Output sample rate in Hz.                                                           |
| `lang_code`   | string  | `a`     | Kokoro pipeline language code, such as `a` for American English or `e` for Spanish. |

For example:

```json
{
  "uuid": "593a5f37-b4ea-4437-8001-67945d26e566",
  "text": "Hello, I am Jerry.",
  "voice": "am_liam",
  "speed": 1.0,
  "sample_rate": 24000,
  "lang_code": "a"
}
```

`speed`, `sample_rate`, and `lang_code` are request properties, not daemon
startup options. Omitting them uses the defaults shown above.

### Response

Every valid request receives a `TTSResponse`:

| Field      | Type           | Description                                                            |
| ---------- | -------------- | ---------------------------------------------------------------------- |
| `type`     | string         | `generate` for synthesis results, or `parse` for invalid request data. |
| `status`   | string         | `success` or `error`.                                                  |
| `message`  | string         | Human-readable result or error detail.                                 |
| `uuid`     | string or null | Request id when it could be identified.                                |
| `filename` | string or null | Generated filename on success; otherwise `null`.                       |

A successful response looks like this:

```json
{
  "type": "generate",
  "status": "success",
  "message": "TTS generated successfully",
  "uuid": "593a5f37-b4ea-4437-8001-67945d26e566",
  "filename": "593a5f37-b4ea-4437-8001-67945d26e566.wav"
}
```

The complete path is `write_path / filename`. A malformed JSON line or a
request that fails validation returns an error response with `type` set to
`parse`; a failure during synthesis returns `type` `generate` and includes the
request UUID when available.

## Example client

The following client sends one request and reads the server response. The
newline is required because the server processes one JSON object per line.

```python
import json
import socket
import uuid


socket_path = "build/tts.sock"
request = {
    "uuid": str(uuid.uuid4()),
    "text": "Hello, I am Jerry.",
    "voice": "am_liam",
    "speed": 1.0,
    "sample_rate": 24000,
    "lang_code": "a",
}

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
    client.connect(socket_path)
    client.sendall((json.dumps(request) + "\n").encode())
    response = b""
    while not response.endswith(b"\n"):
        response += client.recv(4096)

print(json.loads(response))
```

After a successful response, read the audio from `build/out/<filename>` (or
from the configured `--write-path`). The client should treat a response with
`status: "error"` as a failed synthesis and inspect its `message` field.

## Command-line smoke test

With the daemon running, `socat` can be used to send a request manually:

```sh
printf '%s\n' '{"uuid":"593a5f37-b4ea-4437-8001-67945d26e566","text":"Hello, I am Jerry.","voice":"am_liam","speed":1.0,"sample_rate":24000,"lang_code":"a"}' \
  | socat - UNIX-CONNECT:build/tts.sock
```

## Jerry Voice

It has been decided that the voice of "Jerry" will be as follows:

- Voice: `am_liam`
- Speed: `1.0`
- Language code: `a` (American English)
- Sample rate: `44000` Hz (double the default resulting in 2x playback speed)
