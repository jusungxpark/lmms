#!/usr/bin/env python3
"""
LMMS Note Editor - Provides comprehensive note editing capabilities
Allows modification of existing notes in patterns and tracks
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Note:
    """Represents a note in LMMS"""
    pitch: int
    position: int
    length: int
    velocity: int = 100
    pan: int = 0
    
    def to_xml(self) -> ET.Element:
        """Convert to XML element"""
        note = ET.Element('note')
        note.set('key', str(self.pitch))
        note.set('pos', str(self.position))
        note.set('len', str(self.length))
        note.set('vol', str(self.velocity))
        note.set('pan', str(self.pan))
        return note
    
    @staticmethod
    def from_xml(element: ET.Element) -> 'Note':
        """Create Note from XML element"""
        return Note(
            pitch=int(element.get('key', 60)),
            position=int(element.get('pos', 0)),
            length=int(element.get('len', 48)),
            velocity=int(element.get('vol', 100)),
            pan=int(element.get('pan', 0))
        )


class NoteEditor:
    """Edit notes in LMMS patterns"""
    
    def __init__(self, controller):
        """Initialize with LMMS controller"""
        self.controller = controller
        self.root = controller.root
    
    def get_track_patterns(self, track_name: str) -> List[ET.Element]:
        """Get all patterns in a track"""
        patterns = []
        
        # Find the track
        track = self.controller.get_track(track_name)
        if not track:
            return patterns
        
        # Get all pattern elements in the track
        for pattern in track.findall('.//pattern'):
            patterns.append(pattern)
        
        return patterns
    
    def get_pattern_notes(self, pattern: ET.Element) -> List[Note]:
        """Get all notes from a pattern"""
        notes = []
        for note_elem in pattern.findall('.//note'):
            notes.append(Note.from_xml(note_elem))
        return notes
    
    def set_pattern_notes(self, pattern: ET.Element, notes: List[Note]):
        """Replace all notes in a pattern"""
        # Remove existing notes
        for note_elem in pattern.findall('.//note'):
            pattern.remove(note_elem)
        
        # Add new notes
        for note in notes:
            pattern.append(note.to_xml())
    
    def modify_notes_in_track(self, track_name: str, 
                            modification_func: callable,
                            pattern_index: Optional[int] = None) -> bool:
        """
        Modify notes in a track using a custom function
        
        Args:
            track_name: Name of the track
            modification_func: Function that takes List[Note] and returns List[Note]
            pattern_index: Specific pattern to modify (None = all patterns)
        
        Returns:
            True if successful
        """
        patterns = self.get_track_patterns(track_name)
        
        if not patterns:
            print(f"No patterns found in track '{track_name}'")
            return False
        
        if pattern_index is not None:
            # Modify specific pattern
            if 0 <= pattern_index < len(patterns):
                pattern = patterns[pattern_index]
                notes = self.get_pattern_notes(pattern)
                modified_notes = modification_func(notes)
                self.set_pattern_notes(pattern, modified_notes)
                return True
            else:
                print(f"Pattern index {pattern_index} out of range")
                return False
        else:
            # Modify all patterns
            for pattern in patterns:
                notes = self.get_pattern_notes(pattern)
                if notes:  # Only modify if pattern has notes
                    modified_notes = modification_func(notes)
                    self.set_pattern_notes(pattern, modified_notes)
            return True
    
    def remove_octave_jumps(self, track_name: str) -> bool:
        """Remove octave jumps from bassline"""
        
        def flatten_octaves(notes: List[Note]) -> List[Note]:
            """Keep all notes in the same octave"""
            if not notes:
                return notes
            
            modified = []
            base_octave = notes[0].pitch // 12  # Get first note's octave
            
            for note in notes:
                new_pitch = (note.pitch % 12) + (base_octave * 12)
                modified.append(Note(
                    pitch=new_pitch,
                    position=note.position,
                    length=note.length,
                    velocity=note.velocity,
                    pan=note.pan
                ))
            
            return modified
        
        return self.modify_notes_in_track(track_name, flatten_octaves)
    
    def transpose_notes(self, track_name: str, semitones: int, 
                       pattern_index: Optional[int] = None) -> bool:
        """Transpose notes by semitones"""
        
        def transpose(notes: List[Note]) -> List[Note]:
            modified = []
            for note in notes:
                new_pitch = max(0, min(127, note.pitch + semitones))
                modified.append(Note(
                    pitch=new_pitch,
                    position=note.position,
                    length=note.length,
                    velocity=note.velocity,
                    pan=note.pan
                ))
            return modified
        
        return self.modify_notes_in_track(track_name, transpose, pattern_index)
    
    def quantize_notes(self, track_name: str, grid_size: int = 12,
                      pattern_index: Optional[int] = None) -> bool:
        """Quantize note positions to grid"""
        
        def quantize(notes: List[Note]) -> List[Note]:
            modified = []
            for note in notes:
                # Quantize position to nearest grid point
                quantized_pos = round(note.position / grid_size) * grid_size
                modified.append(Note(
                    pitch=note.pitch,
                    position=quantized_pos,
                    length=note.length,
                    velocity=note.velocity,
                    pan=note.pan
                ))
            return modified
        
        return self.modify_notes_in_track(track_name, quantize, pattern_index)
    
    def scale_velocities(self, track_name: str, factor: float,
                        pattern_index: Optional[int] = None) -> bool:
        """Scale all note velocities"""
        
        def scale_vel(notes: List[Note]) -> List[Note]:
            modified = []
            for note in notes:
                new_velocity = max(1, min(127, int(note.velocity * factor)))
                modified.append(Note(
                    pitch=note.pitch,
                    position=note.position,
                    length=note.length,
                    velocity=new_velocity,
                    pan=note.pan
                ))
            return modified
        
        return self.modify_notes_in_track(track_name, scale_vel, pattern_index)
    
    def create_rolling_pattern(self, track_name: str, root_note: int = 36,
                              pattern_length: int = 192) -> bool:
        """Create a rolling bassline pattern without octave jumps"""
        
        def generate_rolling(notes: List[Note]) -> List[Note]:
            """Generate a rolling pattern in single octave"""
            # Common rolling bass pattern positions and intervals
            pattern = [
                (0, 0, 10),    # Root
                (12, 0, 10),   # Root
                (24, 5, 10),   # Fifth
                (36, 0, 10),   # Root
                (48, 0, 10),   # Root
                (60, 3, 10),   # Third
                (72, 5, 10),   # Fifth
                (84, 7, 10),   # Seventh
                (96, 0, 10),   # Root
                (108, 0, 10),  # Root
                (120, 5, 10),  # Fifth
                (132, 0, 10),  # Root
                (144, 0, 10),  # Root
                (156, -2, 10), # Flat seventh
                (168, 0, 10),  # Root
                (180, 3, 10),  # Third
            ]
            
            new_notes = []
            for pos, interval, length in pattern:
                if pos < pattern_length:
                    new_notes.append(Note(
                        pitch=root_note + interval,
                        position=pos,
                        length=length,
                        velocity=90 + (10 if pos % 48 == 0 else 0),  # Accent on downbeats
                        pan=0
                    ))
            
            return new_notes
        
        return self.modify_notes_in_track(track_name, generate_rolling)
    
    def fix_bassline_octaves(self, track_name: str) -> bool:
        """Fix bassline by removing octave jumps and keeping it rolling"""
        
        def fix_bass(notes: List[Note]) -> List[Note]:
            """Fix bassline to stay in one octave"""
            if not notes:
                return notes
            
            # Find the most common octave
            octave_counts = {}
            for note in notes:
                octave = note.pitch // 12
                octave_counts[octave] = octave_counts.get(octave, 0) + 1
            
            # Use most common octave (usually bass octave 2 or 3)
            target_octave = max(octave_counts, key=octave_counts.get)
            if target_octave > 3:  # If it's too high, bring it down
                target_octave = 3
            
            modified = []
            for note in notes:
                # Keep the note class (C, D, E, etc.) but in target octave
                note_class = note.pitch % 12
                new_pitch = (target_octave * 12) + note_class
                
                # Make sure it's in bass range
                if new_pitch > 48:  # If above C3, bring down an octave
                    new_pitch -= 12
                
                modified.append(Note(
                    pitch=new_pitch,
                    position=note.position,
                    length=note.length,
                    velocity=note.velocity,
                    pan=note.pan
                ))
            
            return modified
        
        success = self.modify_notes_in_track(track_name, fix_bass)
        if success:
            print(f"Fixed octave jumps in bassline for track '{track_name}'")
        return success
    
    def get_track_info(self, track_name: str) -> Dict[str, Any]:
        """Get information about notes in a track"""
        patterns = self.get_track_patterns(track_name)
        
        info = {
            'track_name': track_name,
            'pattern_count': len(patterns),
            'patterns': []
        }
        
        for i, pattern in enumerate(patterns):
            notes = self.get_pattern_notes(pattern)
            
            if notes:
                pitches = [n.pitch for n in notes]
                pattern_info = {
                    'index': i,
                    'note_count': len(notes),
                    'pitch_range': (min(pitches), max(pitches)),
                    'has_octave_jumps': (max(pitches) - min(pitches)) > 12,
                    'average_pitch': sum(pitches) / len(pitches)
                }
            else:
                pattern_info = {
                    'index': i,
                    'note_count': 0,
                    'pitch_range': (0, 0),
                    'has_octave_jumps': False,
                    'average_pitch': 0
                }
            
            info['patterns'].append(pattern_info)
        
        return info


def integrate_with_controller(controller_class):
    """Add note editing methods to the controller class"""
    
    original_init = controller_class.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.note_editor = NoteEditor(self)
    
    controller_class.__init__ = new_init
    
    # Add convenience methods
    controller_class.fix_bassline_octaves = lambda self, track: self.note_editor.fix_bassline_octaves(track)
    controller_class.remove_octave_jumps = lambda self, track: self.note_editor.remove_octave_jumps(track)
    controller_class.transpose_track = lambda self, track, semitones: self.note_editor.transpose_notes(track, semitones)
    controller_class.quantize_track = lambda self, track, grid=12: self.note_editor.quantize_notes(track, grid)
    controller_class.get_track_note_info = lambda self, track: self.note_editor.get_track_info(track)


if __name__ == "__main__":
    # Test the note editor
    from lmms_complete_controller import LMMSCompleteController
    
    # Integrate with controller
    integrate_with_controller(LMMSCompleteController)
    
    # Create controller and test
    controller = LMMSCompleteController()
    controller.create_new_project()
    
    # Add a bass track
    controller.add_track("Bass", 0)
    controller.set_instrument("Bass", "tripleoscillator")
    
    # Add a pattern with notes
    pattern = controller.add_pattern("Bass", "Bassline", 0, 192)
    
    # Add some notes with octave jumps
    controller.add_note(pattern, 36, 0, 12)   # C2
    controller.add_note(pattern, 48, 12, 12)  # C3 (octave jump!)
    controller.add_note(pattern, 38, 24, 12)  # D2
    controller.add_note(pattern, 50, 36, 12)  # D3 (octave jump!)
    
    # Get info before fix
    info_before = controller.get_track_note_info("Bass")
    print("Before fix:", info_before)
    
    # Fix the octave jumps
    controller.fix_bassline_octaves("Bass")
    
    # Get info after fix
    info_after = controller.get_track_note_info("Bass")
    print("After fix:", info_after)
    
    # Save project
    controller.save_project("test_note_editor.mmp")
    print("Test complete - saved to test_note_editor.mmp")