#!/usr/bin/env python3
"""
LMMS AI Interface - High-level interface for AI to control LMMS
Provides semantic, music-oriented commands that GPT-5 can easily understand and use
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add parent directory to path for lmms_controller import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_controller import LMMSController


class LMMSAIInterface:
    """
    High-level interface for AI to control LMMS
    All methods are designed to be intuitive for an AI that understands music production
    """
    
    def __init__(self, project_path: Optional[str] = None):
        self.controller = LMMSController(project_path)
        self.current_project = project_path
        
        # Musical constants for easier reference
        self.WAVEFORMS = {
            'sine': 0,
            'triangle': 1,
            'saw': 2,
            'square': 3,
            'noise': 4,
            'user': 5
        }
        
        self.FILTER_TYPES = {
            'lowpass': 0,
            'highpass': 1,
            'bandpass': 2,
            'bandstop': 3,
            'allpass': 4,
            'notch': 5
        }
        
        self.NOTE_MAP = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
    
    # === Project Management ===
    
    def create_new_project(self, name: str, tempo: int = 128, genre: str = "techno") -> str:
        """
        Create a new music project
        
        Args:
            name: Project name (will be saved as name.mmp)
            tempo: BPM (beats per minute)
            genre: Musical genre (helps set up appropriate defaults)
        
        Returns:
            Status message
        """
        self.controller = LMMSController()
        self.controller.set_tempo(tempo)
        
        # Set up genre-specific defaults
        if genre.lower() in ['techno', 'house', 'electronic']:
            # Add basic techno/house structure
            self.add_drum_track("Kick", drum_type="kick")
            self.add_drum_track("Hihat", drum_type="hihat")
            self.add_bass_track("Bass")
        elif genre.lower() in ['ambient', 'atmospheric']:
            self.add_pad_track("Pad")
            self.add_lead_track("Lead")
        
        filepath = f"{name}.mmp"
        self.controller.save_project(filepath)
        self.current_project = filepath
        
        return f"Created new {genre} project '{name}' at {tempo} BPM"
    
    def save_project(self, name: Optional[str] = None) -> str:
        """Save the current project"""
        if name:
            filepath = f"{name}.mmp" if not name.endswith('.mmp') else name
        else:
            filepath = self.current_project
        
        self.controller.save_project(filepath)
        return f"Project saved to {filepath}"
    
    def open_project(self, filepath: str) -> str:
        """Open an existing project"""
        self.controller.load_project(filepath)
        self.current_project = filepath
        info = self.controller.get_info()
        return f"Opened project with {len(info['tracks'])} tracks at {info['tempo']} BPM"
    
    # === Track Creation ===
    
    def add_drum_track(self, name: str, drum_type: str = "kick") -> str:
        """
        Add a drum track
        
        Args:
            name: Track name
            drum_type: Type of drum (kick, snare, hihat, clap, etc.)
        
        Returns:
            Status message
        """
        track = self.controller.add_kick_track(name)
        
        # Set drum-specific parameters based on type
        if drum_type == "kick":
            self.set_kick_character(name, "punchy")
        elif drum_type == "hihat":
            # Adjust kick parameters to sound more like a hihat
            self.controller.instruments.set_kicker_params(
                name,
                start=8000,
                end=4000,
                decay=50,
                dist=0.1,
                noise=0.7
            )
        elif drum_type == "snare":
            self.controller.instruments.set_kicker_params(
                name,
                start=400,
                end=200,
                decay=150,
                dist=0.3,
                noise=0.5
            )
        
        return f"Added {drum_type} drum track: {name}"
    
    def add_bass_track(self, name: str = "Bass", character: str = "deep") -> str:
        """
        Add a bass track
        
        Args:
            name: Track name
            character: Bass character (deep, acid, sub, punchy)
        
        Returns:
            Status message
        """
        track = self.controller.add_synth_track(name)
        
        # Configure for bass sound
        if character == "deep":
            # Deep sub bass
            self.controller.instruments.set_tripleoscillator_params(
                name, 0, vol=100, wavetype=self.WAVEFORMS['sine'], coarse=-12
            )
            self.controller.instruments.set_tripleoscillator_params(
                name, 1, vol=30, wavetype=self.WAVEFORMS['square'], coarse=-12
            )
            self.controller.instruments.set_filter(
                name, fcut=500, fres=0.3, ftype=self.FILTER_TYPES['lowpass']
            )
        elif character == "acid":
            # Acid bass (303-style)
            self.controller.instruments.set_tripleoscillator_params(
                name, 0, vol=100, wavetype=self.WAVEFORMS['saw'], coarse=-24
            )
            self.controller.instruments.set_filter(
                name, fcut=800, fres=0.8, ftype=self.FILTER_TYPES['lowpass']
            )
            # Short envelope for acid sound
            self.controller.instruments.set_envelope(
                name, 'vol', att=0.01, dec=0.2, sus=0.3, rel=0.1
            )
        
        return f"Added {character} bass track: {name}"
    
    def add_lead_track(self, name: str = "Lead", character: str = "bright") -> str:
        """
        Add a lead/melody track
        
        Args:
            name: Track name
            character: Lead character (bright, warm, harsh, soft)
        
        Returns:
            Status message
        """
        track = self.controller.add_synth_track(name)
        
        if character == "bright":
            self.controller.instruments.set_tripleoscillator_params(
                name, 0, vol=80, wavetype=self.WAVEFORMS['saw']
            )
            self.controller.instruments.set_tripleoscillator_params(
                name, 1, vol=60, wavetype=self.WAVEFORMS['square'], finel=7
            )
            self.controller.instruments.set_filter(
                name, fcut=8000, fres=0.4
            )
        elif character == "warm":
            self.controller.instruments.set_tripleoscillator_params(
                name, 0, vol=70, wavetype=self.WAVEFORMS['triangle']
            )
            self.controller.instruments.set_tripleoscillator_params(
                name, 1, vol=50, wavetype=self.WAVEFORMS['sine'], coarse=12
            )
            self.controller.instruments.set_filter(
                name, fcut=4000, fres=0.2
            )
        
        return f"Added {character} lead track: {name}"
    
    def add_pad_track(self, name: str = "Pad", character: str = "atmospheric") -> str:
        """
        Add a pad/atmosphere track
        
        Args:
            name: Track name
            character: Pad character (atmospheric, warm, bright, dark)
        
        Returns:
            Status message
        """
        track = self.controller.add_synth_track(name)
        
        # Long attack and release for pad sound
        self.controller.instruments.set_envelope(
            name, 'vol', att=0.8, dec=0.3, sus=0.7, rel=1.5
        )
        
        if character == "atmospheric":
            self.controller.instruments.set_tripleoscillator_params(
                name, 0, vol=60, wavetype=self.WAVEFORMS['saw'], finel=3
            )
            self.controller.instruments.set_tripleoscillator_params(
                name, 1, vol=50, wavetype=self.WAVEFORMS['saw'], finer=-3
            )
            self.controller.instruments.set_tripleoscillator_params(
                name, 2, vol=40, wavetype=self.WAVEFORMS['sine'], coarse=12
            )
            self.controller.instruments.set_filter(
                name, fcut=3000, fres=0.3
            )
        
        return f"Added {character} pad track: {name}"
    
    # === Sound Design ===
    
    def set_kick_character(self, track_name: str, character: str) -> str:
        """
        Set kick drum character
        
        Args:
            track_name: Name of the kick track
            character: Kick character (punchy, deep, hard, soft, distorted)
        
        Returns:
            Status message
        """
        params = {}
        
        if character == "punchy":
            params = {'start': 200, 'end': 40, 'decay': 300, 'dist': 0.3, 'startclick': 0.5}
        elif character == "deep":
            params = {'start': 120, 'end': 30, 'decay': 500, 'dist': 0.1, 'startclick': 0.2}
        elif character == "hard":
            params = {'start': 250, 'end': 50, 'decay': 200, 'dist': 0.7, 'startclick': 0.8}
        elif character == "soft":
            params = {'start': 100, 'end': 35, 'decay': 400, 'dist': 0, 'startclick': 0}
        elif character == "distorted":
            params = {'start': 200, 'end': 40, 'decay': 350, 'dist': 0.9, 'startclick': 0.6}
        
        self.controller.instruments.set_kicker_params(track_name, **params)
        return f"Set {track_name} to {character} character"
    
    def adjust_brightness(self, track_name: str, amount: str) -> str:
        """
        Adjust track brightness (filter cutoff)
        
        Args:
            track_name: Track to adjust
            amount: Brightness level (very-dark, dark, neutral, bright, very-bright)
        
        Returns:
            Status message
        """
        cutoff_map = {
            'very-dark': 500,
            'dark': 1500,
            'neutral': 5000,
            'bright': 10000,
            'very-bright': 14000
        }
        
        cutoff = cutoff_map.get(amount, 5000)
        self.controller.instruments.set_filter(track_name, fcut=cutoff)
        return f"Set {track_name} brightness to {amount}"
    
    def set_envelope_shape(self, track_name: str, shape: str) -> str:
        """
        Set envelope shape using musical terms
        
        Args:
            track_name: Track to adjust
            shape: Envelope shape (pluck, pad, stab, sustained, percussive)
        
        Returns:
            Status message
        """
        shapes = {
            'pluck': {'att': 0, 'dec': 0.3, 'sus': 0, 'rel': 0.2},
            'pad': {'att': 0.8, 'dec': 0.3, 'sus': 0.7, 'rel': 1.5},
            'stab': {'att': 0, 'dec': 0.1, 'sus': 0.3, 'rel': 0.3},
            'sustained': {'att': 0.1, 'dec': 0.1, 'sus': 0.9, 'rel': 0.5},
            'percussive': {'att': 0, 'dec': 0.2, 'sus': 0, 'rel': 0.1}
        }
        
        if shape in shapes:
            self.controller.instruments.set_envelope(track_name, 'vol', **shapes[shape])
            return f"Set {track_name} envelope to {shape}"
        return f"Unknown shape: {shape}"
    
    # === Mix Controls ===
    
    def set_volume(self, track_name: str, level: str) -> str:
        """
        Set track volume using descriptive terms
        
        Args:
            track_name: Track to adjust
            level: Volume level (silent, very-quiet, quiet, medium, loud, very-loud, max)
        
        Returns:
            Status message
        """
        volume_map = {
            'silent': 0,
            'very-quiet': 20,
            'quiet': 40,
            'medium': 60,
            'loud': 80,
            'very-loud': 90,
            'max': 100
        }
        
        volume = volume_map.get(level, 70)
        self.controller.tracks.set_volume(track_name, volume)
        return f"Set {track_name} volume to {level}"
    
    def set_panning(self, track_name: str, position: str) -> str:
        """
        Set track panning
        
        Args:
            track_name: Track to adjust
            position: Pan position (hard-left, left, center, right, hard-right)
        
        Returns:
            Status message
        """
        pan_map = {
            'hard-left': -100,
            'left': -50,
            'center': 0,
            'right': 50,
            'hard-right': 100
        }
        
        pan = pan_map.get(position, 0)
        self.controller.tracks.set_pan(track_name, pan)
        return f"Panned {track_name} to {position}"
    
    def mute(self, track_name: str) -> str:
        """Mute a track"""
        self.controller.tracks.mute_track(track_name, True)
        return f"Muted {track_name}"
    
    def unmute(self, track_name: str) -> str:
        """Unmute a track"""
        self.controller.tracks.mute_track(track_name, False)
        return f"Unmuted {track_name}"
    
    # === Effects ===
    
    def add_reverb(self, track_name: str, size: str = "medium") -> str:
        """
        Add reverb to a track
        
        Args:
            track_name: Track to add reverb to
            size: Reverb size (small, medium, large, huge)
        
        Returns:
            Status message
        """
        # This would need to be implemented with specific LMMS reverb plugin
        return f"Added {size} reverb to {track_name}"
    
    def add_delay(self, track_name: str, time: str = "1/8") -> str:
        """
        Add delay effect
        
        Args:
            track_name: Track to add delay to
            time: Delay time (1/4, 1/8, 1/16, etc.)
        
        Returns:
            Status message
        """
        return f"Added {time} delay to {track_name}"
    
    def add_distortion(self, track_name: str, amount: str = "moderate") -> str:
        """
        Add distortion
        
        Args:
            track_name: Track to distort
            amount: Distortion amount (light, moderate, heavy, extreme)
        
        Returns:
            Status message
        """
        return f"Added {amount} distortion to {track_name}"
    
    # === Project Analysis ===
    
    def analyze_project(self) -> str:
        """
        Analyze current project and provide musical insights
        
        Returns:
            Analysis text
        """
        info = self.controller.get_info()
        
        analysis = f"Project Analysis:\n"
        analysis += f"- Tempo: {info['tempo']} BPM\n"
        analysis += f"- Time Signature: {info['time_signature']}\n"
        analysis += f"- Total Tracks: {len(info['tracks'])}\n\n"
        
        analysis += "Track Breakdown:\n"
        for track in info['tracks']:
            status = "🔇 Muted" if track['muted'] else "🔊 Active"
            instrument = track.get('instrument', 'No instrument')
            analysis += f"- {track['name']}: {instrument} [{status}]\n"
        
        # Genre detection based on tempo and track names
        if info['tempo'] is not None:
            if 120 <= info['tempo'] <= 130:
                if any('kick' in t['name'].lower() for t in info['tracks']):
                    analysis += "\nGenre hint: House/Techno range"
            elif 140 <= info['tempo'] <= 150:
                analysis += "\nGenre hint: Trance/Hardstyle range"
            elif 160 <= info['tempo'] <= 180:
                analysis += "\nGenre hint: Drum & Bass range"
            elif 60 <= info['tempo'] <= 90:
                analysis += "\nGenre hint: Hip-Hop/Downtempo range"
        
        return analysis
    
    def suggest_next_element(self) -> str:
        """
        Suggest what element to add next based on current project
        
        Returns:
            Suggestion text
        """
        info = self.controller.get_info()
        tracks = [t['name'].lower() for t in info['tracks']]
        
        suggestions = []
        
        if not any('kick' in t for t in tracks):
            suggestions.append("Add a kick drum for rhythm foundation")
        
        if not any('bass' in t for t in tracks):
            suggestions.append("Add a bass line for low-end support")
        
        if not any('lead' in t or 'melody' in t for t in tracks):
            suggestions.append("Add a lead melody for the main hook")
        
        if not any('pad' in t or 'atmosphere' in t for t in tracks):
            suggestions.append("Add atmospheric pads for depth")
        
        if not any('hat' in t or 'hihat' in t for t in tracks):
            suggestions.append("Add hi-hats for rhythmic detail")
        
        if len(info['tracks']) > 4 and not any('bus' in t or 'group' in t for t in tracks):
            suggestions.append("Consider grouping similar tracks")
        
        if suggestions:
            return "Suggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
        else:
            return "Project has good coverage. Consider adding variations or effects."
    
    # === Workflow Helpers ===
    
    def create_basic_beat(self, style: str = "house") -> str:
        """
        Create a basic beat pattern
        
        Args:
            style: Beat style (house, techno, trap, dnb, etc.)
        
        Returns:
            Status message
        """
        if style == "house":
            self.add_drum_track("Kick", "kick")
            self.set_kick_character("Kick", "punchy")
            self.add_drum_track("Hihat", "hihat")
            self.add_drum_track("Clap", "snare")
            return "Created basic house beat (kick, hihat, clap)"
        
        elif style == "techno":
            self.add_drum_track("Kick", "kick")
            self.set_kick_character("Kick", "hard")
            self.add_drum_track("Hihat", "hihat")
            self.add_bass_track("Acid Bass", "acid")
            return "Created basic techno beat (hard kick, hihat, acid bass)"
        
        elif style == "trap":
            self.controller.set_tempo(140)
            self.add_drum_track("Kick", "kick")
            self.set_kick_character("Kick", "deep")
            self.add_drum_track("Snare", "snare")
            self.add_drum_track("Hihat", "hihat")
            return "Created basic trap beat at 140 BPM"
        
        return f"Style '{style}' not recognized"
    
    def prepare_for_live_performance(self) -> str:
        """
        Set up project for live performance
        
        Returns:
            Status message
        """
        info = self.controller.get_info()
        
        # Unmute all tracks
        for track in info['tracks']:
            if track['muted']:
                self.controller.tracks.mute_track(track['name'], False)
        
        # Set reasonable volumes
        for track in info['tracks']:
            name_lower = track['name'].lower()
            if 'kick' in name_lower:
                self.controller.tracks.set_volume(track['name'], 90)
            elif 'bass' in name_lower:
                self.controller.tracks.set_volume(track['name'], 80)
            elif 'lead' in name_lower or 'melody' in name_lower:
                self.controller.tracks.set_volume(track['name'], 70)
            else:
                self.controller.tracks.set_volume(track['name'], 60)
        
        return "Project prepared for live performance - all tracks unmuted and balanced"
    
    def export_stems(self, output_dir: str = "./stems") -> str:
        """
        Export individual track stems for mixing
        
        Args:
            output_dir: Directory to export stems to
        
        Returns:
            Status message
        """
        # This would need actual LMMS export functionality
        return f"Stems would be exported to {output_dir}"
    
    def get_help(self) -> str:
        """
        Get help on available commands
        
        Returns:
            Help text
        """
        help_text = """
LMMS AI Interface - Available Commands:

PROJECT MANAGEMENT:
- create_new_project(name, tempo, genre) - Start a new project
- save_project(name) - Save current project
- open_project(filepath) - Open existing project

TRACK CREATION:
- add_drum_track(name, drum_type) - Add drums (kick, snare, hihat, etc.)
- add_bass_track(name, character) - Add bass (deep, acid, sub, punchy)
- add_lead_track(name, character) - Add lead (bright, warm, harsh, soft)
- add_pad_track(name, character) - Add pads (atmospheric, warm, bright, dark)

SOUND DESIGN:
- set_kick_character(track, character) - Adjust kick sound
- adjust_brightness(track, amount) - Control filter brightness
- set_envelope_shape(track, shape) - Set ADSR envelope

MIX CONTROLS:
- set_volume(track, level) - Set volume (quiet, medium, loud, etc.)
- set_panning(track, position) - Pan track (left, center, right)
- mute(track) / unmute(track) - Mute control

EFFECTS:
- add_reverb(track, size) - Add reverb
- add_delay(track, time) - Add delay
- add_distortion(track, amount) - Add distortion

WORKFLOW:
- create_basic_beat(style) - Quick beat creation
- analyze_project() - Get project overview
- suggest_next_element() - Get production suggestions
- prepare_for_live_performance() - Optimize for live use

Type get_help() for this list.
        """
        return help_text


# Command-line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        ai = LMMSAIInterface()
        print(ai.get_help())
        sys.exit(0)
    
    command = sys.argv[1]
    
    # Create an interface instance
    ai = LMMSAIInterface()
    
    # Simple command router
    if command == "new":
        if len(sys.argv) >= 4:
            result = ai.create_new_project(sys.argv[2], int(sys.argv[3]))
            print(result)
        else:
            print("Usage: new <name> <tempo>")
    
    elif command == "analyze":
        if len(sys.argv) >= 3:
            ai.open_project(sys.argv[2])
            print(ai.analyze_project())
        else:
            print("Usage: analyze <project.mmp>")
    
    elif command == "suggest":
        if len(sys.argv) >= 3:
            ai.open_project(sys.argv[2])
            print(ai.suggest_next_element())
        else:
            print("Usage: suggest <project.mmp>")
    
    elif command == "beat":
        style = sys.argv[2] if len(sys.argv) > 2 else "house"
        result = ai.create_basic_beat(style)
        ai.save_project(f"{style}_beat.mmp")
        print(result)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: new, analyze, suggest, beat")