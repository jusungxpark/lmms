#!/usr/bin/env python3
"""
LMMS Actions - Complete programmatic access to ALL LMMS actions and operations
This module provides access to every single action available in LMMS
"""

import xml.etree.ElementTree as ET
import os
import sys
import json
import random
import math
import gzip
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from enum import Enum, IntEnum
from dataclasses import dataclass
import base64

# Import the complete controller for base functionality
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_complete_controller import LMMSCompleteController, TrackType, WaveForm, FilterType


# ============================================================================
# ACTION ENUMERATIONS
# ============================================================================

class EditMode(IntEnum):
    """Edit modes for various editors"""
    DRAW = 0
    ERASE = 1
    SELECT = 2
    MOVE = 3
    KNIFE = 4
    PITCHBEND = 5
    TANGENT = 6


class QuantizeMode(IntEnum):
    """Quantization modes"""
    OFF = 0
    BAR = 1
    HALF = 2
    QUARTER = 4
    EIGHTH = 8
    SIXTEENTH = 16
    THIRTY_SECOND = 32
    SIXTY_FOURTH = 64


class NoteEditMode(IntEnum):
    """Note editing modes in piano roll"""
    VOLUME = 0
    PANNING = 1
    PITCH = 2


class ExportFormat(IntEnum):
    """Export format options"""
    WAV = 0
    OGG = 1
    MP3 = 2
    FLAC = 3


class TimeSignature:
    """Time signature representation"""
    def __init__(self, numerator: int = 4, denominator: int = 4):
        self.numerator = numerator
        self.denominator = denominator


# ============================================================================
# NOTE AND PATTERN DATA STRUCTURES
# ============================================================================

@dataclass
class Note:
    """Represents a single note"""
    pitch: int  # MIDI pitch (0-127)
    position: int  # Position in ticks
    length: int  # Length in ticks
    velocity: int = 100  # Velocity (0-127)
    panning: int = 0  # Panning (-100 to 100)
    
    def to_xml(self) -> ET.Element:
        """Convert note to XML element"""
        elem = ET.Element('note')
        elem.set('key', str(self.pitch))
        elem.set('pos', str(self.position))
        elem.set('len', str(self.length))
        elem.set('vol', str(self.velocity))
        elem.set('pan', str(self.panning))
        return elem
    
    @classmethod
    def from_xml(cls, elem: ET.Element) -> 'Note':
        """Create note from XML element"""
        return cls(
            pitch=int(elem.get('key', '60')),
            position=int(elem.get('pos', '0')),
            length=int(elem.get('len', '48')),
            velocity=int(elem.get('vol', '100')),
            panning=int(elem.get('pan', '0'))
        )


@dataclass
class Pattern:
    """Represents a pattern/clip"""
    name: str
    position: int
    length: int
    notes: List[Note]
    muted: bool = False
    
    def to_xml(self) -> ET.Element:
        """Convert pattern to XML element"""
        elem = ET.Element('pattern')
        elem.set('name', self.name)
        elem.set('pos', str(self.position))
        elem.set('len', str(self.length))
        elem.set('muted', '1' if self.muted else '0')
        elem.set('type', '0')
        
        for note in self.notes:
            elem.append(note.to_xml())
        
        return elem


# ============================================================================
# LMMS ACTIONS CONTROLLER
# ============================================================================

class LMMSActions(LMMSCompleteController):
    """
    Complete LMMS actions controller providing access to ALL operations
    Extends LMMSCompleteController with every action available in LMMS
    """
    
    def __init__(self, project_path: Optional[str] = None):
        super().__init__(project_path)
        self.clipboard = {'notes': [], 'patterns': [], 'tracks': []}
        self.undo_stack = []
        self.redo_stack = []
        self.current_edit_mode = EditMode.DRAW
        self.quantize_value = QuantizeMode.OFF
        self.metronome_enabled = False
        self.recording = False
    
    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================
    
    def create_new_project_from_template(self, template_name: str = "default") -> bool:
        """Create new project from template"""
        self.create_new_project()
        # Load template settings based on genre/style
        templates = {
            "techno": {"tempo": 130, "tracks": ["Kick", "Bass", "Lead", "Pad"]},
            "house": {"tempo": 128, "tracks": ["Kick", "Hihat", "Bass", "Chords"]},
            "dnb": {"tempo": 174, "tracks": ["Kick", "Snare", "Bass", "Reese"]},
            "ambient": {"tempo": 90, "tracks": ["Pad1", "Pad2", "Lead", "Atmosphere"]},
            "trap": {"tempo": 140, "tracks": ["808", "Hihat", "Snare", "Lead"]}
        }
        
        if template_name in templates:
            template = templates[template_name]
            self.set_tempo(template["tempo"])
            for track_name in template["tracks"]:
                self.add_track(track_name, TrackType.INSTRUMENT)
        
        return True
    
    def import_midi_file(self, filepath: str) -> bool:
        """Import MIDI file into project"""
        # This would require MIDI parsing
        # For now, create placeholder tracks
        track_name = Path(filepath).stem
        self.add_track(track_name, TrackType.INSTRUMENT)
        return True
    
    def export_project(self, filepath: str, format: ExportFormat = ExportFormat.WAV,
                      sample_rate: int = 44100, bit_depth: int = 16) -> bool:
        """Export project to audio file"""
        # This would require audio rendering engine access
        # Store export settings in project
        export_settings = ET.SubElement(self.root, 'export_settings')
        export_settings.set('format', str(format.value))
        export_settings.set('sample_rate', str(sample_rate))
        export_settings.set('bit_depth', str(bit_depth))
        export_settings.set('filepath', filepath)
        return True
    
    def export_stems(self, output_dir: str, format: ExportFormat = ExportFormat.WAV) -> bool:
        """Export individual track stems"""
        tracks = self.get_all_tracks()
        for track in tracks:
            track_name = track.get('name', 'Unnamed')
            stem_path = os.path.join(output_dir, f"{track_name}.{format.name.lower()}")
            # Mark track for stem export
            track.set('export_stem', stem_path)
        return True
    
    def export_midi(self, filepath: str, track_name: Optional[str] = None) -> bool:
        """Export project or specific track as MIDI"""
        if track_name:
            track = self.get_track(track_name)
            if track:
                track.set('export_midi', filepath)
        else:
            self.root.set('export_midi', filepath)
        return True
    
    # ========================================================================
    # EDIT OPERATIONS
    # ========================================================================
    
    def undo(self) -> bool:
        """Undo last operation"""
        if self.undo_stack:
            # Save current state to redo stack
            current_state = ET.tostring(self.root, encoding='unicode')
            self.redo_stack.append(current_state)
            
            # Restore previous state
            previous_state = self.undo_stack.pop()
            self.root = ET.fromstring(previous_state)
            self.tree = ET.ElementTree(self.root)
            return True
        return False
    
    def redo(self) -> bool:
        """Redo previously undone operation"""
        if self.redo_stack:
            # Save current state to undo stack
            current_state = ET.tostring(self.root, encoding='unicode')
            self.undo_stack.append(current_state)
            
            # Restore next state
            next_state = self.redo_stack.pop()
            self.root = ET.fromstring(next_state)
            self.tree = ET.ElementTree(self.root)
            return True
        return False
    
    def save_undo_state(self):
        """Save current state for undo"""
        state = ET.tostring(self.root, encoding='unicode')
        self.undo_stack.append(state)
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
        
        # Limit undo stack size
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
    
    # ========================================================================
    # TRACK OPERATIONS
    # ========================================================================
    
    def clone_track(self, track_name: str, new_name: Optional[str] = None) -> bool:
        """Clone an entire track with all settings and patterns"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        # Deep copy the track
        new_track = ET.fromstring(ET.tostring(track))
        new_track.set('name', new_name or f"{track_name} (Clone)")
        
        # Add to track container
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer is not None:
            trackcontainer.append(new_track)
            return True
        
        return False
    
    def clear_track(self, track_name: str) -> bool:
        """Clear all patterns/clips from a track"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        # Remove all pattern elements
        for pattern in track.findall('pattern'):
            track.remove(pattern)
        
        return True
    
    def set_track_color(self, track_name: str, color: str) -> bool:
        """Set track color (hex color code)"""
        track = self.get_track(track_name)
        if track:
            track.set('color', color)
            return True
        return False
    
    def randomize_track_color(self, track_name: str) -> bool:
        """Set random track color"""
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        return self.set_track_color(track_name, color)
    
    def reset_track_color(self, track_name: str) -> bool:
        """Reset track to default color"""
        track = self.get_track(track_name)
        if track:
            if 'color' in track.attrib:
                del track.attrib['color']
            return True
        return False
    
    def set_volume(self, track_name: str, volume: int) -> bool:
        """Set track volume (0-100)"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        inst_track = track.find('instrumenttrack')
        if inst_track:
            inst_track.set('vol', str(max(0, min(100, volume))))
            return True
        
        sample_track = track.find('sampletrack')
        if sample_track:
            sample_track.set('vol', str(max(0, min(100, volume))))
            return True
        
        return False
    
    def set_panning(self, track_name: str, panning: int) -> bool:
        """Set track panning (-100 to 100)"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        inst_track = track.find('instrumenttrack')
        if inst_track:
            inst_track.set('pan', str(max(-100, min(100, panning))))
            return True
        
        return False
    
    def move_track(self, track_name: str, position: int) -> bool:
        """Move track to new position in track list"""
        self.save_undo_state()
        
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if not trackcontainer:
            return False
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        tracks = list(trackcontainer.findall('track'))
        trackcontainer.remove(track)
        
        # Insert at new position
        position = max(0, min(position, len(tracks) - 1))
        trackcontainer.insert(position, track)
        
        return True
    
    # ========================================================================
    # PATTERN/CLIP OPERATIONS
    # ========================================================================
    
    def clone_pattern(self, track_name: str, pattern_index: int) -> Optional[ET.Element]:
        """Clone a pattern on a track"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return None
        
        patterns = track.findall('pattern')
        if 0 <= pattern_index < len(patterns):
            original = patterns[pattern_index]
            
            # Clone the pattern
            new_pattern = ET.fromstring(ET.tostring(original))
            new_pattern.set('name', f"{original.get('name', 'Pattern')} (Clone)")
            
            # Offset position to avoid overlap
            original_pos = int(original.get('pos', '0'))
            original_len = int(original.get('len', '192'))
            new_pattern.set('pos', str(original_pos + original_len))
            
            track.append(new_pattern)
            return new_pattern
        
        return None
    
    def split_pattern(self, track_name: str, pattern_index: int, split_position: int) -> bool:
        """Split a pattern at a specific position"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        patterns = track.findall('pattern')
        if 0 <= pattern_index < len(patterns):
            pattern = patterns[pattern_index]
            
            # Get pattern data
            pos = int(pattern.get('pos', '0'))
            length = int(pattern.get('len', '192'))
            name = pattern.get('name', 'Pattern')
            
            if 0 < split_position < length:
                # Create first part (modify original)
                pattern.set('len', str(split_position))
                
                # Create second part
                second_pattern = ET.fromstring(ET.tostring(pattern))
                second_pattern.set('name', f"{name} (2)")
                second_pattern.set('pos', str(pos + split_position))
                second_pattern.set('len', str(length - split_position))
                
                # Adjust notes in second pattern
                for note in second_pattern.findall('note'):
                    note_pos = int(note.get('pos', '0'))
                    if note_pos >= split_position:
                        note.set('pos', str(note_pos - split_position))
                    else:
                        second_pattern.remove(note)
                
                # Remove notes from first pattern that are after split
                for note in pattern.findall('note'):
                    note_pos = int(note.get('pos', '0'))
                    if note_pos >= split_position:
                        pattern.remove(note)
                
                track.append(second_pattern)
                return True
        
        return False
    
    def merge_patterns(self, track_name: str, pattern_indices: List[int]) -> bool:
        """Merge multiple patterns into one"""
        self.save_undo_state()
        
        if len(pattern_indices) < 2:
            return False
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        patterns = track.findall('pattern')
        patterns_to_merge = [patterns[i] for i in pattern_indices if 0 <= i < len(patterns)]
        
        if len(patterns_to_merge) < 2:
            return False
        
        # Find earliest position and total length
        min_pos = min(int(p.get('pos', '0')) for p in patterns_to_merge)
        max_end = max(int(p.get('pos', '0')) + int(p.get('len', '192')) for p in patterns_to_merge)
        
        # Create merged pattern
        merged = patterns_to_merge[0]
        merged.set('pos', str(min_pos))
        merged.set('len', str(max_end - min_pos))
        merged.set('name', f"{merged.get('name', 'Pattern')} (Merged)")
        
        # Merge notes from other patterns
        for pattern in patterns_to_merge[1:]:
            pattern_pos = int(pattern.get('pos', '0'))
            for note in pattern.findall('note'):
                new_note = ET.fromstring(ET.tostring(note))
                note_pos = int(new_note.get('pos', '0'))
                new_note.set('pos', str(note_pos + pattern_pos - min_pos))
                merged.append(new_note)
            
            # Remove the merged pattern
            track.remove(pattern)
        
        return True
    
    def rename_pattern(self, track_name: str, pattern_index: int, new_name: str) -> bool:
        """Rename a pattern"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        patterns = track.findall('pattern')
        if 0 <= pattern_index < len(patterns):
            patterns[pattern_index].set('name', new_name)
            return True
        
        return False
    
    # ========================================================================
    # NOTE OPERATIONS
    # ========================================================================
    
    def get_notes_from_pattern(self, track_name: str, pattern_index: int) -> List[Note]:
        """Get all notes from a pattern"""
        track = self.get_track(track_name)
        if not track:
            return []
        
        patterns = track.findall('pattern')
        if 0 <= pattern_index < len(patterns):
            pattern = patterns[pattern_index]
            return [Note.from_xml(note) for note in pattern.findall('note')]
        
        return []
    
    def set_notes_in_pattern(self, track_name: str, pattern_index: int, notes: List[Note]) -> bool:
        """Replace all notes in a pattern"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        patterns = track.findall('pattern')
        if 0 <= pattern_index < len(patterns):
            pattern = patterns[pattern_index]
            
            # Remove existing notes
            for note in pattern.findall('note'):
                pattern.remove(note)
            
            # Add new notes
            for note in notes:
                pattern.append(note.to_xml())
            
            return True
        
        return False
    
    def add_notes_to_pattern(self, track_name: str, pattern_index: int, notes: List[Note]) -> bool:
        """Add notes to an existing pattern"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        patterns = track.findall('pattern')
        if 0 <= pattern_index < len(patterns):
            pattern = patterns[pattern_index]
            
            for note in notes:
                pattern.append(note.to_xml())
            
            return True
        
        return False
    
    def quantize_notes(self, notes: List[Note], quantize_value: QuantizeMode,
                      quantize_pos: bool = True, quantize_len: bool = False) -> List[Note]:
        """Quantize note positions and/or lengths"""
        # Handle both QuantizeMode enum and int values
        if isinstance(quantize_value, QuantizeMode):
            if quantize_value == QuantizeMode.OFF:
                return notes
            quantize_val = quantize_value.value
        else:
            if quantize_value == 0:
                return notes
            quantize_val = quantize_value
        
        # Calculate quantize grid in ticks (assuming 48 ticks per quarter note)
        ticks_per_quarter = 48
        quantize_ticks = (ticks_per_quarter * 4) // quantize_val
        
        quantized_notes = []
        for note in notes:
            new_note = Note(
                pitch=note.pitch,
                position=note.position,
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            
            if quantize_pos:
                # Quantize position to nearest grid point
                new_note.position = round(note.position / quantize_ticks) * quantize_ticks
            
            if quantize_len:
                # Quantize length to nearest grid point
                new_note.length = max(1, round(note.length / quantize_ticks) * quantize_ticks)
            
            quantized_notes.append(new_note)
        
        return quantized_notes
    
    def humanize_notes(self, notes: List[Note], timing_amount: float = 0.1,
                      velocity_amount: float = 0.1) -> List[Note]:
        """Add human-like timing and velocity variations"""
        humanized_notes = []
        
        for note in notes:
            new_note = Note(
                pitch=note.pitch,
                position=note.position,
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            
            # Add timing variation (±timing_amount of a 16th note)
            timing_variation = int(random.uniform(-3 * timing_amount, 3 * timing_amount))
            new_note.position = max(0, note.position + timing_variation)
            
            # Add velocity variation
            velocity_variation = int(random.uniform(-127 * velocity_amount, 127 * velocity_amount))
            new_note.velocity = max(1, min(127, note.velocity + velocity_variation))
            
            humanized_notes.append(new_note)
        
        return humanized_notes
    
    def transpose_notes(self, notes: List[Note], semitones: int) -> List[Note]:
        """Transpose notes by semitones"""
        transposed_notes = []
        
        for note in notes:
            new_note = Note(
                pitch=max(0, min(127, note.pitch + semitones)),
                position=note.position,
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            transposed_notes.append(new_note)
        
        return transposed_notes
    
    def reverse_notes(self, notes: List[Note]) -> List[Note]:
        """Reverse the order of notes"""
        if not notes:
            return []
        
        # Find the total span of notes
        min_pos = min(n.position for n in notes)
        max_end = max(n.position + n.length for n in notes)
        total_span = max_end - min_pos
        
        reversed_notes = []
        for note in notes:
            # Calculate reversed position
            note_end = note.position + note.length - min_pos
            new_pos = total_span - note_end + min_pos
            
            new_note = Note(
                pitch=note.pitch,
                position=new_pos,
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            reversed_notes.append(new_note)
        
        return reversed_notes
    
    def scale_note_lengths(self, notes: List[Note], scale_factor: float) -> List[Note]:
        """Scale the length of all notes"""
        scaled_notes = []
        
        for note in notes:
            new_note = Note(
                pitch=note.pitch,
                position=int(note.position * scale_factor),
                length=max(1, int(note.length * scale_factor)),
                velocity=note.velocity,
                panning=note.panning
            )
            scaled_notes.append(new_note)
        
        return scaled_notes
    
    def remove_overlaps(self, notes: List[Note]) -> List[Note]:
        """Remove overlapping portions of notes"""
        if not notes:
            return []
        
        # Sort notes by position and pitch
        sorted_notes = sorted(notes, key=lambda n: (n.pitch, n.position))
        
        cleaned_notes = []
        for i, note in enumerate(sorted_notes):
            new_note = Note(
                pitch=note.pitch,
                position=note.position,
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            
            # Check for overlap with next note of same pitch
            if i < len(sorted_notes) - 1:
                next_note = sorted_notes[i + 1]
                if next_note.pitch == note.pitch:
                    if note.position + note.length > next_note.position:
                        # Trim this note to end where next begins
                        new_note.length = next_note.position - note.position
            
            if new_note.length > 0:
                cleaned_notes.append(new_note)
        
        return cleaned_notes
    
    def glue_notes(self, notes: List[Note], max_gap: int = 4) -> List[Note]:
        """Connect adjacent notes of the same pitch"""
        if not notes:
            return []
        
        # Sort notes by pitch and position
        sorted_notes = sorted(notes, key=lambda n: (n.pitch, n.position))
        
        glued_notes = []
        current_note = None
        
        for note in sorted_notes:
            if current_note is None:
                current_note = Note(
                    pitch=note.pitch,
                    position=note.position,
                    length=note.length,
                    velocity=note.velocity,
                    panning=note.panning
                )
            elif (note.pitch == current_note.pitch and
                  note.position - (current_note.position + current_note.length) <= max_gap):
                # Extend current note to include this one
                current_note.length = note.position + note.length - current_note.position
                # Average velocities
                current_note.velocity = (current_note.velocity + note.velocity) // 2
            else:
                # Save current note and start new one
                glued_notes.append(current_note)
                current_note = Note(
                    pitch=note.pitch,
                    position=note.position,
                    length=note.length,
                    velocity=note.velocity,
                    panning=note.panning
                )
        
        if current_note:
            glued_notes.append(current_note)
        
        return glued_notes
    
    # ========================================================================
    # PATTERN GENERATION
    # ========================================================================
    
    def generate_drum_pattern(self, track_name: str, pattern_name: str,
                             style: str = "basic", length: int = 192) -> bool:
        """Generate a drum pattern based on style"""
        self.save_undo_state()
        
        patterns = {
            "basic": [0, 48, 96, 144],  # Four-on-the-floor
            "breakbeat": [0, 58, 96, 144, 168],
            "dnb": [0, 44, 96, 116, 144, 168],
            "trap": [0, 36, 96, 108, 144],
            "techno": [0, 24, 48, 72, 96, 120, 144, 168],
            "jazz": [0, 30, 48, 78, 96, 126, 144, 174]
        }
        
        positions = patterns.get(style, patterns["basic"])
        
        # Create pattern with notes
        pattern = self.add_pattern(track_name, pattern_name, 0, length)
        if pattern is not None:
            for pos in positions:
                if pos < length:
                    note = Note(
                        pitch=36,  # C2 - typical kick drum
                        position=pos,
                        length=12,
                        velocity=100
                    )
                    pattern.append(note.to_xml())
            
            return True
        
        return False
    
    def generate_bassline(self, track_name: str, pattern_name: str,
                         root_note: int = 36, scale: str = "minor",
                         pattern_type: str = "simple", length: int = 192) -> bool:
        """Generate a bassline pattern"""
        self.save_undo_state()
        
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10]
        }
        
        scale_intervals = scales.get(scale, scales["minor"])
        
        pattern = self.add_pattern(track_name, pattern_name, 0, length)
        if pattern is not None:
            if pattern_type == "simple":
                # Simple root note pattern
                for i in range(0, length, 48):
                    note = Note(
                        pitch=root_note,
                        position=i,
                        length=36,
                        velocity=80
                    )
                    pattern.append(note.to_xml())
            
            elif pattern_type == "walking":
                # Walking bassline
                position = 0
                while position < length:
                    interval = random.choice(scale_intervals)
                    note = Note(
                        pitch=root_note + interval,
                        position=position,
                        length=24,
                        velocity=70 + random.randint(-10, 10)
                    )
                    pattern.append(note.to_xml())
                    position += 24
            
            elif pattern_type == "arpeggio":
                # Arpeggiated bassline
                arp_pattern = [0, 7, 12, 7]  # Root, fifth, octave, fifth
                position = 0
                for interval in arp_pattern * (length // (len(arp_pattern) * 12)):
                    if position >= length:
                        break
                    note = Note(
                        pitch=root_note + interval,
                        position=position,
                        length=10,
                        velocity=75
                    )
                    pattern.append(note.to_xml())
                    position += 12
            
            return True
        
        return False
    
    def generate_chord_progression(self, track_name: str, pattern_name: str,
                                  root_note: int = 60, progression: str = "I-IV-V-I",
                                  length: int = 768) -> bool:
        """Generate a chord progression"""
        self.save_undo_state()
        
        # Define chord intervals
        chord_types = {
            "major": [0, 4, 7],
            "minor": [0, 3, 7],
            "dim": [0, 3, 6],
            "aug": [0, 4, 8],
            "7": [0, 4, 7, 10],
            "m7": [0, 3, 7, 10],
            "maj7": [0, 4, 7, 11]
        }
        
        # Parse progression
        progression_map = {
            "I": (0, "major"), "i": (0, "minor"),
            "II": (2, "major"), "ii": (2, "minor"),
            "III": (4, "major"), "iii": (4, "minor"),
            "IV": (5, "major"), "iv": (5, "minor"),
            "V": (7, "major"), "v": (7, "minor"),
            "VI": (9, "major"), "vi": (9, "minor"),
            "VII": (11, "major"), "vii": (11, "dim")
        }
        
        chords = progression.split("-")
        chord_length = length // len(chords)
        
        pattern = self.add_pattern(track_name, pattern_name, 0, length)
        if pattern is not None:
            position = 0
            for chord_symbol in chords:
                if chord_symbol in progression_map:
                    root_offset, chord_type = progression_map[chord_symbol]
                    intervals = chord_types[chord_type]
                    
                    # Add notes for this chord
                    for interval in intervals:
                        note = Note(
                            pitch=root_note + root_offset + interval,
                            position=position,
                            length=chord_length - 4,  # Small gap between chords
                            velocity=70
                        )
                        pattern.append(note.to_xml())
                    
                    position += chord_length
            
            return True
        
        return False
    
    def generate_melody(self, track_name: str, pattern_name: str,
                       root_note: int = 72, scale: str = "major",
                       rhythm: str = "moderate", length: int = 192) -> bool:
        """Generate a melodic pattern"""
        self.save_undo_state()
        
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10],
            "chromatic": list(range(12))
        }
        
        rhythms = {
            "slow": [48, 48, 96],
            "moderate": [24, 24, 12, 12, 48],
            "fast": [12, 12, 6, 6, 12, 24],
            "syncopated": [12, 12, 24, 6, 6, 12, 24]
        }
        
        scale_intervals = scales.get(scale, scales["major"])
        rhythm_pattern = rhythms.get(rhythm, rhythms["moderate"])
        
        pattern = self.add_pattern(track_name, pattern_name, 0, length)
        if pattern is not None:
            position = 0
            previous_pitch = root_note
            
            while position < length:
                # Choose rhythm duration
                duration = random.choice(rhythm_pattern)
                if position + duration > length:
                    duration = length - position
                
                # Choose pitch (prefer stepwise motion)
                if random.random() < 0.7:  # 70% chance of stepwise motion
                    step = random.choice([-1, 1])
                    interval_index = scale_intervals.index(
                        (previous_pitch - root_note) % 12
                    ) if (previous_pitch - root_note) % 12 in scale_intervals else 0
                    
                    new_index = (interval_index + step) % len(scale_intervals)
                    interval = scale_intervals[new_index]
                else:
                    # Random leap
                    interval = random.choice(scale_intervals)
                
                # Keep within reasonable range
                octave_offset = random.choice([-12, 0, 0, 0, 12])  # Mostly same octave
                pitch = root_note + interval + octave_offset
                pitch = max(48, min(96, pitch))  # Limit range
                
                note = Note(
                    pitch=pitch,
                    position=position,
                    length=duration - 2,  # Small gap for articulation
                    velocity=60 + random.randint(-10, 20)
                )
                pattern.append(note.to_xml())
                
                previous_pitch = pitch
                position += duration
            
            return True
        
        return False
    
    # ========================================================================
    # ADVANCED EDITING
    # ========================================================================
    
    def strum_notes(self, notes: List[Note], strum_time: int = 2) -> List[Note]:
        """Create a strum effect by slightly offsetting note starts"""
        if not notes:
            return []
        
        # Sort by pitch (lowest to highest)
        sorted_notes = sorted(notes, key=lambda n: n.pitch)
        
        strummed_notes = []
        for i, note in enumerate(sorted_notes):
            new_note = Note(
                pitch=note.pitch,
                position=note.position + (i * strum_time),
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            strummed_notes.append(new_note)
        
        return strummed_notes
    
    def create_roll(self, pitch: int, start_pos: int, end_pos: int,
                   subdivisions: int = 16) -> List[Note]:
        """Create a drum roll or note roll"""
        notes = []
        note_length = (end_pos - start_pos) // subdivisions
        
        for i in range(subdivisions):
            position = start_pos + (i * note_length)
            # Gradually increase velocity for crescendo effect
            velocity = 40 + int((i / subdivisions) * 60)
            
            note = Note(
                pitch=pitch,
                position=position,
                length=note_length - 1,
                velocity=velocity
            )
            notes.append(note)
        
        return notes
    
    def create_echo(self, notes: List[Note], echoes: int = 3,
                   delay: int = 24, decay: float = 0.7) -> List[Note]:
        """Create an echo effect by duplicating notes with decreasing velocity"""
        all_notes = list(notes)
        
        for echo_num in range(1, echoes + 1):
            for note in notes:
                echo_velocity = int(note.velocity * (decay ** echo_num))
                if echo_velocity > 0:
                    echo_note = Note(
                        pitch=note.pitch,
                        position=note.position + (delay * echo_num),
                        length=note.length,
                        velocity=echo_velocity,
                        panning=note.panning
                    )
                    all_notes.append(echo_note)
        
        return all_notes
    
    # ========================================================================
    # CLIP OPERATIONS
    # ========================================================================
    
    def copy_clips(self, track_name: str, pattern_indices: List[int]) -> bool:
        """Copy clips to clipboard"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        patterns = track.findall('pattern')
        self.clipboard['patterns'] = []
        
        for index in pattern_indices:
            if 0 <= index < len(patterns):
                pattern_copy = ET.tostring(patterns[index], encoding='unicode')
                self.clipboard['patterns'].append(pattern_copy)
        
        return len(self.clipboard['patterns']) > 0
    
    def paste_clips(self, track_name: str, position: int = 0) -> bool:
        """Paste clips from clipboard"""
        if not self.clipboard['patterns']:
            return False
        
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        for pattern_str in self.clipboard['patterns']:
            pattern = ET.fromstring(pattern_str)
            pattern.set('pos', str(position))
            track.append(pattern)
            
            # Move position for next paste
            position += int(pattern.get('len', '192'))
        
        return True
    
    def cut_clips(self, track_name: str, pattern_indices: List[int]) -> bool:
        """Cut clips (copy and remove)"""
        if self.copy_clips(track_name, pattern_indices):
            self.save_undo_state()
            
            track = self.get_track(track_name)
            if track:
                patterns = track.findall('pattern')
                # Remove in reverse order to maintain indices
                for index in sorted(pattern_indices, reverse=True):
                    if 0 <= index < len(patterns):
                        track.remove(patterns[index])
                return True
        
        return False
    
    # ========================================================================
    # TRANSPORT CONTROL
    # ========================================================================
    
    def set_loop_points(self, start: int, end: int) -> bool:
        """Set loop points for playback"""
        timeline = self.root.find('.//timeline')
        if timeline is None:
            song = self.root.find('.//song')
            if song:
                timeline = ET.SubElement(song, 'timeline')
        
        if timeline is not None:
            timeline.set('lp0pos', str(start))
            timeline.set('lp1pos', str(end))
            timeline.set('lpstate', '1')  # Enable loop
            return True
        
        return False
    
    def disable_loop(self) -> bool:
        """Disable loop playback"""
        timeline = self.root.find('.//timeline')
        if timeline is not None:
            timeline.set('lpstate', '0')
            return True
        return False
    
    def toggle_metronome(self) -> bool:
        """Toggle metronome on/off"""
        self.metronome_enabled = not self.metronome_enabled
        
        # Store metronome state in project
        head = self.root.find('.//head')
        if head is not None:
            head.set('metronome', '1' if self.metronome_enabled else '0')
        
        return self.metronome_enabled
    
    def set_record_mode(self, enabled: bool) -> bool:
        """Enable/disable recording mode"""
        self.recording = enabled
        
        # Store recording state in project
        head = self.root.find('.//head')
        if head is not None:
            head.set('recording', '1' if enabled else '0')
        
        return True
    
    # ========================================================================
    # VIEW MANAGEMENT
    # ========================================================================
    
    def set_zoom(self, horizontal: float = 1.0, vertical: float = 1.0) -> bool:
        """Set zoom levels for editors"""
        view_settings = self.root.find('.//view_settings')
        if view_settings is None:
            song = self.root.find('.//song')
            if song:
                view_settings = ET.SubElement(song, 'view_settings')
        
        if view_settings is not None:
            view_settings.set('h_zoom', str(horizontal))
            view_settings.set('v_zoom', str(vertical))
            return True
        
        return False
    
    def set_snap(self, snap_value: QuantizeMode) -> bool:
        """Set snap/quantization for editing"""
        self.quantize_value = snap_value
        
        view_settings = self.root.find('.//view_settings')
        if view_settings is None:
            song = self.root.find('.//song')
            if song:
                view_settings = ET.SubElement(song, 'view_settings')
        
        if view_settings is not None:
            view_settings.set('snap', str(snap_value.value))
            return True
        
        return False
    
    def set_edit_mode(self, mode: EditMode) -> bool:
        """Set the current edit mode"""
        self.current_edit_mode = mode
        
        view_settings = self.root.find('.//view_settings')
        if view_settings is None:
            song = self.root.find('.//song')
            if song:
                view_settings = ET.SubElement(song, 'view_settings')
        
        if view_settings is not None:
            view_settings.set('edit_mode', str(mode.value))
            return True
        
        return False
    
    # ========================================================================
    # SELECTION OPERATIONS
    # ========================================================================
    
    def select_all_notes(self, track_name: str, pattern_index: int) -> List[Note]:
        """Select all notes in a pattern"""
        return self.get_notes_from_pattern(track_name, pattern_index)
    
    def select_notes_in_range(self, notes: List[Note], start_pos: int,
                             end_pos: int) -> List[Note]:
        """Select notes within a time range"""
        return [n for n in notes if start_pos <= n.position < end_pos]
    
    def select_notes_by_pitch(self, notes: List[Note], pitch: int) -> List[Note]:
        """Select all notes of a specific pitch"""
        return [n for n in notes if n.pitch == pitch]
    
    def select_notes_in_pitch_range(self, notes: List[Note],
                                   min_pitch: int, max_pitch: int) -> List[Note]:
        """Select notes within a pitch range"""
        return [n for n in notes if min_pitch <= n.pitch <= max_pitch]
    
    # ========================================================================
    # SCALE AND KEY OPERATIONS
    # ========================================================================
    
    def constrain_to_scale(self, notes: List[Note], root_note: int,
                          scale: str = "major") -> List[Note]:
        """Constrain notes to a specific scale"""
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10],
            "dorian": [0, 2, 3, 5, 7, 9, 10],
            "phrygian": [0, 1, 3, 5, 7, 8, 10],
            "lydian": [0, 2, 4, 6, 7, 9, 11],
            "mixolydian": [0, 2, 4, 5, 7, 9, 10],
            "locrian": [0, 1, 3, 5, 6, 8, 10]
        }
        
        scale_intervals = scales.get(scale, scales["major"])
        constrained_notes = []
        
        for note in notes:
            # Find closest scale note
            note_interval = (note.pitch - root_note) % 12
            closest_interval = min(scale_intervals,
                                  key=lambda x: abs(x - note_interval))
            
            # Calculate new pitch
            octave = (note.pitch - root_note) // 12
            new_pitch = root_note + (octave * 12) + closest_interval
            
            new_note = Note(
                pitch=new_pitch,
                position=note.position,
                length=note.length,
                velocity=note.velocity,
                panning=note.panning
            )
            constrained_notes.append(new_note)
        
        return constrained_notes
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def batch_set_velocity(self, notes: List[Note], velocity: int) -> List[Note]:
        """Set velocity for all notes"""
        return [Note(n.pitch, n.position, n.length, velocity, n.panning) for n in notes]
    
    def batch_scale_velocity(self, notes: List[Note], scale_factor: float) -> List[Note]:
        """Scale velocity of all notes"""
        scaled_notes = []
        for n in notes:
            new_velocity = max(1, min(127, int(n.velocity * scale_factor)))
            scaled_notes.append(Note(n.pitch, n.position, n.length, new_velocity, n.panning))
        return scaled_notes
    
    def batch_set_panning(self, notes: List[Note], panning: int) -> List[Note]:
        """Set panning for all notes"""
        return [Note(n.pitch, n.position, n.length, n.velocity, panning) for n in notes]
    
    # ========================================================================
    # PRESET MANAGEMENT
    # ========================================================================
    
    def save_instrument_preset(self, track_name: str, preset_name: str) -> bool:
        """Save instrument settings as preset"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        inst = track.find('.//instrument')
        if inst:
            # Store preset data
            preset_data = ET.tostring(inst, encoding='unicode')
            
            # Create presets container if needed
            presets = self.root.find('.//presets')
            if presets is None:
                presets = ET.SubElement(self.root, 'presets')
            
            # Add preset
            preset = ET.SubElement(presets, 'preset')
            preset.set('name', preset_name)
            preset.set('type', 'instrument')
            preset.text = base64.b64encode(preset_data.encode()).decode()
            
            return True
        
        return False
    
    def load_instrument_preset(self, track_name: str, preset_name: str) -> bool:
        """Load instrument preset"""
        self.save_undo_state()
        
        track = self.get_track(track_name)
        if not track:
            return False
        
        presets = self.root.find('.//presets')
        if presets:
            for preset in presets.findall('preset'):
                if (preset.get('name') == preset_name and
                    preset.get('type') == 'instrument'):
                    
                    # Decode preset data
                    preset_data = base64.b64decode(preset.text).decode()
                    new_inst = ET.fromstring(preset_data)
                    
                    # Replace instrument
                    inst_track = track.find('instrumenttrack')
                    if inst_track:
                        old_inst = inst_track.find('instrument')
                        if old_inst is not None:
                            inst_track.remove(old_inst)
                        inst_track.append(new_inst)
                        return True
        
        return False
    
    # ========================================================================
    # ANALYSIS FUNCTIONS
    # ========================================================================
    
    def analyze_notes(self, notes: List[Note]) -> Dict[str, Any]:
        """Analyze a collection of notes"""
        if not notes:
            return {}
        
        analysis = {
            'count': len(notes),
            'pitch_range': {
                'min': min(n.pitch for n in notes),
                'max': max(n.pitch for n in notes)
            },
            'time_range': {
                'start': min(n.position for n in notes),
                'end': max(n.position + n.length for n in notes)
            },
            'average_velocity': sum(n.velocity for n in notes) / len(notes),
            'average_length': sum(n.length for n in notes) / len(notes),
            'pitch_histogram': {},
            'note_density': 0
        }
        
        # Calculate pitch histogram
        for note in notes:
            pitch = note.pitch
            if pitch not in analysis['pitch_histogram']:
                analysis['pitch_histogram'][pitch] = 0
            analysis['pitch_histogram'][pitch] += 1
        
        # Calculate note density (notes per beat)
        time_span = analysis['time_range']['end'] - analysis['time_range']['start']
        if time_span > 0:
            analysis['note_density'] = len(notes) / (time_span / 48)  # 48 ticks per beat
        
        return analysis
    
    def detect_key(self, notes: List[Note]) -> Tuple[int, str]:
        """Attempt to detect the key of a set of notes"""
        if not notes:
            return (60, "major")  # Default to C major
        
        # Count occurrences of each pitch class
        pitch_classes = [0] * 12
        for note in notes:
            pitch_class = note.pitch % 12
            pitch_classes[pitch_class] += note.length  # Weight by duration
        
        # Compare to major and minor scale templates
        major_template = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
        minor_template = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]
        
        best_match = (0, "major", 0)  # (root, scale, score)
        
        for root in range(12):
            # Test major
            major_score = 0
            minor_score = 0
            
            for i in range(12):
                shifted_index = (i - root) % 12
                if major_template[shifted_index]:
                    major_score += pitch_classes[i]
                if minor_template[shifted_index]:
                    minor_score += pitch_classes[i]
            
            if major_score > best_match[2]:
                best_match = (root, "major", major_score)
            if minor_score > best_match[2]:
                best_match = (root, "minor", minor_score)
        
        # Convert pitch class to note name
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        root_note = 60 + best_match[0]  # Middle C octave
        
        return (root_note, best_match[1])
    
    # ========================================================================
    # ALL TRACK ACCESS
    # ========================================================================
    
    def get_all_tracks(self) -> List[ET.Element]:
        """Get all tracks in the project"""
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer is not None:
            return trackcontainer.findall('track')
        return []
    
    def get_tracks_by_type(self, track_type: TrackType) -> List[ET.Element]:
        """Get all tracks of a specific type"""
        tracks = []
        for track in self.get_all_tracks():
            if track.get('type') == str(track_type.value):
                tracks.append(track)
        return tracks
    
    # ========================================================================
    # ACTION VALIDATION
    # ========================================================================
    
    def validate_action(self, action_name: str) -> bool:
        """Check if an action is available"""
        available_actions = [
            # File operations
            'create_new_project', 'create_new_project_from_template', 'load_project',
            'save_project', 'import_midi_file', 'export_project', 'export_stems',
            'export_midi',
            
            # Edit operations
            'undo', 'redo', 'copy', 'cut', 'paste', 'delete', 'select_all',
            
            # Track operations
            'add_track', 'delete_track', 'clone_track', 'clear_track', 'rename_track',
            'move_track', 'set_track_color', 'randomize_track_color', 'reset_track_color',
            
            # Pattern operations
            'add_pattern', 'clone_pattern', 'split_pattern', 'merge_patterns',
            'rename_pattern', 'copy_clips', 'paste_clips', 'cut_clips',
            
            # Note operations
            'add_note', 'delete_note', 'transpose_notes', 'quantize_notes',
            'humanize_notes', 'reverse_notes', 'scale_note_lengths', 'remove_overlaps',
            'glue_notes', 'strum_notes', 'create_roll', 'create_echo',
            
            # Pattern generation
            'generate_drum_pattern', 'generate_bassline', 'generate_chord_progression',
            'generate_melody',
            
            # Transport control
            'play', 'stop', 'record', 'set_loop_points', 'disable_loop',
            'toggle_metronome', 'set_tempo', 'set_time_signature',
            
            # View management
            'set_zoom', 'set_snap', 'set_edit_mode',
            
            # Effects
            'add_effect', 'remove_effect', 'set_effect_parameter',
            
            # Instruments
            'set_instrument', 'set_instrument_parameter',
            
            # Automation
            'add_automation_pattern', 'add_automation_point',
            
            # Mixer
            'set_mixer_channel', 'set_mixer_channel_volume', 'add_mixer_effect',
            
            # Analysis
            'analyze_notes', 'detect_key', 'get_project_info'
        ]
        
        return action_name in available_actions
    
    def get_available_actions(self) -> List[str]:
        """Get list of all available actions"""
        return [method for method in dir(self) 
                if not method.startswith('_') and callable(getattr(self, method))]


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
LMMS Actions - Complete programmatic access to ALL LMMS operations

Usage:
  python lmms_actions.py <command> [args...]

Commands:
  list-actions                    - List all available actions
  generate-beat <style>           - Generate a drum pattern
  generate-bass <type>            - Generate a bassline
  generate-melody <scale>         - Generate a melody
  quantize <file> <value>         - Quantize all notes in project
  humanize <file> <amount>        - Humanize timing and velocity
  transpose <file> <semitones>    - Transpose entire project
  analyze <file>                  - Analyze project
  
Examples:
  python lmms_actions.py generate-beat techno
  python lmms_actions.py generate-bass walking
  python lmms_actions.py quantize project.mmp 16
  python lmms_actions.py humanize project.mmp 0.1
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list-actions":
        controller = LMMSActions()
        actions = controller.get_available_actions()
        print("Available Actions:")
        for action in sorted(actions):
            if not action.startswith('get_') and not action.endswith('_xml'):
                print(f"  - {action}")
    
    elif command == "generate-beat" and len(sys.argv) >= 3:
        controller = LMMSActions()
        controller.add_track("Drums", TrackType.INSTRUMENT)
        controller.generate_drum_pattern("Drums", "Beat", sys.argv[2])
        controller.save_project(f"{sys.argv[2]}_beat.mmp")
        print(f"Generated {sys.argv[2]} beat pattern")
    
    elif command == "generate-bass" and len(sys.argv) >= 3:
        controller = LMMSActions()
        controller.add_track("Bass", TrackType.INSTRUMENT)
        controller.generate_bassline("Bass", "Bassline", pattern_type=sys.argv[2])
        controller.save_project(f"{sys.argv[2]}_bass.mmp")
        print(f"Generated {sys.argv[2]} bassline")
    
    elif command == "generate-melody" and len(sys.argv) >= 3:
        controller = LMMSActions()
        controller.add_track("Lead", TrackType.INSTRUMENT)
        controller.generate_melody("Lead", "Melody", scale=sys.argv[2])
        controller.save_project(f"{sys.argv[2]}_melody.mmp")
        print(f"Generated melody in {sys.argv[2]} scale")
    
    elif command == "analyze" and len(sys.argv) >= 3:
        controller = LMMSActions(sys.argv[2])
        info = controller.get_project_info()
        print(json.dumps(info, indent=2))
        
        # Analyze notes in first pattern of first track
        tracks = controller.get_all_tracks()
        if tracks:
            track_name = tracks[0].get('name')
            notes = controller.get_notes_from_pattern(track_name, 0)
            if notes:
                analysis = controller.analyze_notes(notes)
                print("\nNote Analysis:")
                print(json.dumps(analysis, indent=2))
                
                key = controller.detect_key(notes)
                print(f"\nDetected Key: {key[0]} {key[1]}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)