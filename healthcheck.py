"""Container health check for the TTS Unix socket server."""

import argparse
import json
import socket
import uuid


def main(target: str) -> int:
    request_id = str(uuid.uuid4())
    request = {"command": "ping", "uuid": request_id}

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(3)
            client.connect(target)
            client.sendall((json.dumps(request) + "\n").encode())

            response = b""
            while not response.endswith(b"\n"):
                chunk = client.recv(4096)
                if not chunk:
                    return 1
                response += chunk

        result = json.loads(response)
    except (OSError, ValueError):
        return 1

    return int(
        not (
            isinstance(result, dict)
            and result.get("command") == "ping"
            and result.get("ok") is True
            and result.get("uuid") == request_id
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        required=False,
        default="/data/tts.sock",
        help="Path to the Unix socket to check.",
    )
    args = parser.parse_args()
    raise SystemExit(main(target=args.target))
