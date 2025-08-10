#!/usr/bin/env python3
"""
LMMS Controller - Programmatic control interface for LMMS
Allows GPT-5 to manipulate tracks, instruments, effects, and parameters
"""

import xml.etree.ElementTree as ET
import json
import os
import subprocess
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import gzip
import shutil


class LMMSProject:
    """Handles reading and writing LMMS project files (.mmp/.mmpz)"""
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath
        self.tree = None
        self.root = None
        self.is_compressed = False
        
        if filepath:
            self.load(filepath)
    
    def load(self, filepath: str):
        """Load an LMMS project file"""
        self.filepath = filepath
        self.is_compressed = filepath.endswith('.mmpz')
        
        if self.is_compressed:
            # Decompress .mmpz file
            with gzip.open(filepath, 'rb') as f:
                content = f.read()
            self.tree = ET.ElementTree(ET.fromstring(content))
        else:
            self.tree = ET.parse(filepath)
        
        self.root = self.tree.getroot()
    
    def save(self, filepath: Optional[str] = None):
        """Save the project to a file"""
        if filepath is None:
            filepath = self.filepath
        
        if filepath.endswith('.mmpz'):
            # Save as compressed
            xml_str = ET.tostring(self.root, encoding='unicode')
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write('<?xml version="1.0"?>\n')
                f.write('<!DOCTYPE multimedia-project>\n')
                f.write(xml_str)
        else:
            # Save as uncompressed
            self.tree.write(filepath, encoding='unicode', xml_declaration=True)
    
    def get_tracks(self) -> List[ET.Element]:
        """Get all tracks in the project"""
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer is not None:
            return trackcontainer.findall('track')
        return []
    
    def get_track_by_name(self, name: str) -> Optional[ET.Element]:
        """Find a track by its name"""
        for track in self.get_tracks():
            if track.get('name') == name:
                return track
        return None
    
    def add_instrument_track(self, name: str, instrument: str = "tripleoscillator") -> ET.Element:
        """Add a new instrument track"""
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        
        # Create track element
        track = ET.SubElement(trackcontainer, 'track')
        track.set('muted', '0')
        track.set('type', '0')  # Instrument track
        track.set('name', name)
        
        # Create instrument track
        inst_track = ET.SubElement(track, 'instrumenttrack')
        inst_track.set('pan', '0')
        inst_track.set('mixch', '0')
        inst_track.set('pitch', '0')
        inst_track.set('basenote', '57')
        inst_track.set('vol', '100')
        
        # Add instrument
        inst_elem = ET.SubElement(inst_track, 'instrument')
        inst_elem.set('name', instrument)
        
        # Add instrument-specific parameters
        self._add_instrument_params(inst_elem, instrument)
        
        # Add envelope data
        self._add_envelope_data(inst_track)
        
        # Add effects chain
        fxchain = ET.SubElement(inst_track, 'fxchain')
        fxchain.set('numofeffects', '0')
        fxchain.set('enabled', '0')
        
        return track
    
    def _add_instrument_params(self, inst_elem: ET.Element, instrument: str):
        """Add instrument-specific parameters"""
        if instrument == "kicker":
            kicker = ET.SubElement(inst_elem, 'kicker')
            kicker.set('decay', '440')
            kicker.set('dist', '0.8')
            kicker.set('distend', '0.733')
            kicker.set('diststart', '0.986')
            kicker.set('end', '40')
            kicker.set('env', '0.163')
            kicker.set('gain', '1')
            kicker.set('noise', '0')
            kicker.set('slope', '0.06')
            kicker.set('start', '200')
            kicker.set('startclick', '0.395')
            kicker.set('version', '1')
        elif instrument == "tripleoscillator":
            osc = ET.SubElement(inst_elem, 'tripleoscillator')
            # Set default triple oscillator parameters
            for i in range(3):
                osc.set(f'vol{i}', '33')
                osc.set(f'pan{i}', '0')
                osc.set(f'coarse{i}', '0')
                osc.set(f'finel{i}', '0')
                osc.set(f'finer{i}', '0')
                osc.set(f'wavetype{i}', '0')
                osc.set(f'phoffset{i}', '0')
                osc.set(f'stphdetun{i}', '0')
                osc.set(f'userwavefile{i}', '')
            osc.set('modalgo1', '2')
            osc.set('modalgo2', '2')
            osc.set('modalgo3', '2')
    
    def _add_envelope_data(self, inst_track: ET.Element):
        """Add envelope data to instrument track"""
        eldata = ET.SubElement(inst_track, 'eldata')
        eldata.set('fres', '0.5')
        eldata.set('ftype', '0')
        eldata.set('fcut', '14000')
        eldata.set('fwet', '0')
        
        # Volume envelope
        elvol = ET.SubElement(eldata, 'elvol')
        self._set_envelope_params(elvol)
        
        # Filter cutoff envelope
        elcut = ET.SubElement(eldata, 'elcut')
        self._set_envelope_params(elcut)
        
        # Filter resonance envelope
        elres = ET.SubElement(eldata, 'elres')
        self._set_envelope_params(elres)
    
    def _set_envelope_params(self, env: ET.Element):
        """Set default envelope parameters"""
        env.set('att', '0')
        env.set('dec', '0.5')
        env.set('sus', '0.5')
        env.set('rel', '0.1')
        env.set('hold', '0.5')
        env.set('amt', '0')
        env.set('lamt', '0')
        env.set('x100', '0')
        env.set('pdel', '0')
        env.set('lpdel', '0')
        env.set('latt', '0')
        env.set('lspd', '0.1')
        env.set('lshp', '0')
        env.set('userwavefile', '')
        env.set('syncmode', '0')
        env.set('ctlenvamt', '0')
        env.set('lspd_numerator', '4')
        env.set('lspd_denominator', '4')


class TrackController:
    """Controls individual tracks and their parameters"""
    
    def __init__(self, project: LMMSProject):
        self.project = project
    
    def set_volume(self, track_name: str, volume: int):
        """Set track volume (0-100)"""
        track = self.project.get_track_by_name(track_name)
        if track:
            inst_track = track.find('instrumenttrack')
            if inst_track:
                inst_track.set('vol', str(volume))
                return True
        return False
    
    def set_pan(self, track_name: str, pan: int):
        """Set track panning (-100 to 100)"""
        track = self.project.get_track_by_name(track_name)
        if track:
            inst_track = track.find('instrumenttrack')
            if inst_track:
                inst_track.set('pan', str(pan))
                return True
        return False
    
    def set_pitch(self, track_name: str, pitch: int):
        """Set track pitch offset in semitones"""
        track = self.project.get_track_by_name(track_name)
        if track:
            inst_track = track.find('instrumenttrack')
            if inst_track:
                inst_track.set('pitch', str(pitch))
                return True
        return False
    
    def mute_track(self, track_name: str, muted: bool = True):
        """Mute or unmute a track"""
        track = self.project.get_track_by_name(track_name)
        if track:
            track.set('muted', '1' if muted else '0')
            return True
        return False
    
    def set_mixer_channel(self, track_name: str, channel: int):
        """Assign track to mixer channel (0-63)"""
        track = self.project.get_track_by_name(track_name)
        if track:
            inst_track = track.find('instrumenttrack')
            if inst_track:
                inst_track.set('mixch', str(channel))
                return True
        return False


class InstrumentController:
    """Controls instrument parameters"""
    
    def __init__(self, project: LMMSProject):
        self.project = project
    
    def set_kicker_params(self, track_name: str, **params):
        """
        Set Kicker drum synthesizer parameters:
        - start: Start frequency (Hz)
        - end: End frequency (Hz)
        - decay: Decay time (ms)
        - dist: Distortion amount (0-1)
        - gain: Overall gain (0-1)
        - noise: Noise amount (0-1)
        - startclick: Click amount (0-1)
        - slope: Frequency slope
        - env: Envelope slope
        """
        track = self.project.get_track_by_name(track_name)
        if not track:
            return False
        
        kicker = track.find('.//instrument[@name="kicker"]/kicker')
        if kicker is None:
            return False
        
        for param, value in params.items():
            if param in ['start', 'end', 'decay', 'dist', 'diststart', 'distend',
                        'gain', 'noise', 'startclick', 'slope', 'env']:
                kicker.set(param, str(value))
        
        return True
    
    def set_tripleoscillator_params(self, track_name: str, osc_num: int, **params):
        """
        Set TripleOscillator parameters for a specific oscillator (0-2):
        - vol: Volume (0-100)
        - pan: Panning (-100 to 100)
        - coarse: Coarse detune (semitones)
        - finel: Fine detune left (cents)
        - finer: Fine detune right (cents)
        - wavetype: Waveform (0=sine, 1=triangle, 2=saw, 3=square, 4=noise, etc.)
        - phoffset: Phase offset (0-360)
        """
        track = self.project.get_track_by_name(track_name)
        if not track:
            return False
        
        osc = track.find('.//instrument[@name="tripleoscillator"]/tripleoscillator')
        if osc is None:
            return False
        
        for param, value in params.items():
            if param in ['vol', 'pan', 'coarse', 'finel', 'finer', 'wavetype', 'phoffset']:
                osc.set(f'{param}{osc_num}', str(value))
        
        return True
    
    def set_envelope(self, track_name: str, env_type: str, **params):
        """
        Set envelope parameters:
        - env_type: 'vol', 'cut', or 'res'
        - att: Attack time
        - dec: Decay time
        - sus: Sustain level
        - rel: Release time
        - hold: Hold time
        - amt: Envelope amount
        """
        track = self.project.get_track_by_name(track_name)
        if not track:
            return False
        
        env = track.find(f'.//el{env_type}')
        if env is None:
            return False
        
        for param, value in params.items():
            if param in ['att', 'dec', 'sus', 'rel', 'hold', 'amt']:
                env.set(param, str(value))
        
        return True
    
    def set_filter(self, track_name: str, **params):
        """
        Set filter parameters:
        - fcut: Cutoff frequency (Hz)
        - fres: Resonance (0-1)
        - ftype: Filter type (0=lowpass, 1=highpass, 2=bandpass, etc.)
        - fwet: Wet/dry mix (0-1)
        """
        track = self.project.get_track_by_name(track_name)
        if not track:
            return False
        
        eldata = track.find('.//eldata')
        if eldata is None:
            return False
        
        for param, value in params.items():
            if param in ['fcut', 'fres', 'ftype', 'fwet']:
                eldata.set(param, str(value))
        
        return True


class EffectsController:
    """Controls effects and effect chains"""
    
    def __init__(self, project: LMMSProject):
        self.project = project
    
    def add_effect(self, track_name: str, effect_type: str, **params) -> bool:
        """Add an effect to a track's effect chain"""
        track = self.project.get_track_by_name(track_name)
        if not track:
            return False
        
        fxchain = track.find('.//fxchain')
        if fxchain is None:
            return False
        
        # Create effect element
        effect = ET.SubElement(fxchain, 'effect')
        effect.set('name', effect_type)
        
        # Add effect-specific parameters
        self._add_effect_params(effect, effect_type, params)
        
        # Update effect count
        num_effects = int(fxchain.get('numofeffects', '0'))
        fxchain.set('numofeffects', str(num_effects + 1))
        fxchain.set('enabled', '1')
        
        return True
    
    def _add_effect_params(self, effect: ET.Element, effect_type: str, params: dict):
        """Add effect-specific parameters"""
        if effect_type == 'ladspaeffect':
            # LADSPA effect parameters
            key = ET.SubElement(effect, 'ladspacontrols')
            for param, value in params.items():
                key.set(param, str(value))
        elif effect_type == 'bassbooster':
            bb = ET.SubElement(effect, 'bassbooster')
            bb.set('freq', params.get('freq', '100'))
            bb.set('gain', params.get('gain', '1'))
            bb.set('ratio', params.get('ratio', '1'))
        # Add more effect types as needed
    
    def remove_effect(self, track_name: str, effect_index: int) -> bool:
        """Remove an effect from the chain by index"""
        track = self.project.get_track_by_name(track_name)
        if not track:
            return False
        
        fxchain = track.find('.//fxchain')
        if fxchain is None:
            return False
        
        effects = fxchain.findall('effect')
        if 0 <= effect_index < len(effects):
            fxchain.remove(effects[effect_index])
            
            # Update effect count
            fxchain.set('numofeffects', str(len(effects) - 1))
            if len(effects) == 1:
                fxchain.set('enabled', '0')
            
            return True
        return False


class AutomationController:
    """Controls automation patterns and curves"""
    
    def __init__(self, project: LMMSProject):
        self.project = project
    
    def add_automation_pattern(self, param_name: str, values: List[Tuple[int, float]]):
        """
        Add an automation pattern
        values: List of (position, value) tuples
        """
        auto_track = self.root.find('.//track[@type="6"]')
        if auto_track is None:
            # Create automation track if it doesn't exist
            song = self.root.find('.//song')
            auto_track = ET.SubElement(song, 'track')
            auto_track.set('type', '6')
            auto_track.set('name', 'Automation track')
            auto_track.set('muted', '0')
            ET.SubElement(auto_track, 'automationtrack')
        
        # Create automation pattern
        pattern = ET.SubElement(auto_track, 'automationpattern')
        pattern.set('name', param_name)
        pattern.set('pos', '0')
        
        # Add time points
        for pos, value in values:
            time = ET.SubElement(pattern, 'time')
            time.set('pos', str(pos))
            time.set('value', str(value))
        
        return True


class LMMSController:
    """High-level controller for LMMS - main interface for GPT-5"""
    
    def __init__(self, project_path: Optional[str] = None):
        if project_path:
            self.project = LMMSProject(project_path)
        else:
            # Create new project from template
            self.project = LMMSProject()
            self._create_new_project()
        
        self.tracks = TrackController(self.project)
        self.instruments = InstrumentController(self.project)
        self.effects = EffectsController(self.project)
        self.automation = AutomationController(self.project)
    
    def _create_new_project(self):
        """Create a new empty project"""
        # Load empty project template
        template_path = "/Users/andymu/Desktop/projects/lmms/tests/emptyproject.mmp"
        if os.path.exists(template_path):
            self.project.load(template_path)
        else:
            # Create minimal project structure
            root = ET.Element('multimedia-project')
            root.set('version', '1.0')
            root.set('type', 'song')
            
            # Add head
            head = ET.SubElement(root, 'head')
            head.set('bpm', '140')
            head.set('timesig_numerator', '4')
            head.set('timesig_denominator', '4')
            head.set('mastervol', '100')
            head.set('masterpitch', '0')
            
            # Add song structure
            song = ET.SubElement(root, 'song')
            trackcontainer = ET.SubElement(song, 'trackcontainer')
            trackcontainer.set('type', 'song')
            
            self.project.root = root
            self.project.tree = ET.ElementTree(root)
    
    def save_project(self, filepath: str):
        """Save the current project"""
        self.project.save(filepath)
    
    def load_project(self, filepath: str):
        """Load a project file"""
        self.project.load(filepath)
        return True
    
    def add_kick_track(self, name: str = "Kick") -> str:
        """Add a kick drum track with Kicker instrument"""
        track = self.project.add_instrument_track(name, "kicker")
        return f"Added kick track: {name}"
    
    def add_synth_track(self, name: str = "Synth") -> str:
        """Add a synthesizer track with TripleOscillator"""
        track = self.project.add_instrument_track(name, "tripleoscillator")
        return f"Added synth track: {name}"
    
    def set_tempo(self, bpm: int):
        """Set project tempo"""
        head = self.project.root.find('.//head')
        if head is not None:
            head.set('bpm', str(bpm))
            return f"Tempo set to {bpm} BPM"
        return "Failed to set tempo"
    
    def get_info(self) -> dict:
        """Get project information"""
        info = {
            'tracks': [],
            'tempo': None,
            'time_signature': None
        }
        
        # Get tempo and time signature
        head = self.project.root.find('.//head')
        if head:
            info['tempo'] = int(head.get('bpm', '140'))
            info['time_signature'] = f"{head.get('timesig_numerator', '4')}/{head.get('timesig_denominator', '4')}"
        
        # Get track info
        for track in self.project.get_tracks():
            track_info = {
                'name': track.get('name'),
                'type': track.get('type'),
                'muted': track.get('muted') == '1'
            }
            
            # Get instrument info
            inst = track.find('.//instrument')
            if inst:
                track_info['instrument'] = inst.get('name')
            
            info['tracks'].append(track_info)
        
        return info
    
    def list_available_tools(self) -> dict:
        """List all available control methods for GPT-5"""
        return {
            "project_management": [
                "load_project(filepath)",
                "save_project(filepath)",
                "get_info()"
            ],
            "track_control": [
                "add_kick_track(name)",
                "add_synth_track(name)",
                "tracks.set_volume(track_name, volume)",
                "tracks.set_pan(track_name, pan)",
                "tracks.set_pitch(track_name, pitch)",
                "tracks.mute_track(track_name, muted)",
                "tracks.set_mixer_channel(track_name, channel)"
            ],
            "instrument_control": [
                "instruments.set_kicker_params(track_name, **params)",
                "instruments.set_tripleoscillator_params(track_name, osc_num, **params)",
                "instruments.set_envelope(track_name, env_type, **params)",
                "instruments.set_filter(track_name, **params)"
            ],
            "effects_control": [
                "effects.add_effect(track_name, effect_type, **params)",
                "effects.remove_effect(track_name, effect_index)"
            ],
            "automation_control": [
                "automation.add_automation_pattern(param_name, values)"
            ],
            "global_control": [
                "set_tempo(bpm)"
            ]
        }


# Command-line interface for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("LMMS Controller - Programmatic interface for LMMS")
        print("\nUsage:")
        print("  python lmms_controller.py <command> [args...]")
        print("\nCommands:")
        print("  info <project.mmp>          - Show project information")
        print("  create <output.mmp>         - Create new project")
        print("  add_kick <project> <name>   - Add kick track")
        print("  set_tempo <project> <bpm>   - Set project tempo")
        print("  list_tools                  - List available control methods")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list_tools":
        controller = LMMSController()
        tools = controller.list_available_tools()
        print(json.dumps(tools, indent=2))
    
    elif command == "info" and len(sys.argv) >= 3:
        controller = LMMSController(sys.argv[2])
        info = controller.get_info()
        print(json.dumps(info, indent=2))
    
    elif command == "create" and len(sys.argv) >= 3:
        controller = LMMSController()
        controller.save_project(sys.argv[2])
        print(f"Created new project: {sys.argv[2]}")
    
    elif command == "add_kick" and len(sys.argv) >= 4:
        controller = LMMSController(sys.argv[2])
        name = sys.argv[3] if len(sys.argv) > 3 else "Kick"
        result = controller.add_kick_track(name)
        controller.save_project(sys.argv[2])
        print(result)
    
    elif command == "set_tempo" and len(sys.argv) >= 4:
        controller = LMMSController(sys.argv[2])
        result = controller.set_tempo(int(sys.argv[3]))
        controller.save_project(sys.argv[2])
        print(result)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)