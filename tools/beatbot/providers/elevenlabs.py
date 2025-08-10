from __future__ import annotations

import os
import time
import hashlib
from pathlib import Path
from typing import Optional
import requests


class ElevenLabsMusicProvider:
    """ElevenLabs Music Generation Provider

    Note: As of the hackathon, ElevenLabs Music API is in beta.
    This implementation uses their text-to-music endpoint.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.elevenlabs.io") -> None:
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path.home() / ".cache" / "beatbot" / "elevenlabs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, duration: float, outdir: Path) -> Path:
        """Generate music from text prompt

        Args:
            prompt: Text description of the music to generate
            duration: Duration in seconds (max 22 for ElevenLabs)
            outdir: Output directory for the generated file

        Returns:
            Path to the generated audio file
        """
        if not self.api_key:
            # Fallback to synthetic generation for demo
            return self._generate_fallback(prompt, duration, outdir)

        # Check cache first
        cache_key = self._get_cache_key(prompt, duration)
        cached_file = self.cache_dir / f"{cache_key}.mp3"

        if cached_file.exists():
            # Copy from cache to output directory
            output_path = outdir / f"elevenlabs_{cache_key[:8]}.mp3"
            import shutil
            shutil.copy2(cached_file, output_path)
            return output_path

        outdir.mkdir(parents=True, exist_ok=True)

        # Prepare the request
        url = f"{self.base_url}/v1/sound-generation"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Enhance prompt for better results
        enhanced_prompt = self._enhance_prompt(prompt)

        payload = {
            "text": enhanced_prompt,
            "duration_seconds": min(duration, 22),  # ElevenLabs max is 22 seconds
            "prompt_influence": 0.3,  # How much the prompt influences generation
        }

        try:
            # Make the API request
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                # Handle successful response
                output_path = outdir / f"elevenlabs_{cache_key[:8]}.mp3"

                # Check if response is JSON with audio URL or direct audio
                content_type = response.headers.get("content-type", "")

                if "application/json" in content_type:
                    data = response.json()

                    # Check for async generation (polling required)
                    if "generation_id" in data:
                        audio_url = self._poll_for_completion(data["generation_id"])
                        if audio_url:
                            audio_response = requests.get(audio_url, timeout=60)
                            audio_response.raise_for_status()
                            output_path.write_bytes(audio_response.content)
                    elif "audio_url" in data:
                        # Direct audio URL in response
                        audio_response = requests.get(data["audio_url"], timeout=60)
                        audio_response.raise_for_status()
                        output_path.write_bytes(audio_response.content)
                else:
                    # Direct audio bytes in response
                    output_path.write_bytes(response.content)

                # Cache the result
                if output_path.exists():
                    import shutil
                    shutil.copy2(output_path, cached_file)

                return output_path

            elif response.status_code == 429:
                # Rate limited - use fallback
                print(f"ElevenLabs rate limited, using fallback generation")
                return self._generate_fallback(prompt, duration, outdir)

            else:
                # API error - use fallback
                print(f"ElevenLabs API error {response.status_code}: {response.text}")
                return self._generate_fallback(prompt, duration, outdir)

        except requests.exceptions.RequestException as e:
            print(f"Network error with ElevenLabs: {e}")
            return self._generate_fallback(prompt, duration, outdir)

    def _poll_for_completion(self, generation_id: str, max_attempts: int = 30) -> Optional[str]:
        """Poll for async generation completion"""
        url = f"{self.base_url}/v1/sound-generation/{generation_id}"
        headers = {"xi-api-key": self.api_key}

        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "completed":
                        return data.get("audio_url")
                    elif data.get("status") == "failed":
                        print(f"Generation failed: {data.get('error')}")
                        return None
                time.sleep(2)  # Wait 2 seconds between polls
            except:
                pass

        return None

    def _enhance_prompt(self, prompt: str) -> str:
        """Enhance the prompt for better music generation"""
        prompt_lower = prompt.lower()

        # Add production quality hints
        enhancements = []

        if "drum" in prompt_lower or "beat" in prompt_lower:
            if "trap" in prompt_lower:
                enhancements.append("crisp 808 drums, rattling hi-hats")
            elif "house" in prompt_lower:
                enhancements.append("punchy four-on-the-floor kick, crisp claps")
            elif "lofi" in prompt_lower:
                enhancements.append("dusty vinyl drums, subtle swing")

        if "bass" in prompt_lower:
            if "sub" in prompt_lower or "808" in prompt_lower:
                enhancements.append("deep sub bass with smooth slides")
            elif "walking" in prompt_lower:
                enhancements.append("melodic walking bass line")

        if "melody" in prompt_lower or "lead" in prompt_lower:
            enhancements.append("catchy memorable melody, clear lead sound")

        # Add quality markers
        if not any(q in prompt_lower for q in ["quality", "professional", "studio"]):
            enhancements.append("professional studio quality")

        # Add tempo if not specified
        if "bpm" not in prompt_lower:
            if "trap" in prompt_lower:
                enhancements.append("140 BPM")
            elif "house" in prompt_lower:
                enhancements.append("124 BPM")
            elif "lofi" in prompt_lower:
                enhancements.append("85 BPM")

        enhanced = prompt
        if enhancements:
            enhanced = f"{prompt}, {', '.join(enhancements)}"

        return enhanced

    def _generate_fallback(self, prompt: str, duration: float, outdir: Path) -> Path:
        """Generate synthetic audio as fallback when API is unavailable"""
        outdir.mkdir(parents=True, exist_ok=True)

        # Use ffmpeg to generate a simple tone or drum pattern
        output_path = outdir / "fallback_generation.wav"

        # Determine what to generate based on prompt
        prompt_lower = prompt.lower()

        if "drum" in prompt_lower or "beat" in prompt_lower:
            # Generate a simple drum pattern using ffmpeg
            self._generate_drum_pattern(output_path, duration)
        elif "bass" in prompt_lower:
            # Generate a bass tone
            self._generate_bass_tone(output_path, duration)
        else:
            # Generate a simple melodic pattern
            self._generate_melody(output_path, duration)

        return output_path

    def _generate_drum_pattern(self, output_path: Path, duration: float) -> None:
        """Generate a simple drum pattern using ffmpeg"""
        import subprocess

        # Create a kick drum sound (low frequency sine wave burst)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=60:duration={duration}:sample_rate=44100",
            "-af", "aeval=val(0)*exp(-t*4):c=same",  # Exponential decay envelope
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If ffmpeg fails, create a simple sine wave
            self._create_simple_tone(output_path, 60, duration)

    def _generate_bass_tone(self, output_path: Path, duration: float) -> None:
        """Generate a bass tone"""
        import subprocess

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=110:duration={duration}:sample_rate=44100",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._create_simple_tone(output_path, 110, duration)

    def _generate_melody(self, output_path: Path, duration: float) -> None:
        """Generate a simple melody"""
        import subprocess

        # Create a simple ascending melody
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={duration}:sample_rate=44100",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._create_simple_tone(output_path, 440, duration)

    def _create_simple_tone(self, output_path: Path, frequency: float, duration: float) -> None:
        """Create a simple sine wave tone without external dependencies"""
        import struct
        import math

        sample_rate = 44100
        num_samples = int(sample_rate * duration)

        # Generate sine wave samples
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            sample = math.sin(2 * math.pi * frequency * t)
            # Apply simple envelope
            envelope = min(1.0, t * 10) * max(0, 1 - (t - duration + 0.1) * 10)
            samples.append(int(sample * envelope * 32767))

        # Write WAV file
        with open(output_path, "wb") as f:
            # WAV header
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + num_samples * 2))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack("<I", 16))  # fmt chunk size
            f.write(struct.pack("<H", 1))   # PCM
            f.write(struct.pack("<H", 1))   # Mono
            f.write(struct.pack("<I", sample_rate))
            f.write(struct.pack("<I", sample_rate * 2))  # Byte rate
            f.write(struct.pack("<H", 2))   # Block align
            f.write(struct.pack("<H", 16))  # Bits per sample
            f.write(b"data")
            f.write(struct.pack("<I", num_samples * 2))

            # Write samples
            for sample in samples:
                f.write(struct.pack("<h", sample))

    def _get_cache_key(self, prompt: str, duration: float) -> str:
        """Generate a cache key for the prompt and duration"""
        key_str = f"{prompt}_{duration}"
        return hashlib.md5(key_str.encode()).hexdigest()