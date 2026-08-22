"""TTS implementation"""

import soundfile
from pathlib import Path
from kokoro import KPipeline

from .models import TTSConfig, TTSRequest
from .logging import get_logger

logger = get_logger(__name__)


class TTS:
    """TTS implementation"""

    def __init__(self, config: TTSConfig):
        """Initialize TTS class

        Args:
            config (TTSConfig): The TTS configuration
        """
        from kokoro import (
            KPipeline,
        )  # only import kokoro here for performance reasons, as it takes a while to load the module

        self.pipelines: dict[str, KPipeline] = {}
        self.config = config

        if not self.write_path.exists():
            self.write_path.mkdir(parents=True, exist_ok=True)
            
    def get_pipeline(self, lang_code: str) -> KPipeline:
        """Get the TTS pipeline for the given language code

        Args:
            lang_code (str): The language code for the TTS pipeline
        """
        if lang_code not in self.pipelines:
            self.pipelines[lang_code] = KPipeline(lang_code)

        return self.pipelines[lang_code]

    def generate(
        self,
        request: TTSRequest,
    ) -> Path:
        """Generate TTS audio from text and save to file

        Args:
            request (TTSRequest): The TTS request containing text, voice, speed, and sample rate

        Returns:
            Path: The path to the generated audio file
        """
        audio_path = self.write_path / f"{request.uuid}{self.config.file_extension}"

        logger.info(
            "Generating TTS for UUID: %s, text: %s, voice: %s, speed: %s, sample_rate: %s",
            request.uuid,
            request.text,
            request.voice,
            request.speed,
            request.sample_rate,
        )

        with soundfile.SoundFile(
            audio_path,
            mode="w",
            samplerate=request.sample_rate,
            channels=1,
        ) as file:
            for _, _, audio in self.get_pipeline(request.lang_code)(
                request.text, voice=request.voice, speed=request.speed,
            ):
                file.write(audio)  # type: ignore

        return audio_path

    @property
    def write_path(self) -> Path:
        """Get the path to write the generated audio files"""
        return self.config.write_path
