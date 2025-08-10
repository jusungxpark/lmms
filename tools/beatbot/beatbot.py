#!/usr/bin/env python3
"""
BeatBot: Natural-language to music workflow orchestrator for LMMS

- Parses user prompts into a command plan (via GPT-5/OpenAI or heuristics)
- Executes commands to generate stems (ElevenLabs Music), assemble LMMS project,
  render audio, and export TikTok-ready video.

Environment variables:
- OPENAI_API_KEY (optional, for GPT planning)
- ELEVENLABS_API_KEY (optional, for music generation)

Config file (optional): tools/beatbot/config.json
{
  "lmms_bin": "/usr/local/bin/lmms",
  "ffmpeg_bin": "/opt/homebrew/bin/ffmpeg",
  "work_dir": "/absolute/path/to/lmms"  (defaults to repo root if omitted)
}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables from .env file if it exists
def load_env():
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    if key and value:
                        os.environ[key] = value

load_env()

# Support running as script or module
try:
    from .planner_enhanced import EnhancedPlanner as PromptPlanner
    from .commands import CommandExecutor, Command
    from .providers.elevenlabs import ElevenLabsMusicProvider
except ImportError:  # pragma: no cover
    # Fallback when executed directly
    try:
        # Try import when run from repo root
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from tools.beatbot.planner_enhanced import EnhancedPlanner as PromptPlanner  # type: ignore
        from tools.beatbot.commands import CommandExecutor, Command  # type: ignore
        from tools.beatbot.providers.elevenlabs import ElevenLabsMusicProvider  # type: ignore
    except ImportError:
        # Last fallback to original planner
        from planner import PromptPlanner  # type: ignore
        from commands import CommandExecutor, Command  # type: ignore
        from providers.elevenlabs import ElevenLabsMusicProvider  # type: ignore


def load_config(explicit_path: Optional[str] = None) -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    default_config_candidates = [
        Path(explicit_path) if explicit_path else None,
        repo_root / "tools" / "beatbot" / "config.json",
        repo_root / "tools" / "beatbot" / "config.example.json",
    ]
    for candidate in default_config_candidates:
        if candidate and candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Expand vars and user in all string values
            def expand(v: Any) -> Any:
                if isinstance(v, str):
                    return os.path.expandvars(os.path.expanduser(v))
                if isinstance(v, list):
                    return [expand(x) for x in v]
                if isinstance(v, dict):
                    return {k: expand(val) for k, val in v.items()}
                return v

            return expand(data)  # type: ignore[return-value]
    return {}


def _build_executor(config: Dict[str, Any]) -> CommandExecutor:
    repo_root = Path(__file__).resolve().parents[2]
    work_dir = Path(config.get("work_dir") or repo_root).resolve()
    lmms_bin = config.get("lmms_bin") or "lmms"
    ffmpeg_bin = config.get("ffmpeg_bin") or "ffmpeg"

    # Providers
    eleven = ElevenLabsMusicProvider(api_key=os.getenv("ELEVENLABS_API_KEY"))

    return CommandExecutor(
        work_dir=work_dir,
        lmms_bin=lmms_bin,
        ffmpeg_bin=ffmpeg_bin,
        providers={
            "elevenlabs": eleven,
        },
    )


def cmd_plan(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    planner = PromptPlanner(model=args.model, temperature=args.temperature)
    plan = planner.plan(args.prompt)
    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    else:
        print(json.dumps(plan, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    executor = _build_executor(config)
    plan_data = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    commands: List[Command] = [Command(**c) for c in plan_data.get("commands", [])]
    executor.run(commands)
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    planner = PromptPlanner(model=args.model, temperature=args.temperature)
    plan = planner.plan(args.prompt)
    if args.print_plan:
        print(json.dumps(plan, indent=2))
    executor = _build_executor(config)
    commands: List[Command] = [Command(**c) for c in plan.get("commands", [])]
    executor.run(commands)
    return 0


def cmd_gen(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    executor = _build_executor(config)
    provider_name = args.provider
    prompt = args.prompt
    duration = args.duration
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    audio_path = executor.generate_music(provider_name, prompt, duration, outdir)
    print(str(audio_path))
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="BeatBot Orchestrator")
    p.add_argument("--config", help="Path to config.json", default=None)

    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("plan", help="Plan commands from a prompt")
    sp.add_argument("prompt")
    sp.add_argument("--model", default=os.getenv("BEATBOT_MODEL", "gpt-4o-mini"))
    sp.add_argument("--temperature", type=float, default=0.2)
    sp.add_argument("--out", help="Write plan JSON to file")
    sp.set_defaults(func=cmd_plan)

    sr = sub.add_parser("run", help="Run a command plan JSON")
    sr.add_argument("plan", help="Path to plan.json")
    sr.set_defaults(func=cmd_run)

    sp2 = sub.add_parser("prompt", help="Plan and execute directly from a prompt")
    sp2.add_argument("prompt")
    sp2.add_argument("--model", default=os.getenv("BEATBOT_MODEL", "gpt-4o-mini"))
    sp2.add_argument("--temperature", type=float, default=0.2)
    sp2.add_argument("--print-plan", action="store_true")
    sp2.set_defaults(func=cmd_prompt)

    sg = sub.add_parser("gen", help="Generate a stem via provider")
    sg.add_argument("provider", choices=["elevenlabs"], help="Music generation provider")
    sg.add_argument("prompt", help="Provider prompt")
    sg.add_argument("--duration", type=float, default=8.0, help="Seconds")
    sg.add_argument("--outdir", default="build/beatbot/generated")
    sg.set_defaults(func=cmd_gen)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


