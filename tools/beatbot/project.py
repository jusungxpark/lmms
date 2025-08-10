from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


class LmmsProject:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()

    def save(self) -> None:
        self.tree.write(self.path, encoding="utf-8", xml_declaration=True)

    # Header level controls
    def set_bpm(self, bpm: float) -> None:
        head = self.root.find("head")
        if head is None:
            head = ET.SubElement(self.root, "head")
        head.set("bpm", str(int(round(bpm))))

    def set_timesig(self, numerator: int, denominator: int) -> None:
        head = self.root.find("head")
        if head is None:
            head = ET.SubElement(self.root, "head")
        head.set("timesig_numerator", str(numerator))
        head.set("timesig_denominator", str(denominator))

    # Tracks and clips
    def _get_song_trackcontainer(self):
        song = self.root.find("song")
        if song is None:
            raise RuntimeError("Malformed project: missing <song>")
        for child in song:
            if child.tag == "trackcontainer" and child.attrib.get("type") == "song":
                return child
        # Fallback: first trackcontainer
        tc = song.find("trackcontainer")
        if tc is None:
            raise RuntimeError("Malformed project: missing <trackcontainer>")
        return tc

    def _ensure_sample_track(self, track_index: int) -> ET.Element:
        tc = self._get_song_trackcontainer()
        tracks = [t for t in tc.findall("track")]
        # Ensure enough tracks
        while len(tracks) <= track_index:
            # Create a new empty Sample track
            new_t = ET.SubElement(tc, "track", {"muted": "0", "type": "2", "name": "Sample Track"})
            ET.SubElement(new_t, "sampletrack", {"vol": "100"})
            tracks.append(new_t)
        t = tracks[track_index]
        # If not a sample track, convert by resetting children
        if t.attrib.get("type") != "2":
            t.attrib["type"] = "2"
            for ch in list(t):
                t.remove(ch)
            ET.SubElement(t, "sampletrack", {"vol": "100"})
        return t

    def add_sample_clip(self, sample_path: Path, pos: int, length: int, track_index: int = 0) -> None:
        t = self._ensure_sample_track(track_index)
        clip_attrs = {
            "pos": str(pos),
            "len": str(length if length > 0 else 192),
            "muted": "0",
            "src": str(sample_path),
            "off": "0",
            "autoresize": "1",
        }
        ET.SubElement(t, "sampleclip", clip_attrs)

    # Instrument + MIDI
    def _ensure_instrument_track(self, track_index: int) -> ET.Element:
        tc = self._get_song_trackcontainer()
        tracks = [t for t in tc.findall("track")]
        while len(tracks) <= track_index:
            new_t = ET.SubElement(tc, "track", {"muted": "0", "type": "0", "name": "Instrument"})
            it = ET.SubElement(new_t, "instrumenttrack", {"pan": "0", "mixch": "0", "pitch": "0", "basenote": "57", "vol": "100"})
            inst = ET.SubElement(it, "instrument", {"name": "tripleoscillator"})
            ET.SubElement(inst, "tripleoscillator")
            ET.SubElement(it, "midiport")
            ET.SubElement(it, "fxchain", {"numofeffects": "0", "enabled": "0"})
            tracks.append(new_t)
        t = tracks[track_index]
        # If not instrument track, convert
        if t.attrib.get("type") != "0":
            t.attrib["type"] = "0"
            for ch in list(t):
                t.remove(ch)
            it = ET.SubElement(t, "instrumenttrack", {"pan": "0", "mixch": "0", "pitch": "0", "basenote": "57", "vol": "100"})
            inst = ET.SubElement(it, "instrument", {"name": "tripleoscillator"})
            ET.SubElement(inst, "tripleoscillator")
            ET.SubElement(it, "midiport")
            ET.SubElement(it, "fxchain", {"numofeffects": "0", "enabled": "0"})
        return t

    def set_instrument_plugin(self, track_index: int, plugin_name: str, track_name: Optional[str] = None) -> None:
        t = self._ensure_instrument_track(track_index)
        if track_name:
            t.set("name", track_name)
        # Ensure instrumenttrack child exists
        it = t.find("instrumenttrack")
        if it is None:
            it = ET.SubElement(t, "instrumenttrack", {"pan": "0", "mixch": "0", "pitch": "0", "basenote": "57", "vol": "100"})
        inst = it.find("instrument")
        if inst is None:
            inst = ET.SubElement(it, "instrument", {"name": plugin_name})
        else:
            inst.set("name", plugin_name)
        # ensure plugin node exists (best-effort)
        if len(list(inst)) == 0:
            ET.SubElement(inst, plugin_name)  # create empty plugin node

    def add_midi_clip(self, track_index: int, pos: int, length: int, name: str = "Pattern") -> None:
        t = self._ensure_instrument_track(track_index)
        pat_attrs = {
            "type": "1",  # melody clip
            "muted": "0",
            "steps": "16",
            "name": name,
            "pos": str(pos),
            "len": str(length if length > 0 else 192),
        }
        ET.SubElement(t, "pattern", pat_attrs)

    def _get_pattern(self, track_index: int, clip_index: int = -1) -> ET.Element:
        t = self._ensure_instrument_track(track_index)
        patterns = [p for p in t.findall("pattern")]
        if not patterns:
            # create a default one bar clip
            self.add_midi_clip(track_index, pos=0, length=192, name="Pattern")
            patterns = [p for p in t.findall("pattern")]
        if clip_index < 0:
            return patterns[0]
        return patterns[clip_index]

    def clear_notes_in_clip(self, track_index: int, clip_index: int = -1) -> None:
        pat = self._get_pattern(track_index, clip_index)
        for n in list(pat.findall("note")):
            pat.remove(n)

    def add_notes(self, track_index: int, notes: list[dict], clip_index: int = -1) -> None:
        pat = self._get_pattern(track_index, clip_index)
        for nd in notes:
            attrs = {
                "key": str(nd.get("key", 60)),
                "vol": str(nd.get("vol", 100)),
                "pos": str(nd.get("pos", 0)),
                "pan": str(nd.get("pan", 0)),
                "len": str(nd.get("len", 48)),
            }
            ET.SubElement(pat, "note", attrs)

    def replace_beats_with_chord(self, track_index: int, start_pos: int, bars: int, root_key: int = 60, quality: str = "maj7", note_len: int = 36) -> None:
        """Write a chord on each beat over the given bars, replacing notes in the first clip.

        - start_pos: tick offset to start (usually 0)
        - bars: number of bars to fill
        - root_key: MIDI key (60=C4)
        - quality: maj7|min7|dom7|maj9|sus2|sus4|dim7|min9|add9
        - note_len: ticks per note (<= 48 for quarter at 4/4)
        """
        intervals_map = {
            "maj7": [0, 4, 7, 11],
            "min7": [0, 3, 7, 10],
            "dom7": [0, 4, 7, 10],
            "maj9": [0, 4, 7, 11, 14],
            "min9": [0, 3, 7, 10, 14],
            "sus2": [0, 2, 7],
            "sus4": [0, 5, 7],
            "dim7": [0, 3, 6, 9],
            "add9": [0, 4, 7, 14],
            "6": [0, 4, 7, 9],
            "m6": [0, 3, 7, 9],
        }
        intervals = intervals_map.get(quality, intervals_map["maj7"])
        ticks_per_bar = 192
        beats_per_bar = 4
        ticks_per_beat = ticks_per_bar // beats_per_bar

        # Ensure clip exists and clear it
        self._ensure_instrument_track(track_index)
        self.add_midi_clip(track_index, pos=start_pos, length=bars * ticks_per_bar, name=f"Chord {quality}")
        self.clear_notes_in_clip(track_index)

        notes: list[dict] = []
        for b in range(bars * beats_per_bar):
            beat_pos = start_pos + b * ticks_per_beat
            for iv in intervals:
                notes.append({
                    "key": root_key + iv,
                    "vol": 100,
                    "pos": beat_pos,
                    "pan": 0,
                    "len": note_len,
                })
        self.add_notes(track_index, notes)

    # Enhanced drum patterns with genre-specific grooves
    def add_drum_pattern(self, style: str, bars: int = 4, start_pos: int = 0) -> None:
        style_l = style.lower()
        ticks_per_bar = 192
        q = ticks_per_bar // 4  # Quarter note
        e = q // 2  # Eighth note
        s = e // 2  # Sixteenth note
        t = s // 3  # Triplet

        # Tracks: Kick, Snare, Hats, Percussion
        kick_ti, snare_ti, hat_ti, perc_ti = 0, 1, 2, 3
        self.set_instrument_plugin(kick_ti, "kicker", track_name="Kick")
        self.set_instrument_plugin(snare_ti, "tripleoscillator", track_name="Snare")
        self.set_instrument_plugin(hat_ti, "tripleoscillator", track_name="Hats")

        # Helper to place notes with velocity variations
        def bar_positions(offsets):
            for b in range(bars):
                for off in offsets:
                    yield start_pos + b * ticks_per_bar + off

        # Genre-specific patterns with groove
        if "house" in style_l or "edm" in style_l:
            # Classic 4-on-the-floor with sidechain pump feel
            kick_pos = [0, q, 2*q, 3*q]
            kick_vels = [127, 110, 120, 110]  # Accent on 1 and 3
            snare_pos = [q, 3*q]  # Claps on 2 and 4
            hat_pos = [e, 3*e, 5*e, 7*e]  # Open hats on offbeats
            hat_vels = [80, 90, 80, 90]

        elif "trap" in style_l:
            # Trap with 808 pattern and hi-hat rolls
            kick_pos = [0, int(2.5*q)]
            kick_vels = [127, 100]
            snare_pos = [q, 3*q]
            # Complex hi-hat pattern with rolls
            hat_pos = []
            hat_vels = []
            for i in range(16):  # 16th notes
                pos = i * s
                if i % 4 == 0:
                    hat_pos.append(pos)
                    hat_vels.append(100)
                elif i in [6, 7, 14, 15]:  # Rolls
                    hat_pos.extend([pos, pos + s//2])
                    hat_vels.extend([80, 60])
                else:
                    hat_pos.append(pos)
                    hat_vels.append(70)

        elif "dnb" in style_l or "drum and bass" in style_l:
            # Amen break inspired pattern
            kick_pos = [0, int(2.5*q)]
            kick_vels = [127, 110]
            snare_pos = [q, 3*q]
            hat_pos = [0, e, q, q+e, 2*q, 2*q+e, 3*q, 3*q+e]
            hat_vels = [90, 70, 80, 70, 90, 70, 80, 70]

        elif "dubstep" in style_l:
            # Half-time feel with heavy emphasis
            kick_pos = [0]
            kick_vels = [127]
            snare_pos = [q]
            hat_pos = [e, 2*q+e]
            hat_vels = [80, 80]

        elif "lofi" in style_l or "lo-fi" in style_l:
            # Laid-back boom-bap pattern
            kick_pos = [0, int(1.75*q), int(2.5*q)]
            kick_vels = [100, 70, 80]
            snare_pos = [q, int(2.75*q)]
            hat_pos = [i*e for i in range(8)]
            hat_vels = [60 + (i%2)*20 for i in range(8)]  # Alternating velocities

        elif "techno" in style_l:
            # Driving techno with rolling percussion
            kick_pos = [0, q, 2*q, 3*q]
            kick_vels = [127, 120, 125, 120]
            snare_pos = []  # No snare, use percussion
            hat_pos = [i*s for i in range(16) if i % 2 == 1]  # 16th note off-beats
            hat_vels = [70 + (i%4)*10 for i in range(8)]

        elif "jazz" in style_l or "jazzy" in style_l:
            # Swing pattern (approximate with straight time)
            kick_pos = [0, int(1.5*q), 2*q]
            kick_vels = [90, 60, 70]
            snare_pos = [int(0.75*q), int(2.75*q)]  # Ghost notes
            hat_pos = [0, int(0.67*q), q, int(1.67*q), 2*q, int(2.67*q), 3*q, int(3.67*q)]
            hat_vels = [80, 60, 70, 60, 80, 60, 70, 60]

        else:  # Default: versatile pop/rock beat
            kick_pos = [0, 2*q]
            kick_vels = [120, 110]
            snare_pos = [q, 3*q]
            hat_pos = [i*e for i in range(8)]
            hat_vels = [80, 60, 70, 60, 80, 60, 70, 60]

        # Create clips and add notes
        self.add_midi_clip(kick_ti, start_pos, bars * ticks_per_bar, name=f"{style} Kick")
        self.add_midi_clip(snare_ti, start_pos, bars * ticks_per_bar, name=f"{style} Snare")
        self.add_midi_clip(hat_ti, start_pos, bars * ticks_per_bar, name=f"{style} Hats")

        self.clear_notes_in_clip(kick_ti)
        self.clear_notes_in_clip(snare_ti)
        self.clear_notes_in_clip(hat_ti)

        # Generate notes with velocity variations
        kick_notes = []
        for b in range(bars):
            for i, pos in enumerate(kick_pos):
                vel = kick_vels[i % len(kick_vels)] if 'kick_vels' in locals() else 120
                kick_notes.append({
                    "key": 36,  # C2 - standard kick
                    "pos": start_pos + b * ticks_per_bar + pos,
                    "len": int(0.8*q),
                    "vol": vel
                })

        snare_notes = []
        if snare_pos:  # Some patterns have no snare
            snare_vels = locals().get('snare_vels', [100] * len(snare_pos))
            for b in range(bars):
                for i, pos in enumerate(snare_pos):
                    snare_notes.append({
                        "key": 38,  # D2 - standard snare
                        "pos": start_pos + b * ticks_per_bar + pos,
                        "len": int(0.4*q),
                        "vol": snare_vels[i % len(snare_vels)]
                    })

        hat_notes = []
        for b in range(bars):
            for i, pos in enumerate(hat_pos):
                vel = hat_vels[i % len(hat_vels)] if 'hat_vels' in locals() else 80
                hat_notes.append({
                    "key": 42,  # F#2 - closed hat
                    "pos": start_pos + b * ticks_per_bar + pos,
                    "len": int(0.2*q),
                    "vol": vel
                })

        self.add_notes(kick_ti, kick_notes)
        self.add_notes(snare_ti, snare_notes)
        self.add_notes(hat_ti, hat_notes)

    def add_walking_bass(self, root_key: int, bars: int = 2, start_pos: int = 0) -> None:
        ticks_per_bar = 192
        q = ticks_per_bar // 4
        track_index = 3
        self.set_instrument_plugin(track_index, "tripleoscillator", track_name="Bass")
        self.add_midi_clip(track_index, start_pos, bars * ticks_per_bar, name="Walking Bass")
        self.clear_notes_in_clip(track_index)

        # Jazz walking bass with chromatic passing tones
        patterns = [
            [0, 4, 7, 5],  # 1-3-5-4
            [0, 2, 4, 5],  # 1-2-3-4
            [0, -2, -4, -5],  # 1-b7-6-5
            [0, 3, 5, 7],  # 1-b3-4-5
        ]

        notes = []
        for b in range(bars):
            bar_start = start_pos + b * ticks_per_bar
            pattern = patterns[b % len(patterns)]
            for i, iv in enumerate(pattern):
                notes.append({
                    "key": root_key + iv - 12,  # bass one octave down
                    "pos": bar_start + i*q,
                    "len": int(0.9*q),
                    "vol": 100 + (i%2)*10,  # Accent beats 1 and 3
                    "pan": 0,
                })
        self.add_notes(track_index, notes)

    def add_bass_pattern(self, style: str, root_key: int = 36, bars: int = 4, start_pos: int = 0) -> None:
        """Add genre-specific bass patterns"""
        style_l = style.lower()
        ticks_per_bar = 192
        q = ticks_per_bar // 4
        e = q // 2
        s = e // 2

        track_index = 3
        self.set_instrument_plugin(track_index, "tripleoscillator", track_name="Bass")
        self.add_midi_clip(track_index, start_pos, bars * ticks_per_bar, name=f"{style} Bass")
        self.clear_notes_in_clip(track_index)

        notes = []

        if "house" in style_l or "edm" in style_l:
            # Driving octave bass pattern
            for b in range(bars):
                bar_start = start_pos + b * ticks_per_bar
                # Root-octave-fifth pattern
                notes.extend([
                    {"key": root_key, "pos": bar_start, "len": e, "vol": 120},
                    {"key": root_key + 12, "pos": bar_start + e, "len": e, "vol": 100},
                    {"key": root_key, "pos": bar_start + q, "len": e, "vol": 110},
                    {"key": root_key + 7, "pos": bar_start + q + e, "len": e, "vol": 90},
                    {"key": root_key, "pos": bar_start + 2*q, "len": e, "vol": 120},
                    {"key": root_key + 12, "pos": bar_start + 2*q + e, "len": e, "vol": 100},
                    {"key": root_key, "pos": bar_start + 3*q, "len": e, "vol": 110},
                    {"key": root_key + 5, "pos": bar_start + 3*q + e, "len": e, "vol": 90},
                ])

        elif "trap" in style_l:
            # 808 sub bass with slides
            for b in range(bars):
                bar_start = start_pos + b * ticks_per_bar
                if b % 2 == 0:
                    # Main pattern
                    notes.extend([
                        {"key": root_key, "pos": bar_start, "len": q + e, "vol": 127},
                        {"key": root_key - 2, "pos": bar_start + 2*q, "len": e, "vol": 100},
                        {"key": root_key, "pos": bar_start + 3*q, "len": q, "vol": 110},
                    ])
                else:
                    # Variation
                    notes.extend([
                        {"key": root_key - 5, "pos": bar_start, "len": q, "vol": 120},
                        {"key": root_key, "pos": bar_start + q + e, "len": e + q, "vol": 110},
                    ])

        elif "dnb" in style_l:
            # Reese bass with movement
            for b in range(bars):
                bar_start = start_pos + b * ticks_per_bar
                progression = [0, 0, 7, 5] if b % 2 == 0 else [0, 3, 5, 7]
                for i, interval in enumerate(progression):
                    notes.append({
                        "key": root_key + interval,
                        "pos": bar_start + i*q,
                        "len": q - s,
                        "vol": 100 + (i==0)*20,
                    })

        elif "dubstep" in style_l:
            # Sub bass wobble pattern
            for b in range(bars):
                bar_start = start_pos + b * ticks_per_bar
                # Heavy sub on the 1
                notes.append({"key": root_key - 12, "pos": bar_start, "len": 2*q, "vol": 127})
                # Movement in second half
                notes.append({"key": root_key - 7, "pos": bar_start + 2*q, "len": q, "vol": 100})
                notes.append({"key": root_key - 5, "pos": bar_start + 3*q, "len": e, "vol": 90})

        else:  # Default groovy bass
            for b in range(bars):
                bar_start = start_pos + b * ticks_per_bar
                notes.extend([
                    {"key": root_key, "pos": bar_start, "len": q + e, "vol": 110},
                    {"key": root_key + 7, "pos": bar_start + 2*q, "len": e, "vol": 90},
                    {"key": root_key + 5, "pos": bar_start + 2*q + e, "len": e, "vol": 85},
                    {"key": root_key, "pos": bar_start + 3*q, "len": e, "vol": 100},
                ])

        self.add_notes(track_index, notes)

    def add_melody_pattern(self, style: str, scale: str = "minor", bars: int = 4, start_pos: int = 0) -> None:
        """Add catchy melody patterns optimized for viral potential"""
        ticks_per_bar = 192
        q = ticks_per_bar // 4
        e = q // 2

        track_index = 4
        self.set_instrument_plugin(track_index, "tripleoscillator", track_name="Lead")
        self.add_midi_clip(track_index, start_pos, bars * ticks_per_bar, name=f"{style} Melody")
        self.clear_notes_in_clip(track_index)

        # Define scales
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10],
        }

        scale_notes = scales.get(scale, scales["minor"])
        root = 60  # C4

        # Create catchy melodic patterns
        notes = []

        if style == "catchy":
            # Simple, memorable hook
            melody = [0, 0, 4, 3, 2, 2, 1, 0]  # Scale degrees
            rhythms = [q, e, e, q, q, e, e, q]

            for b in range(bars):
                bar_start = start_pos + b * ticks_per_bar
                pos = 0
                for i, (degree, length) in enumerate(zip(melody, rhythms)):
                    if degree < len(scale_notes):
                        notes.append({
                            "key": root + scale_notes[degree],
                            "pos": bar_start + pos,
                            "len": length - 2,  # Small gap
                            "vol": 90 + (i==0)*20,  # Accent first note
                        })
                    pos += length
                    if pos >= ticks_per_bar:
                        break

        self.add_notes(track_index, notes)


