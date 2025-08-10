from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Music theory constants
class Genre(Enum):
    HOUSE = "house"
    TECHNO = "techno"
    TRAP = "trap"
    DNB = "dnb"
    DUBSTEP = "dubstep"
    LOFI = "lofi"
    JAZZ = "jazz"
    POP = "pop"
    EDM = "edm"
    HIPHOP = "hiphop"
    AMBIENT = "ambient"

# BPM ranges for genres
GENRE_BPM = {
    Genre.HOUSE: (120, 128),
    Genre.TECHNO: (120, 140),
    Genre.TRAP: (140, 170),
    Genre.DNB: (160, 180),
    Genre.DUBSTEP: (140, 145),
    Genre.LOFI: (70, 90),
    Genre.JAZZ: (110, 130),
    Genre.POP: (100, 130),
    Genre.EDM: (120, 135),
    Genre.HIPHOP: (80, 100),
    Genre.AMBIENT: (60, 100),
}

# Chord progressions (in Roman numerals)
PROGRESSIONS = {
    "pop": ["I", "V", "vi", "IV"],  # C-G-Am-F
    "jazz": ["ii", "V", "I"],  # Dm-G-C
    "blues": ["I", "IV", "V"],  # C-F-G
    "emotional": ["vi", "IV", "I", "V"],  # Am-F-C-G
    "edm": ["i", "VI", "III", "VII"],  # Am-F-C-G
    "trap": ["i", "iv", "i", "v"],  # Am-Dm-Am-Em
}

# Enhanced system prompt for GPT-5
SYSTEM_PROMPT_V2 = """
You are BeatBot Planner v2 – an expert music producer with deep knowledge of electronic music production.
Your task is to convert natural language into precise LMMS DAW commands, optimizing for viral potential.

Commands Available:
- new_project: {path, template?}
- set_bpm: {bpm}
- set_timesig: {numerator, denominator}
- add_sample_clip: {src, pos, len, track_index}
- add_midi_clip: {track_index, pos, len, name?}
- add_notes: {track_index, clip_index?, notes:[{key,vol,pos,pan,len}]}
- replace_beats_with_chord: {track_index, start_pos, bars, root_key?, quality?, note_len?}
- add_drum_pattern: {style, bars, start_pos}
- add_bass_pattern: {style, root_key, bars, start_pos}
- add_melody_pattern: {style, scale, bars, start_pos}
- set_instrument: {track_index, plugin, name?}
- add_effect: {track_index, effect, params?}
- generate_music: {provider, prompt, duration, out}
- export_tiktok: {audio, out, cover?, duration?}
- render: {out, format, samplerate, bitrate}

Music Production Rules:
1. Structure: Intro (8 bars) → Buildup (8 bars) → Drop (16 bars) → Breakdown (8 bars) → Outro (8 bars)
2. Energy: Build tension with filters, risers, and automation before drops
3. Catchiness: Repeat hooks every 8 bars, use call-and-response patterns
4. Sidechaining: Apply compression to bass/pads triggered by kick for pump effect
5. Layering: Stack sounds (sub+mid+high) for fullness
6. Space: Use reverb/delay for depth, but keep kick/bass dry

Routing Strategy:
- FAST (<100ms): Drums, bass, simple patterns → use add_drum_pattern, add_bass_pattern
- THINKING (>1s): Melodies, complex harmonies → use generate_music provider
- Balance speed and quality based on user intent

Output JSON: {"commands": [...], "metadata": {"genre": "...", "vibe": "...", "viral_score": 0-10}}
"""

class EnhancedPlanner:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3) -> None:
        self.model = model
        self.temperature = temperature

    def detect_genre(self, text: str) -> Optional[Genre]:
        """Detect genre from user text"""
        text_lower = text.lower()
        for genre in Genre:
            if genre.value in text_lower:
                return genre
        # Check for related terms
        if any(w in text_lower for w in ["4 on the floor", "four on floor", "dance"]):
            return Genre.HOUSE
        if any(w in text_lower for w in ["aggressive", "hard", "industrial"]):
            return Genre.TECHNO
        if any(w in text_lower for w in ["808", "hi-hat", "rattling"]):
            return Genre.TRAP
        if any(w in text_lower for w in ["break", "amen", "jungle"]):
            return Genre.DNB
        if any(w in text_lower for w in ["wobble", "drop", "heavy"]):
            return Genre.DUBSTEP
        if any(w in text_lower for w in ["chill", "relaxed", "study"]):
            return Genre.LOFI
        return None

    def get_optimal_bpm(self, genre: Optional[Genre], text: str) -> int:
        """Get optimal BPM for genre or extract from text"""
        # Check if BPM is explicitly mentioned
        import re
        bpm_match = re.search(r"(\d{2,3})\s*bpm", text.lower())
        if bpm_match:
            return max(60, min(200, int(bpm_match.group(1))))

        # Use genre-specific BPM
        if genre and genre in GENRE_BPM:
            min_bpm, max_bpm = GENRE_BPM[genre]
            return (min_bpm + max_bpm) // 2

        return 120  # Default

    def create_drum_pattern(self, style: str, bars: int = 4) -> Dict[str, Any]:
        """Create genre-specific drum patterns"""
        patterns = {
            "house": {
                "kick": [0, 48, 96, 144],  # 4-on-floor
                "clap": [48, 144],  # 2 and 4
                "hihat": [24, 72, 120, 168],  # Off-beats
            },
            "trap": {
                "kick": [0, 72, 144],  # Syncopated
                "snare": [48, 144],
                "hihat": list(range(0, 192, 12)),  # Rapid 16ths with variations
            },
            "dnb": {
                "kick": [0, 132],  # Broken beat
                "snare": [48, 144],
                "hihat": [0, 24, 48, 72, 96, 120, 144, 168],
            },
            "dubstep": {
                "kick": [0],
                "snare": [48],
                "hihat": [24, 72, 120],
            },
            "lofi": {
                "kick": [0, 96],
                "snare": [48, 120],
                "hihat": [0, 24, 48, 72, 96, 120, 144, 168],
            },
        }
        return patterns.get(style, patterns["house"])

    def create_bass_pattern(self, style: str, root_key: int = 36) -> List[Dict[str, int]]:
        """Create genre-specific bass patterns"""
        patterns = {
            "house": [  # Driving octave bass
                {"key": root_key, "pos": 0, "len": 24, "vel": 100},
                {"key": root_key + 12, "pos": 24, "len": 24, "vel": 90},
                {"key": root_key, "pos": 48, "len": 24, "vel": 100},
                {"key": root_key + 12, "pos": 72, "len": 24, "vel": 90},
            ],
            "trap": [  # 808 slides
                {"key": root_key, "pos": 0, "len": 48, "vel": 120},
                {"key": root_key - 2, "pos": 48, "len": 24, "vel": 100},
                {"key": root_key, "pos": 72, "len": 72, "vel": 110},
            ],
            "dnb": [  # Reese bass
                {"key": root_key, "pos": 0, "len": 96, "vel": 100},
                {"key": root_key + 7, "pos": 96, "len": 48, "vel": 90},
                {"key": root_key + 5, "pos": 144, "len": 48, "vel": 95},
            ],
        }
        return patterns.get(style, patterns["house"])

    def should_use_fast_generation(self, element: str) -> bool:
        """Determine if we should use fast (algorithmic) generation"""
        fast_elements = ["drum", "drums", "beat", "kick", "snare", "hat", "hihat",
                        "percussion", "rhythm", "groove", "loop"]
        return any(f in element.lower() for f in fast_elements)

    def plan(self, prompt: str) -> Dict[str, Any]:
        """Create an optimized plan for music generation"""
        # Try GPT-5 first if available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_V2},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = completion.choices[0].message.content or "{}"
                return json.loads(content)
            except Exception as e:
                print(f"GPT-5 planning failed, using enhanced fallback: {e}")

        # Enhanced fallback planning
        return self.create_fallback_plan(prompt)

    def create_fallback_plan(self, prompt: str) -> Dict[str, Any]:
        """Create a sophisticated fallback plan without GPT-5"""
        prompt_lower = prompt.lower()

        # Detect genre and parameters
        genre = self.detect_genre(prompt)
        bpm = self.get_optimal_bpm(genre, prompt)

        # Determine duration
        duration = 15  # Default for TikTok
        if "30" in prompt:
            duration = 30
        elif "8" in prompt:
            duration = 8
        elif "minute" in prompt:
            duration = 60

        # Build command sequence
        commands = []

        # Project setup
        commands.append({
            "name": "new_project",
            "args": {
                "path": "build/beatbot/session.mmp",
                "template": "tools/beatbot/templates/beatbot_template.mmp",
            }
        })
        commands.append({"name": "set_bpm", "args": {"bpm": bpm}})

        # Determine what to create
        track_index = 0

        # Add drums if mentioned or implied
        if any(w in prompt_lower for w in ["drum", "beat", "rhythm", "groove"]) or genre:
            style = genre.value if genre else "house"
            commands.append({
                "name": "add_drum_pattern",
                "args": {"style": style, "bars": 4, "start_pos": 0}
            })
            track_index += 3  # Drums use 3 tracks (kick, snare, hats)

        # Add bass if mentioned
        if any(w in prompt_lower for w in ["bass", "sub", "low"]):
            style = genre.value if genre else "house"
            commands.append({
                "name": "add_bass_pattern",
                "args": {"style": style, "root_key": 36, "bars": 4, "start_pos": 0}
            })
            track_index += 1

        # Add melody if mentioned
        if any(w in prompt_lower for w in ["melody", "lead", "synth", "tune"]):
            commands.append({
                "name": "add_melody_pattern",
                "args": {"style": "catchy", "scale": "minor", "bars": 4, "start_pos": 0}
            })
            track_index += 1

        # Add chords if mentioned
        if any(w in prompt_lower for w in ["chord", "harmony", "pad"]):
            quality = "min7" if "sad" in prompt_lower else "maj7"
            commands.append({
                "name": "add_midi_clip",
                "args": {"track_index": track_index, "pos": 0, "len": 768, "name": "Chords"}
            })
            commands.append({
                "name": "replace_beats_with_chord",
                "args": {
                    "track_index": track_index,
                    "start_pos": 0,
                    "bars": 4,
                    "root_key": 60,
                    "quality": quality,
                    "note_len": 48
                }
            })
            track_index += 1

        # If no specific elements mentioned, create a default beat
        if track_index == 0:
            commands.extend([
                {"name": "add_drum_pattern", "args": {"style": "house", "bars": 4, "start_pos": 0}},
                {"name": "add_bass_pattern", "args": {"style": "house", "root_key": 36, "bars": 4, "start_pos": 0}}
            ])

        # Render
        commands.append({
            "name": "render",
            "args": {
                "out": "build/beatbot/mixdown",
                "format": "wav",
                "samplerate": 44100,
                "bitrate": 192
            }
        })

        # Export to TikTok if mentioned
        if "tiktok" in prompt_lower or "viral" in prompt_lower:
            commands.append({
                "name": "export_tiktok",
                "args": {
                    "audio": "build/beatbot/mixdown.wav",
                    "out": "build/beatbot/tiktok.mp4",
                    "duration": duration
                }
            })

        # Calculate viral score based on characteristics
        viral_score = 5
        if genre in [Genre.HOUSE, Genre.TRAP, Genre.POP]:
            viral_score += 2
        if "catchy" in prompt_lower or "viral" in prompt_lower:
            viral_score += 2
        if duration <= 15:
            viral_score += 1

        return {
            "commands": commands,
            "metadata": {
                "genre": genre.value if genre else "electronic",
                "bpm": bpm,
                "duration": duration,
                "viral_score": min(10, viral_score),
                "vibe": "energetic" if bpm > 120 else "chill"
            }
        }

# Backwards compatibility
PromptPlanner = EnhancedPlanner