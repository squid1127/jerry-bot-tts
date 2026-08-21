"""Pydantic models"""

from pydantic import BaseModel, Field, ValidationError


class TTSConfig(BaseModel):
    """TTS configuration model"""

    lang_code: str = Field(..., description="Language code for TTS", examples=["a"])
    default_speed: float = Field(
        1.0, description="Default speed for TTS", examples=[1.0]
    )
    default_sample_rate: int = Field(
        24000, description="Sample rate for audio output", examples=[24000]
    )
    file_extension: str = Field(
        ".wav", description="File extension for audio output", examples=[".wav"]
    )


class TTSRequest(BaseModel):
    """TTS request model"""

    uuid: str = Field(
        ...,
        description="UUID4 string for the request",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(..., description="Voice to use for TTS.")
    speed: float | None = Field(
        None,
        description="Speed of the generated speech. If None, the default speed will be used.",
        examples=[1.0, None],
    )
    sample_rate: int | None = Field(
        None,
        description="Sample rate of the generated audio. If None, the default sample rate will be used.",
        examples=[24000, None],
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
