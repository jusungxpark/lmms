#!/usr/bin/env python3
"""
Musical Key and Scale Engine - Ensures all notes stay in key
Provides scale-aware melody generation and harmonic coherence
"""

import random
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum


class Scale:
    """Musical scales and their intervals"""
    
    # Scale intervals (semitones from root)
    SCALES = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
        'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
        'dorian': [0, 2, 3, 5, 7, 9, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'lydian': [0, 2, 4, 6, 7, 9, 11],
        'mixolydian': [0, 2, 4, 5, 7, 9, 10],
        'aeolian': [0, 2, 3, 5, 7, 8, 10],  # Natural minor
        'locrian': [0, 1, 3, 5, 6, 8, 10],
        'pentatonic_major': [0, 2, 4, 7, 9],
        'pentatonic_minor': [0, 3, 5, 7, 10],
        'blues': [0, 3, 5, 6, 7, 10],
        'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        'whole_tone': [0, 2, 4, 6, 8, 10],
        'diminished': [0, 2, 3, 5, 6, 8, 9, 11],
        'arabian': [0, 2, 4, 5, 6, 8, 10],
        'japanese': [0, 1, 5, 7, 8],
        'hungarian_minor': [0, 2, 3, 6, 7, 8, 11]
    }
    
    # Root notes (MIDI note numbers for octave 3)
    ROOTS = {
        'C': 48, 'C#': 49, 'Db': 49, 'D': 50, 'D#': 51, 'Eb': 51,
        'E': 52, 'F': 53, 'F#': 54, 'Gb': 54, 'G': 55, 'G#': 56,
        'Ab': 56, 'A': 57, 'A#': 58, 'Bb': 58, 'B': 59
    }
    
    @staticmethod
    def get_scale_notes(root: str, scale_type: str, octave_range: Tuple[int, int] = (3, 5)) -> List[int]:
        """Get all notes in a scale across specified octave range"""
        
        root_midi = Scale.ROOTS.get(root, 48)  # Default to C
        intervals = Scale.SCALES.get(scale_type, Scale.SCALES['major'])
        
        notes = []
        for octave in range(octave_range[0], octave_range[1] + 1):
            octave_offset = (octave - 3) * 12
            for interval in intervals:
                note = root_midi + octave_offset + interval
                if 0 <= note <= 127:  # Valid MIDI range
                    notes.append(note)
        
        return notes
    
    @staticmethod
    def quantize_to_scale(note: int, root: str, scale_type: str) -> int:
        """Quantize a note to the nearest note in the scale"""
        
        scale_notes = Scale.get_scale_notes(root, scale_type, (0, 10))
        
        # Find closest note in scale
        closest_note = min(scale_notes, key=lambda x: abs(x - note))
        return closest_note
    
    @staticmethod
    def get_chord_tones(root: str, chord_type: str, octave: int = 4) -> List[int]:
        """Get chord tones for a given chord"""
        
        root_midi = Scale.ROOTS.get(root, 48)
        octave_offset = (octave - 3) * 12
        root_note = root_midi + octave_offset
        
        chord_intervals = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'dim': [0, 3, 6],
            'aug': [0, 4, 8],
            'maj7': [0, 4, 7, 11],
            'min7': [0, 3, 7, 10],
            'dom7': [0, 4, 7, 10],
            'maj9': [0, 4, 7, 11, 14],
            'min9': [0, 3, 7, 10, 14],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7],
            'add9': [0, 4, 7, 14],
            '6': [0, 4, 7, 9],
            'min6': [0, 3, 7, 9]
        }
        
        intervals = chord_intervals.get(chord_type, [0, 4, 7])
        return [root_note + i for i in intervals if root_note + i <= 127]


class KeySignature:
    """Manages key signature and ensures harmonic coherence"""
    
    def __init__(self, root: str = 'C', scale: str = 'major'):
        self.root = root
        self.scale = scale
        self.scale_notes = Scale.get_scale_notes(root, scale)
        
    def get_diatonic_chords(self) -> List[Dict[str, Any]]:
        """Get diatonic chords for the key"""
        
        if self.scale == 'major':
            # I ii iii IV V vi vii°
            chord_pattern = [
                ('major', 0), ('minor', 2), ('minor', 4),
                ('major', 5), ('major', 7), ('minor', 9),
                ('dim', 11)
            ]
        elif self.scale in ['minor', 'aeolian']:
            # i ii° III iv v VI VII
            chord_pattern = [
                ('minor', 0), ('dim', 2), ('major', 3),
                ('minor', 5), ('minor', 7), ('major', 8),
                ('major', 10)
            ]
        else:
            # Default to major pattern
            chord_pattern = [
                ('major', 0), ('minor', 2), ('minor', 4),
                ('major', 5), ('major', 7), ('minor', 9),
                ('dim', 11)
            ]
        
        chords = []
        root_midi = Scale.ROOTS[self.root]
        
        for chord_type, interval in chord_pattern:
            chord_root = root_midi + interval
            # Find the note name
            for name, midi in Scale.ROOTS.items():
                if midi % 12 == chord_root % 12:
                    chords.append({
                        'root': name,
                        'type': chord_type,
                        'degree': len(chords) + 1
                    })
                    break
        
        return chords
    
    def get_chord_progression(self, progression_type: str = 'pop') -> List[Dict[str, Any]]:
        """Get a chord progression in the current key"""
        
        diatonic = self.get_diatonic_chords()
        
        progressions = {
            'pop': [0, 5, 3, 4],        # I-vi-IV-V
            'rock': [0, 3, 4, 3],        # I-IV-V-IV
            'blues': [0, 0, 0, 0, 3, 3, 0, 0, 4, 3, 0, 4],  # 12-bar blues
            'jazz': [1, 4, 0, 0],        # ii-V-I
            'sad': [5, 3, 0, 4],         # vi-IV-I-V
            'epic': [0, 6, 3, 4],        # I-VII-IV-V
            'minimal': [0, 0, 0, 0],     # Drone on I
            'tension': [0, 1, 4, 0],     # I-ii°-V-I
            'spanish': [5, 4, 3, 5],     # vi-V-IV-vi
            'gospel': [0, 2, 3, 0]       # I-iii-IV-I
        }
        
        pattern = progressions.get(progression_type, progressions['pop'])
        return [diatonic[i] for i in pattern if i < len(diatonic)]


class MelodicGenerator:
    """Generates melodies that stay in key and sound musical"""
    
    def __init__(self, key_signature: KeySignature):
        self.key = key_signature
        self.scale_notes = key_signature.scale_notes
        
    def generate_melody(self, bars: int = 4, notes_per_bar: int = 8, 
                       octave_range: Tuple[int, int] = (4, 6)) -> List[Dict[str, Any]]:
        """Generate a melodic line that follows music theory"""
        
        melody = []
        position = 0
        ticks_per_bar = 48
        tick_length = ticks_per_bar // notes_per_bar
        
        # Filter scale notes to octave range
        available_notes = [n for n in self.scale_notes 
                          if octave_range[0] * 12 <= n <= octave_range[1] * 12]
        
        # Start on a strong tone (root, 3rd, or 5th)
        strong_tones = [available_notes[i] for i in [0, 2, 4] if i < len(available_notes)]
        current_note = random.choice(strong_tones)
        
        for bar in range(bars):
            for beat in range(notes_per_bar):
                # Decide if this is a rest
                if random.random() < 0.15:  # 15% chance of rest
                    position += tick_length
                    continue
                
                # Melodic movement rules
                if beat % 4 == 0:  # Strong beats
                    # Prefer chord tones on strong beats
                    if random.random() < 0.7:
                        current_note = random.choice(strong_tones)
                    else:
                        # Small step movement
                        current_note = self._step_motion(current_note, available_notes, 2)
                else:  # Weak beats
                    # Prefer stepwise motion
                    if random.random() < 0.6:
                        current_note = self._step_motion(current_note, available_notes, 1)
                    elif random.random() < 0.85:
                        current_note = self._step_motion(current_note, available_notes, 2)
                    else:
                        # Occasional leap
                        current_note = self._leap_motion(current_note, available_notes)
                
                # Vary note length
                if random.random() < 0.7:
                    length = tick_length
                elif random.random() < 0.8:
                    length = tick_length * 2
                else:
                    length = tick_length // 2
                
                # Vary velocity for dynamics
                if beat % 4 == 0:
                    velocity = 80 + random.randint(-5, 10)
                else:
                    velocity = 60 + random.randint(-10, 10)
                
                melody.append({
                    'position': position,
                    'pitch': current_note,
                    'length': min(length, ticks_per_bar - (position % ticks_per_bar)),
                    'velocity': velocity
                })
                
                position += tick_length
        
        # Resolve to root at the end
        if melody and bar == bars - 1:
            root_note = strong_tones[0]
            melody[-1]['pitch'] = root_note
            melody[-1]['velocity'] = 90
        
        return melody
    
    def _step_motion(self, current: int, available: List[int], max_steps: int) -> int:
        """Move by step within scale"""
        
        if current not in available:
            return random.choice(available)
        
        idx = available.index(current)
        step = random.randint(-max_steps, max_steps)
        new_idx = max(0, min(len(available) - 1, idx + step))
        
        return available[new_idx]
    
    def _leap_motion(self, current: int, available: List[int]) -> int:
        """Make a melodic leap (3rd, 4th, 5th)"""
        
        if current not in available:
            return random.choice(available)
        
        idx = available.index(current)
        leap_intervals = [-5, -4, -3, 3, 4, 5]  # Scale degrees
        leap = random.choice(leap_intervals)
        new_idx = max(0, min(len(available) - 1, idx + leap))
        
        return available[new_idx]
    
    def generate_bass_line(self, chord_progression: List[Dict[str, Any]], 
                          bars: int = 4) -> List[Dict[str, Any]]:
        """Generate a bass line that follows the chord progression"""
        
        bass = []
        ticks_per_bar = 48
        
        for bar in range(bars):
            chord = chord_progression[bar % len(chord_progression)]
            chord_root = Scale.ROOTS[chord['root']] + 24  # Bass octave
            
            bar_position = bar * ticks_per_bar
            
            # Different bass patterns
            patterns = [
                # Walking bass
                [(0, chord_root, 12), (12, chord_root + 5, 12), 
                 (24, chord_root + 7, 12), (36, chord_root + 5, 12)],
                # Root-fifth
                [(0, chord_root, 24), (24, chord_root + 7, 24)],
                # Driving eighth notes
                [(i * 6, chord_root, 6) for i in range(8)],
                # Syncopated
                [(0, chord_root, 18), (18, chord_root, 6), 
                 (30, chord_root + 7, 18)]
            ]
            
            pattern = random.choice(patterns)
            
            for pos, pitch, length in pattern:
                if pos < ticks_per_bar:
                    # Keep in scale
                    pitch = Scale.quantize_to_scale(pitch, self.key.root, self.key.scale)
                    
                    bass.append({
                        'position': bar_position + pos,
                        'pitch': pitch,
                        'length': length,
                        'velocity': 90 + random.randint(-10, 10)
                    })
        
        return bass
    
    def generate_arpeggio(self, chord_progression: List[Dict[str, Any]], 
                         bars: int = 4, pattern: str = 'up') -> List[Dict[str, Any]]:
        """Generate arpeggiated chords"""
        
        arp = []
        ticks_per_bar = 48
        notes_per_bar = 16
        tick_length = ticks_per_bar // notes_per_bar
        
        for bar in range(bars):
            chord = chord_progression[bar % len(chord_progression)]
            chord_tones = Scale.get_chord_tones(chord['root'], chord['type'], 5)
            
            bar_position = bar * ticks_per_bar
            
            # Arpeggio patterns
            if pattern == 'up':
                sequence = chord_tones
            elif pattern == 'down':
                sequence = chord_tones[::-1]
            elif pattern == 'updown':
                sequence = chord_tones + chord_tones[-2:0:-1]
            elif pattern == 'random':
                sequence = [random.choice(chord_tones) for _ in range(notes_per_bar)]
            else:
                sequence = chord_tones
            
            for i in range(notes_per_bar):
                note = sequence[i % len(sequence)]
                
                # Add some rests for breathing
                if random.random() < 0.1:
                    continue
                
                arp.append({
                    'position': bar_position + (i * tick_length),
                    'pitch': note,
                    'length': tick_length - 1,  # Slight gap
                    'velocity': 50 + random.randint(-10, 20)
                })
        
        return arp


class HumanizeEngine:
    """Add human-like timing and velocity variations"""
    
    @staticmethod
    def humanize_timing(notes: List[Dict[str, Any]], amount: float = 0.1) -> List[Dict[str, Any]]:
        """Add slight timing variations to make it less robotic"""
        
        humanized = []
        max_shift = int(48 * amount)  # Max shift as fraction of bar
        
        for note in notes:
            # Don't shift the first note of each bar too much
            if note['position'] % 48 == 0:
                shift = random.randint(-max_shift // 4, max_shift // 4)
            else:
                shift = random.randint(-max_shift, max_shift)
            
            humanized_note = note.copy()
            humanized_note['position'] = max(0, note['position'] + shift)
            humanized.append(humanized_note)
        
        return humanized
    
    @staticmethod
    def humanize_velocity(notes: List[Dict[str, Any]], amount: float = 0.2) -> List[Dict[str, Any]]:
        """Add velocity variations for more natural dynamics"""
        
        humanized = []
        
        for note in notes:
            variation = int(127 * amount)
            
            humanized_note = note.copy()
            new_velocity = note['velocity'] + random.randint(-variation, variation)
            humanized_note['velocity'] = max(1, min(127, new_velocity))
            humanized.append(humanized_note)
        
        return humanized
    
    @staticmethod
    def add_swing(notes: List[Dict[str, Any]], amount: float = 0.2) -> List[Dict[str, Any]]:
        """Add swing to off-beats"""
        
        swung = []
        swing_ticks = int(3 * amount)  # 3 ticks = 1/16 note
        
        for note in notes:
            swung_note = note.copy()
            
            # Shift every other 16th note
            sixteenth_position = (note['position'] // 3) % 2
            if sixteenth_position == 1:
                swung_note['position'] += swing_ticks
            
            swung.append(swung_note)
        
        return swung


def test_key_engine():
    """Test the musical key engine"""
    
    print("Musical Key Engine Test")
    print("=" * 60)
    
    # Test different keys and scales
    test_cases = [
        ('C', 'major'),
        ('A', 'minor'),
        ('D', 'dorian'),
        ('F#', 'harmonic_minor'),
        ('Bb', 'blues')
    ]
    
    for root, scale in test_cases:
        print(f"\nKey: {root} {scale}")
        print("-" * 40)
        
        # Create key signature
        key = KeySignature(root, scale)
        
        # Get scale notes
        scale_notes = Scale.get_scale_notes(root, scale, (4, 5))
        print(f"Scale notes: {scale_notes[:7]}")  # First octave
        
        # Get diatonic chords
        chords = key.get_diatonic_chords()
        chord_str = " ".join([f"{c['root']}{'' if c['type'] == 'major' else 'm' if c['type'] == 'minor' else '°'}" 
                              for c in chords])
        print(f"Diatonic chords: {chord_str}")
        
        # Get chord progression
        progression = key.get_chord_progression('pop')
        prog_str = " - ".join([f"{c['root']}{c['type'][:3]}" for c in progression])
        print(f"Progression: {prog_str}")
        
        # Generate melody
        melodic_gen = MelodicGenerator(key)
        melody = melodic_gen.generate_melody(bars=1, notes_per_bar=8)
        print(f"Melody notes: {len(melody)} notes generated")
        
        # Test humanization
        humanized = HumanizeEngine.humanize_timing(melody, 0.1)
        print(f"Humanized: Timing variations added")


if __name__ == "__main__":
    test_key_engine()