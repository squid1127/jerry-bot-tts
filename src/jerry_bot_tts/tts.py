"""TTS implementation"""

from kokoro import KPipeline
import soundfile
from pathlib import Path
import uuid

from .models import TTSConfig
from .logging import get_logger

logger = get_logger(__name__)

class TTS:
    """TTS implementation"""

    def __init__(self, write_path: Path, config: TTSConfig):
        """Initialize TTS class

        Args:
            write_path (Path): The path to write the generated audio files (directory)
            lang_code (str): The language code for TTS generation
        """
        self.write_path = write_path
        self.pipeline = KPipeline(lang_code=config.lang_code)
        self.config = config
        
        if not self.write_path.exists():
            self.write_path.mkdir(parents=True, exist_ok=True)

    def generate(self, text: str, voice: str, uuid: str, speed: float | None = None, sample_rate: int | None = None) -> Path:
        """Generate TTS audio from text and save to file

        Args:
            text (str): The text to convert to speech
            uuid (str): The UUID4 string to use for the output file name

        Returns:
            Path: The path to the generated audio file
        """
        audio_path = self.write_path / f"{uuid}{self.config.file_extension}"

        logger.info("Generating TTS for UUID: %s, text: %s, voice: %s, speed: %s, sample_rate: %s", uuid, text, voice, speed, sample_rate)
        
        with soundfile.SoundFile(audio_path, mode='w', samplerate=sample_rate or self.config.default_sample_rate, channels=1) as file:
            for _, _, audio in self.pipeline(text, voice=voice, speed=speed or self.config.default_speed):
                file.write(audio) #type: ignore
                
        return audio_path