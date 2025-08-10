### BeatBot: Natural-language music workflow with LMMS

BeatBot turns prompts like "Make this more jazzy" into a command plan, generates stems via ElevenLabs, assembles an LMMS project, renders audio, and exports a TikTok-ready video.

Prereqs:
- LMMS built and available as `lmms` CLI (supports `--render`)
- ffmpeg installed
- Python 3.10+

Env:
- `OPENAI_API_KEY` (optional) for planning
- `ELEVENLABS_API_KEY` for stem generation

Config: `tools/beatbot/config.json` (optional)
```
{
  "lmms_bin": "/usr/local/bin/lmms",
  "ffmpeg_bin": "/opt/homebrew/bin/ffmpeg",
  "work_dir": "/Users/you/Desktop/projects/lmms"
}
```

Install deps:
```
pip install requests openai
```

Usage examples:

Plan from prompt (print JSON):
```
python tools/beatbot/beatbot.py plan "Make this more jazzy with swung drums and walking bass" --print-plan
```

Generate a drum loop stem:
```
python tools/beatbot/beatbot.py gen elevenlabs "tight swung jazz drums, 120bpm" --duration 8 --outdir build/beatbot/generated
```

Create project, insert stems, render, and export TikTok:
```
python tools/beatbot/beatbot.py prompt "Create a 15s jazzy groove: drums + bass. Export TikTok." --print-plan
```

Available commands in plan:
- `new_project {path, template?}`
- `set_project {path}`
- `set_bpm {bpm}`
- `set_timesig {numerator, denominator}`
- `add_sample_clip {src, pos, len, track_index}`
- `render {out, format, samplerate, bitrate, loop?}`
- `export_tiktok {audio, out, cover?, duration?}`

Notes:
- `add_sample_clip` writes `<sampleclip src=...>` into the LMMS `.mmp`. LMMS will load the referenced file on render.
- Use `--format wav|flac|ogg|mp3` with `render`.
- If LMMS binary path differs, copy `tools/beatbot/config.example.json` to `tools/beatbot/config.json` and edit paths.

Dev quickstart on macOS (venv):
```
python3 -m venv .beatbot-venv
source .beatbot-venv/bin/activate
pip install requests openai
PYTHONPATH=. python tools/beatbot/beatbot.py prompt "Create a 8s jazzy groove: drums + bass." --print-plan
```


