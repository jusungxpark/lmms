from __future__ import annotations

import json
import os
from typing import Any, Dict


SYSTEM_PROMPT = """
You are BeatBot Planner – an expert music producer and arranger controlling an automated DAW (LMMS) via a fixed command set.
Convert the user's natural-language request into a precise JSON plan. Infer tempo, bars, chord qualities, and instrumentation.

Use ONLY these commands:
- new_project: {path, template?}
- set_project: {path}
- set_bpm: {bpm}
- set_timesig: {numerator, denominator}
- add_sample_clip: {src, pos, len, track_index}
- add_midi_clip: {track_index, pos, len, name?}
- clear_notes: {track_index, clip_index?}
- add_notes: {track_index, clip_index?, notes:[{key,vol,pos,pan,len}]}
- replace_beats_with_chord: {track_index, start_pos, bars, root_key?, quality?, note_len?}
- generate_music: {provider, prompt, duration, out}
- synthesize_tone: {out, freq?, duration?, samplerate?}
- render: {out, format, samplerate, bitrate, loop?}

Guidelines:
- Chord requests (e.g., 'repeat a beautiful chord every beat') → add_midi_clip then replace_beats_with_chord.
- 'beautiful', 'lush', 'jazzy' → maj9; 'sad/dark' → min7; 'bluesy' → dom7; 'suspended' → sus2/sus4.
- If user says 'for the beat'/'every beat' use 1–2 bars.
- Default tempos: lofi 85, house 124, trap 140, jazz/beautiful 120; override if user gives BPM.
- Key mapping: if a key is given (C, F#, A minor), map to MIDI root around C4=60; otherwise use 60.
- End with render.

Output strictly JSON: {"commands": [...]}.
"""


class PromptPlanner:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2) -> None:
        self.model = model
        self.temperature = temperature

    def plan(self, prompt: str) -> Dict[str, Any]:
        # If OpenAI is available, use it; else fall back to a simple heuristic
        api_key = os.getenv("OPENAI_API_KEY")
        try:
            if api_key:
                import openai  # type: ignore

                client = openai.OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = completion.choices[0].message.content or "{}"
                return json.loads(content)
        except Exception:
            pass

        # Fallback heuristic plan with stronger musical parsing
        prompt_l = prompt.lower()

        def extract_bpm(default: int) -> int:
            import re
            m = re.search(r"(\d{2,3})\s*bpm", prompt_l)
            if m:
                return max(60, min(192, int(m.group(1))))
            m2 = re.search(r"\b(\d{2,3})\b", prompt_l)
            if m2 and any(w in prompt_l for w in ["bpm", "tempo", "beats per", "at"]):
                return max(60, min(192, int(m2.group(1))))
            return default

        def guess_bpm() -> int:
            if "lofi" in prompt_l:
                return 85
            if "house" in prompt_l or "edm" in prompt_l:
                return 124
            if "trap" in prompt_l:
                return 140
            if "jazz" in prompt_l or "beautiful" in prompt_l:
                return 120
            return 110

        def parse_bars(default_bars: int = 2) -> int:
            import re
            m = re.search(r"(\d+)\s*bars?", prompt_l)
            if m:
                return int(m.group(1))
            if "repeat itself for the beat" in prompt_l or "for the beat" in prompt_l or "every beat" in prompt_l:
                return 1
            return default_bars

        def parse_quality() -> str:
            if any(w in prompt_l for w in ["maj9", "beautiful", "lush", "jazzy", "dreamy"]):
                return "maj9"
            if any(w in prompt_l for w in ["maj7", "bright", "happy"]):
                return "maj7"
            if any(w in prompt_l for w in ["dom7", "dominant", "bluesy"]):
                return "dom7"
            if any(w in prompt_l for w in ["sad", "dark", "minor", "moody", "melancholy"]):
                return "min7"
            if "sus4" in prompt_l:
                return "sus4"
            if "sus2" in prompt_l:
                return "sus2"
            return "maj7"

        def parse_root_key(default_key: int = 60) -> int:
            # Map textual key names to MIDI near C4=60
            import re
            names = {
                "c": 60, "c#": 61, "db": 61, "d": 62, "d#": 63, "eb": 63, "e": 64, "f": 65, "f#": 66, "gb": 66,
                "g": 67, "g#": 68, "ab": 68, "a": 69, "a#": 70, "bb": 70, "b": 71
            }
            m = re.search(r"\b([a-g](?:#|b)?)(?:\s*(maj|major|min|minor|m))?\b", prompt_l)
            if not m:
                return default_key
            return names.get(m.group(1), default_key)

        # Special-case: chord replacement over beats
        if ("chord" in prompt_l) and ("beat" in prompt_l or "every beat" in prompt_l or "replace" in prompt_l or "repeat" in prompt_l):
            bpm = extract_bpm(guess_bpm())
            quality = parse_quality()
            bars = parse_bars(2)
            root_key = parse_root_key(60)
            return {
                "commands": [
                    {
                        "name": "new_project",
                        "args": {
                            "path": "build/beatbot/session.mmp",
                            "template": "tools/beatbot/templates/beatbot_template.mmp",
                        },
                    },
                    {"name": "set_bpm", "args": {"bpm": bpm}},
                    {"name": "set_timesig", "args": {"numerator": 4, "denominator": 4}},
                    {"name": "add_midi_clip", "args": {"track_index": 0, "pos": 0, "len": bars * 192, "name": "Chords"}},
                    {
                        "name": "replace_beats_with_chord",
                        "args": {"track_index": 0, "start_pos": 0, "bars": bars, "root_key": root_key, "quality": quality, "note_len": 36},
                    },
                    {
                        "name": "render",
                        "args": {
                            "out": "build/beatbot/mixdown",
                            "format": "wav",
                            "samplerate": 44100,
                            "bitrate": 192,
                        },
                    },
                ]
            }
        duration_s = 15 if "15" in prompt_l else 8
        bpm = extract_bpm(guess_bpm())

        have_eleven = bool(os.getenv("ELEVENLABS_API_KEY"))
        commands = [
            {
                "name": "new_project",
                "args": {
                    "path": "build/beatbot/session.mmp",
                    "template": "tools/beatbot/templates/beatbot_template.mmp",
                },
            },
            {"name": "set_bpm", "args": {"bpm": bpm}},
            {"name": "set_timesig", "args": {"numerator": 4, "denominator": 4}},
        ]

        # Stem generation and style-aware routing
        stems: Dict[str, Dict[str, str]] = {}
        out_dir = "build/beatbot/generated"
        if any(k in prompt_l for k in ["drum", "beat", "loop", "percussion", "kick", "snare", "hats"]):
            stems["drums"] = {"out": f"{out_dir}/drums.wav"}
        if any(k in prompt_l for k in ["bass", "walking bass", "jazzy"]):
            stems["bass"] = {"out": f"{out_dir}/bass.wav"}
        if not stems:
            stems["music"] = {"out": f"{out_dir}/music.wav"}

        track_index = 0
        for stem_name, meta in stems.items():
            out = meta["out"]
            if have_eleven:
                commands.append(
                    {
                        "name": "generate_music",
                        "args": {
                            "provider": "elevenlabs",
                            "prompt": f"{prompt} - {stem_name}",
                            "duration": min(duration_s, 12),
                            "out": out,
                        },
                    }
                )
            else:
                # Fast synth tone fallback: drums lower freq, bass mid freq
                freq = 110 if stem_name == "drums" else 220 if stem_name == "bass" else 330
                commands.append(
                    {
                        "name": "synthesize_tone",
                        "args": {
                            "out": out,
                            "freq": freq,
                            "duration": min(duration_s, 12),
                            "samplerate": 44100,
                        },
                    }
                )

            # If the prompt explicitly asks to program drums/bass inside MIDI, prefer algorithmic patterns
            if stem_name == "drums" and any(w in prompt_l for w in ["program", "pattern", "midi", "make a beat", "house", "trap", "lofi"]):
                commands.append({"name": "add_drum_pattern", "args": {"style": "house" if "house" in prompt_l else "trap" if "trap" in prompt_l else "lofi", "bars": 4, "start_pos": 0}})
            elif stem_name == "bass" and any(w in prompt_l for w in ["walking", "walking bass"]):
                commands.append({"name": "add_walking_bass", "args": {"root_key": 60, "bars": 2, "start_pos": 0}})
            else:
                commands.append(
                    {
                        "name": "add_sample_clip",
                        "args": {"src": out, "pos": 0, "len": 768, "track_index": track_index},
                    }
                )
            track_index += 1

        commands.append(
            {
                "name": "render",
                "args": {
                    "out": "build/beatbot/mixdown",
                    "format": "wav",
                    "samplerate": 44100,
                    "bitrate": 192,
                },
            }
        )

        return {"commands": commands}


