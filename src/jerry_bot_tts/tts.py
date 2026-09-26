"""TTS implementation"""

from pathlib import Path
import wave
from piper import PiperVoice, SynthesisConfig

from .logging import get_logger
from .models import TTSConfig, TTSRequest

logger = get_logger(__name__)


class TTS:
    """TTS implementation"""

    def __init__(self, config: TTSConfig):
        """Initialize TTS class

        Args:
            config (TTSConfig): The TTS configuration
        """

        self.pipelines: dict[str, PiperVoice] = {}
        self.config = config

        if not self.write_path.exists():
            self.write_path.mkdir(parents=True, exist_ok=True)
            
    def find_voice(self, path: Path = Path()) -> Path:
        """Search for a voice file that matches"""
        
        for f in path.glob("*.onnx"):
            return f
        raise FileNotFoundError
            
    def get_voice(self, voice: str) -> PiperVoice:
        """Get the TTS pipeline for the given language code

        Args:
            lang_code (str): The language code for the TTS pipeline
        """
        if voice not in self.pipelines:
            self.pipelines[voice] = PiperVoice.load(self.find_voice())

        return self.pipelines[voice]

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
        voice = self.get_voice(request.voice)
        syn_config = SynthesisConfig(
            length_scale=(1.0 / request.speed),  # twice as slow
            noise_scale=1.0,  # more audio variation
            noise_w_scale=1.0,  # more speaking variation
            normalize_audio=False, # use raw audio from voice
        )

        logger.info(
            "Generating TTS for UUID: %s, text: %s, voice: %s, speed: %s, sample_rate: %s",
            request.uuid,
            request.text,
            request.voice,
            request.speed,
            request.sample_rate,
        )

        with wave.open(str(audio_path), "wb") as wav_file:
            voice.synthesize_wav(request.text, wav_file, syn_config=syn_config)

        return audio_path

    @property
    def write_path(self) -> Path:
        """Get the path to write the generated audio files"""
        return self.config.write_path
