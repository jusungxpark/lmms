from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .project import LmmsProject


@dataclass
class Command:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


class CommandExecutor:
    def __init__(
        self,
        work_dir: Path,
        lmms_bin: str,
        ffmpeg_bin: str,
        providers: Dict[str, Any],
    ) -> None:
        self.work_dir = work_dir
        self.lmms_bin = lmms_bin
        self.ffmpeg_bin = ffmpeg_bin
        self.providers = providers

    def run(self, commands: List[Command]) -> None:
        for cmd in commands:
            handler = getattr(self, f"_cmd_{cmd.name}", None)
            if not handler:
                raise ValueError(f"Unknown command: {cmd.name}")
            handler(cmd.args)

    # Public helpers used by CLI
    def generate_music(self, provider_name: str, prompt: str, duration: float, outdir: Path) -> Path:
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider.generate(prompt=prompt, duration=duration, outdir=outdir)

    # Command handlers
    def _cmd_set_project(self, args: Dict[str, Any]) -> None:
        self.project_path = Path(args["path"]).resolve()
        self.project = LmmsProject(self.project_path)

    def _cmd_new_project(self, args: Dict[str, Any]) -> None:
        template_path = args.get("template", "tools/beatbot/templates/beatbot_template.mmp")
        # If template path is relative, resolve it from work_dir
        if not Path(template_path).is_absolute():
            template = self.work_dir / template_path
        else:
            template = Path(template_path)

        dest = Path(args["path"])
        if not dest.is_absolute():
            dest = self.work_dir / dest

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template, dest)
        self.project_path = dest
        self.project = LmmsProject(self.project_path)

    def _cmd_set_bpm(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        self.project.set_bpm(float(args["bpm"]))
        self.project.save()

    def _cmd_set_timesig(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        self.project.set_timesig(int(args["numerator"]), int(args["denominator"]))
        self.project.save()

    def _cmd_add_sample_clip(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        sample = Path(args["src"]).resolve()
        pos = int(args.get("pos", 0))
        length = int(args.get("len", 0))
        track_index = int(args.get("track_index", 0))
        self.project.add_sample_clip(sample_path=sample, pos=pos, length=length, track_index=track_index)
        self.project.save()

    def _cmd_add_midi_clip(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        track_index = int(args.get("track_index", 0))
        pos = int(args.get("pos", 0))
        length = int(args.get("len", 192))
        name = str(args.get("name", "Pattern"))
        self.project.add_midi_clip(track_index=track_index, pos=pos, length=length, name=name)
        self.project.save()

    def _cmd_clear_notes(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        track_index = int(args.get("track_index", 0))
        clip_index = int(args.get("clip_index", -1))
        self.project.clear_notes_in_clip(track_index=track_index, clip_index=clip_index)
        self.project.save()

    def _cmd_add_notes(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        track_index = int(args.get("track_index", 0))
        clip_index = int(args.get("clip_index", -1))
        notes = args.get("notes", [])
        self.project.add_notes(track_index=track_index, notes=notes, clip_index=clip_index)
        self.project.save()

    def _cmd_replace_beats_with_chord(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        track_index = int(args.get("track_index", 0))
        start_pos = int(args.get("start_pos", 0))
        bars = int(args.get("bars", 1))
        root_key = int(args.get("root_key", 60))
        quality = str(args.get("quality", "maj7"))
        note_len = int(args.get("note_len", 36))
        self.project.replace_beats_with_chord(track_index, start_pos, bars, root_key, quality, note_len)
        self.project.save()

    def _cmd_set_instrument(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        track_index = int(args.get("track_index", 0))
        plugin = str(args["plugin"])  # e.g., 'kicker' or 'tripleoscillator'
        name = args.get("name")
        self.project.set_instrument_plugin(track_index, plugin, name)
        self.project.save()

    def _cmd_add_drum_pattern(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        style = str(args.get("style", "lofi"))
        bars = int(args.get("bars", 4))
        start_pos = int(args.get("start_pos", 0))
        self.project.add_drum_pattern(style=style, bars=bars, start_pos=start_pos)
        self.project.save()

    def _cmd_add_walking_bass(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        root_key = int(args.get("root_key", 60))
        bars = int(args.get("bars", 2))
        start_pos = int(args.get("start_pos", 0))
        self.project.add_walking_bass(root_key=root_key, bars=bars, start_pos=start_pos)
        self.project.save()

    def _cmd_add_bass_pattern(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        style = str(args.get("style", "house"))
        root_key = int(args.get("root_key", 36))
        bars = int(args.get("bars", 4))
        start_pos = int(args.get("start_pos", 0))
        self.project.add_bass_pattern(style=style, root_key=root_key, bars=bars, start_pos=start_pos)
        self.project.save()

    def _cmd_add_melody_pattern(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        style = str(args.get("style", "catchy"))
        scale = str(args.get("scale", "minor"))
        bars = int(args.get("bars", 4))
        start_pos = int(args.get("start_pos", 0))
        self.project.add_melody_pattern(style=style, scale=scale, bars=bars, start_pos=start_pos)
        self.project.save()

    def _cmd_render(self, args: Dict[str, Any]) -> None:
        self._ensure_project()
        out = Path(args["out"]).resolve()
        fmt = args.get("format", "wav")
        sr = int(args.get("samplerate", 44100))
        bitrate = int(args.get("bitrate", 160))
        loop = bool(args.get("loop", False))

        cmd = [
            self.lmms_bin,
            "--render",
            str(self.project_path),
            "--output",
            str(out),
            "--format",
            fmt,
            "--samplerate",
            str(sr),
            "--bitrate",
            str(bitrate),
        ]
        if loop:
            cmd.append("--loop")
        self._run(cmd)

    def _cmd_export_tiktok(self, args: Dict[str, Any]) -> None:
        # TikTok-friendly: 1080x1920 MP4 H.264 AAC 44.1k stereo
        audio = Path(args["audio"]).resolve()
        out = Path(args["out"]).resolve()
        cover = args.get("cover")
        ffmpeg = self.ffmpeg_bin
        duration = float(args.get("duration", 15))

        if cover:
            cover = Path(cover).resolve()
            vf = f"scale=1080:1920,format=yuv420p"
            cmd = [
                ffmpeg,
                "-y",
                "-loop", "1",
                "-i", str(cover),
                "-i", str(audio),
                "-t", str(duration),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", vf,
                "-r", "30",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                str(out),
            ]
        else:
            # Audio only to MP4 with blank canvas
            vf = "color=c=black:s=1080x1920:d=1,format=yuv420p"
            cmd = [
                ffmpeg,
                "-y",
                "-f", "lavfi",
                "-i", vf,
                "-i", str(audio),
                "-t", str(duration),
                "-shortest",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                str(out),
            ]
        self._run(cmd)

    def _cmd_generate_music(self, args: Dict[str, Any]) -> None:
        provider_name = args.get("provider", "elevenlabs")
        prompt = args["prompt"]
        duration = float(args.get("duration", 8.0))
        out = Path(args["out"]).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}")
        tmp = provider.generate(prompt=prompt, duration=duration, outdir=out.parent)
        if tmp != out:
            # Rename/move to requested output path
            tmp.replace(out)

    def _ensure_project(self) -> None:
        if not hasattr(self, "project") or self.project is None:
            raise RuntimeError("Project is not set. Use set_project or new_project first.")

    def _run(self, cmd: List[str]) -> None:
        env = os.environ.copy()
        subprocess.run(cmd, check=True, cwd=self.work_dir, env=env)

    def _cmd_synthesize_tone(self, args: Dict[str, Any]) -> None:
        # Utility to create a tone for demos when no provider/API key present
        out = Path(args["out"]).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        freq = str(args.get("freq", 220))
        duration = str(args.get("duration", 8))
        sr = str(args.get("samplerate", 44100))
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency={freq}:duration={duration}:sample_rate={sr}",
            "-c:a", "pcm_s16le",
            str(out),
        ]
        self._run(cmd)


