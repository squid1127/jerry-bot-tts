# jerry-bot-tts

Helper for jerry-bot to provide a socket-based daemon to generate kokoro TTS as a child process.

Jerry voice: am_liam at 1.0 speed, 48000 sample rate.

## Installation

(Install as a standard git-backed Python package, using poetry or similar.)

## Run The Server

After install, run:

    poetry run jerry-bot-tts \
      --socket-path build/tts.sock \
      --write-path build/out \
      --lang-code a \
      --default-speed 1.0 \
      --default-sample-rate 24000 \
      --file-extension .wav

Arguments:

- --socket-path: Filesystem path to the Unix socket file.
- --write-path: Directory where generated audio files are written.
- --lang-code: Kokoro language code for the pipeline.
- --default-speed: Fallback speed when a request does not include speed.
- --default-sample-rate: Fallback sample rate when a request does not include sample_rate.
- --file-extension: Output file extension (example: .wav).

Show help:

    poetry run jerry-bot-tts --help

## Unix Socket Protocol (Simple Spec)

Transport:

- Unix domain stream socket (AF_UNIX).
- One JSON object per line (newline-delimited JSON).
- Client sends one request line.
- Server returns one response line.

Request JSON fields:

- uuid: string, required. Unique id for output naming/tracking.
- text: string, required. Text to synthesize.
- voice: string, required. Kokoro voice id (example: am_liam).
- speed: number, optional. Per-request speed override.
- sample_rate: integer, optional. Per-request sample rate override.

Response JSON fields:

- type: string. parse or generate.
- status: string. success or error.
- message: string. Human-readable status detail.
- uuid: string or null.
- filename: string or null.

Sample request:

    {"uuid":"593a5f37-b4ea-4437-8001-67945d26e566","text":"hello my name is jerry the octopus, here at your service!","voice":"am_liam","speed":1.0,"sample_rate":24000}

Sample socket call:

    echo '{"uuid":"593a5f37-b4ea-4437-8001-67945d26e566","text":"hello my name is jerry the octopus, here at your service!","voice":"am_liam","speed":1.0,"sample_rate":2400}' | socat - UNIX-CONNECT:build/tts.sock

Typical success response:

    {"type":"generate","status":"success","message":"TTS generated successfully","uuid":"593a5f37-b4ea-4437-8001-67945d26e566","filename":"593a5f37-b4ea-4437-8001-67945d26e566.wav"}

## sample_rate Behavior

sample_rate is resolved in this order:

1. Request sample_rate value, if provided.
2. CLI --default-sample-rate value, if request omits sample_rate.
3. Model default (currently 24000) if CLI value is not set.

This lets you set a global server default while still overriding rate on specific requests.
