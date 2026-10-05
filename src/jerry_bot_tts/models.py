"""Pydantic models"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError


class TTSCommand(Enum):
    """TTS command enumeration"""

    PING = "ping"
    CLEAN = "clean"

class TTSConfig(BaseModel):
    """TTS configuration model"""

    socket_path: Path = Field(
        ..., description="Path to the Unix socket for TTS requests"
    )
    write_path: Path = Field(
        ..., description="Directory to write the generated audio files"
    )
    max_concurrent_requests: int = Field(
        5, description="Maximum number of concurrent TTS requests", examples=[1, 5, 10]
    )

    file_extension: str = Field(
        ".wav", description="File extension for audio output", examples=[".wav"]
    )
    
class TTSCommandRequest(BaseModel):
    """TTS command request model"""

    command: TTSCommand = Field(
        ..., description="Command to execute", examples=[TTSCommand.PING, TTSCommand.CLEAN]
    )
    uuid: str = Field(
        ...,
        description="UUID4 string for the command request. This is used to identify the response.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

class TTSCommandResponse(BaseModel):
    """TTS command response model"""

    command: TTSCommand = Field(
        ..., description="Command that was executed", examples=[TTSCommand.PING, TTSCommand.CLEAN]
    )
    ok: bool = Field(
        ..., description="Indicates if the command was executed successfully", examples=[True, False]
    )
    uuid: str = Field(
        ...,
        description="UUID4 string for the command response. This is used to identify the response.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    message: str | None = Field(
        None,
        description="Optional message describing the result of the command execution",
        examples=["Command executed successfully", "Failed to execute command"],
    )
    
    def to_json_bytes(self) -> bytes:
        """Convert the TTSCommandResponse instance to JSON-encoded bytes

        Returns:
            bytes: The JSON-encoded bytes representing the TTS command response
        """
        return self.model_dump_json().encode()


class TTSRequest(BaseModel):
    """TTS request model"""

    uuid: str = Field(
        ...,
        description="UUID4 string for the request. This is used to uniquely identify the request and the generated audio file.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    text: str = Field(
        ...,
        description="Text to convert to speech. This should be preprocessed to remove any unwanted characters or formatting.",
    )
    voice: str = Field(
        ...,
        description="Voice to use for TTS. Refer to the documentation for a list of supported voices.",
    )
    speed: float = Field(
        1.0,
        description="Speed of the generated speech.",
        examples=[1.0, 0.5, 2.0],
    )
    sample_rate: int = Field(
        24000,
        description="Sample rate of the generated audio. Note that this changes the playback speed/pitch of the audio. To sound normal, it should be 24000.",
        examples=[24000, 44100, 48000],
    )
    lang_code: str = Field(
        "a",
        description="Language code for the TTS pipeline. This is used to select the correct language for a given voice. The default is 'a', which is American English. Refer to the documentation for a list of supported language codes.",
        examples=["a", "b", "j", "e"],
    )

    @classmethod
    def from_json_bytes(cls, data: bytes) -> "TTSRequest":
        """Create a TTSRequest instance from JSON-encoded bytes

        Args:
            data (bytes): The JSON-encoded bytes representing the TTS request

        Returns:
            TTSRequest: The TTSRequest instance
        """
        try:
            return cls.model_validate_json(data)
        except ValidationError as e:
            raise ValueError(f"Invalid TTS request data: {e}") from e

    def to_json_bytes(self) -> bytes:
        """Convert the TTSRequest instance to JSON-encoded bytes

        Returns:
            bytes: The JSON-encoded bytes representing the TTS request
        """
        return self.model_dump_json().encode()


class TTSResponse(BaseModel):
    """TTS response model"""

    type: str = Field(..., description="Type of the response", examples=["ack"])
    status: str = Field(
        ..., description="Status of the TTS request", examples=["success", "error"]
    )
    message: str = Field(
        ..., description="Message describing the result of the TTS request"
    )
    uuid: str | None = Field(
        None,
        description="UUID of the generated audio file, if applicable",
        examples=["123e4567-e89b-12d3-a456-426614174000", None],
    )
    filename: str | None = Field(
        None,
        description="Filename of the generated audio file, if applicable",
        examples=["123e4567-e89b-12d3-a456-426614174000.wav", None],
    )

    def to_json_bytes(self) -> bytes:
        """Convert the TTSResponse instance to JSON-encoded bytes

        Returns:
            bytes: The JSON-encoded bytes representing the TTS response
        """
        return self.model_dump_json().encode()

    @classmethod
    def from_json_bytes(cls, data: bytes) -> "TTSResponse":
        """Create a TTSResponse instance from JSON-encoded bytes

        Args:
            data (bytes): The JSON-encoded bytes representing the TTS response

        Returns:
            TTSResponse: The TTSResponse instance
        """
        try:
            return cls.model_validate_json(data)
        except ValidationError as e:
            raise ValueError(f"Invalid TTS response data: {e}") from e
