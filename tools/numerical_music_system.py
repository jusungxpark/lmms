#!/usr/bin/env python3
"""
Numerical Music System - Music as Numbers for GPT-5
Represents all musical concepts as numbers that LLMs can generate
"""

import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict


# ============================================================================
# MUSICAL CONCEPTS AS NUMBERS
# ============================================================================

class MusicNumbers:
    """
    All music represented as numbers that GPT-5 can understand and generate
    """
    
    # Note numbers (MIDI standard)
    NOTES = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
        'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    }
    
    # Octave multipliers
    OCTAVES = {
        0: 0,   # Sub-bass
        1: 12,  # Bass
        2: 24,  # Low
        3: 36,  # Mid-low
        4: 48,  # Middle
        5: 60,  # Mid-high
        6: 72,  # High
        7: 84,  # Very high
        8: 96   # Ultra high
    }
    
    # Rhythm as fractions of a bar (48 ticks = 1 bar)
    RHYTHMS = {
        'whole': 48,
        'half': 24,
        'quarter': 12,
        'eighth': 6,
        'sixteenth': 3,
        'thirtysecond': 1.5
    }
    
    # Velocity levels (0-127)
    DYNAMICS = {
        'ppp': 20,
        'pp': 35,
        'p': 50,
        'mp': 65,
        'mf': 80,
        'f': 95,
        'ff': 110,
        'fff': 127
    }
    
    @staticmethod
    def note_to_number(note: str, octave: int) -> int:
        """Convert note name to MIDI number"""
        return MusicNumbers.NOTES.get(note, 0) + (octave * 12)
    
    @staticmethod
    def chord_to_numbers(root: int, chord_type: str) -> List[int]:
        """Convert chord to list of numbers"""
        intervals = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'dim': [0, 3, 6],
            'aug': [0, 4, 8],
            'maj7': [0, 4, 7, 11],
            'min7': [0, 3, 7, 10],
            'dom7': [0, 4, 7, 10],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7]
        }
        
        chord_intervals = intervals.get(chord_type, [0, 4, 7])
        return [root + i for i in chord_intervals]


@dataclass
class NumericalPattern:
    """
    A musical pattern represented entirely as numbers
    Format: [[pitch, position, length, velocity], ...]
    """
    notes: List[List[int]]
    length: int = 48  # Pattern length in ticks
    
    def to_json(self) -> str:
        """Convert to JSON for GPT-5 to generate"""
        return json.dumps(asdict(self))
    
    @staticmethod
    def from_json(json_str: str) -> 'NumericalPattern':
        """Create from GPT-5 generated JSON"""
        data = json.loads(json_str)
        return NumericalPattern(**data)


# ============================================================================
# PATTERN GENERATORS USING PURE NUMBERS
# ============================================================================

class NumericalPatternGenerator:
    """Generate patterns as number sequences that GPT-5 can learn"""
    
    @staticmethod
    def generate_kick_pattern(style: str = 'basic') -> NumericalPattern:
        """
        Generate kick pattern as numbers
        Returns: [[pitch, position, length, velocity], ...]
        """
        
        patterns = {
            'basic': [
                [36, 0, 12, 100],   # C2, position 0, quarter note, forte
                [36, 24, 12, 100],  # C2, position 24, quarter note, forte
            ],
            'four_floor': [
                [36, 0, 12, 100],
                [36, 12, 12, 100],
                [36, 24, 12, 100],
                [36, 36, 12, 100],
            ],
            'techno': [
                [36, 0, 12, 110],
                [36, 12, 12, 100],
                [36, 24, 12, 105],
                [36, 30, 6, 80],   # Ghost note
                [36, 36, 12, 100],
            ],
            'breakbeat': [
                [36, 0, 12, 110],
                [36, 18, 6, 90],
                [36, 30, 6, 100],
            ]
        }
        
        return NumericalPattern(notes=patterns.get(style, patterns['basic']))
    
    @staticmethod
    def generate_hihat_pattern(style: str = 'basic') -> NumericalPattern:
        """Generate hihat pattern as numbers"""
        
        patterns = {
            'basic': [
                [42, 6, 3, 60],   # Closed hat on offbeats
                [42, 18, 3, 60],
                [42, 30, 3, 60],
                [42, 42, 3, 60],
            ],
            'sixteenth': [[42, i*3, 3, 50 + (10 if i%4==0 else 0)] for i in range(16)],
            'trap': [
                [42, 0, 3, 70],
                [42, 3, 3, 50],
                [42, 6, 3, 60],
                [42, 9, 3, 50],
                [42, 12, 3, 70],
                [42, 15, 3, 40],
                [42, 18, 3, 60],
                [42, 21, 3, 40],
                [42, 24, 3, 70],
                [44, 27, 3, 80],  # Open hat
                [42, 30, 3, 50],
                [42, 33, 3, 50],
                [42, 36, 3, 70],
                [42, 39, 3, 40],
                [42, 42, 3, 50],
                [42, 45, 3, 40],
            ]
        }
        
        return NumericalPattern(notes=patterns.get(style, patterns['basic']))
    
    @staticmethod
    def generate_bassline(root: int = 36, pattern_type: str = 'simple') -> NumericalPattern:
        """
        Generate bassline as numbers
        root: MIDI note number for root note
        """
        
        patterns = {
            'simple': [
                [root, 0, 24, 90],      # Root, half note
                [root, 24, 24, 90],     # Root, half note
            ],
            'octave': [
                [root, 0, 12, 100],     # Root
                [root+12, 12, 12, 90],  # Octave up
                [root, 24, 12, 95],     # Root
                [root+12, 36, 12, 85],  # Octave up
            ],
            'walking': [
                [root, 0, 12, 90],      # Root
                [root+3, 12, 12, 85],   # Minor third
                [root+5, 24, 12, 85],   # Fourth
                [root+7, 36, 12, 90],   # Fifth
            ],
            'rolling': [
                [root, 0, 10, 100],
                [root, 12, 10, 90],
                [root+7, 24, 10, 85],   # Fifth
                [root, 36, 10, 95],
            ]
        }
        
        return NumericalPattern(notes=patterns.get(pattern_type, patterns['simple']))
    
    @staticmethod
    def generate_chord_progression(progression: List[Tuple[int, str]], 
                                  position_offset: int = 0) -> NumericalPattern:
        """
        Generate chord progression as numbers
        progression: [(root_note, chord_type), ...]
        """
        notes = []
        position = position_offset
        
        for root, chord_type in progression:
            chord_notes = MusicNumbers.chord_to_numbers(root, chord_type)
            
            # Add each note of the chord
            for note in chord_notes:
                notes.append([note, position, 48, 70])  # Whole bar chord
            
            position += 48  # Next bar
        
        return NumericalPattern(notes=notes, length=position)


# ============================================================================
# GPT-5 FRIENDLY PROMPT SYSTEM
# ============================================================================

class GPTMusicPrompt:
    """Create prompts that help GPT-5 generate music as numbers"""
    
    @staticmethod
    def create_generation_prompt(request: str) -> str:
        """Create a prompt that helps GPT-5 generate numerical music"""
        
        prompt = f"""
Generate music as a numerical pattern for: "{request}"

Music is represented as arrays of numbers: [pitch, position, length, velocity]
- pitch: MIDI note (36=C2 kick, 38=D2 snare, 42=F#2 hihat, etc.)
- position: timing in ticks (0-47 for one bar, 48 ticks = 1 bar)
- length: note duration in ticks (3=16th, 6=8th, 12=quarter, 24=half)
- velocity: volume/intensity (0-127, typically 50-110)

Example kick pattern (4/4):
[[36, 0, 12, 100], [36, 12, 12, 100], [36, 24, 12, 100], [36, 36, 12, 100]]

Example bassline (A minor):
[[45, 0, 12, 90], [45, 12, 12, 85], [52, 24, 12, 85], [45, 36, 12, 90]]

Generate a pattern as JSON with this structure:
{{
    "notes": [[pitch, position, length, velocity], ...],
    "length": 48
}}
"""
        return prompt
    
    @staticmethod
    def create_analysis_prompt(pattern: NumericalPattern) -> str:
        """Create a prompt for GPT-5 to analyze numerical patterns"""
        
        prompt = f"""
Analyze this musical pattern represented as numbers:
{pattern.to_json()}

Each array is [pitch, position, length, velocity].
Describe:
1. What instrument/element this likely represents
2. The rhythm pattern (positions tell timing)
3. The note range (pitch values)
4. The dynamics (velocity values)
5. Any notable patterns or repetitions
"""
        return prompt


# ============================================================================
# NUMBER TO MUSIC CONVERTER
# ============================================================================

class NumbersToMusic:
    """Convert numerical representations to actual LMMS music"""
    
    def __init__(self, controller):
        self.controller = controller
    
    def apply_numerical_pattern(self, pattern: NumericalPattern, 
                               track_name: str, pattern_name: str = "Pattern") -> bool:
        """Convert numerical pattern to LMMS pattern"""
        
        # Add pattern to track
        lmms_pattern = self.controller.add_pattern(track_name, pattern_name, 
                                                   0, pattern.length)
        
        if not lmms_pattern:
            return False
        
        # Add each note
        for note_data in pattern.notes:
            if len(note_data) >= 4:
                pitch, position, length, velocity = note_data[:4]
                
                self.controller.add_note(
                    lmms_pattern,
                    pitch=pitch,
                    pos=position,
                    length=length,
                    velocity=velocity
                )
        
        return True
    
    def create_track_from_numbers(self, element_type: str, 
                                 pattern: NumericalPattern) -> str:
        """Create a complete track from numerical pattern"""
        
        # Determine track name and instrument
        track_configs = {
            'kick': ('Kick', 'kicker'),
            'snare': ('Snare', 'audiofileprocessor'),
            'hihat': ('HiHat', 'audiofileprocessor'),
            'bass': ('Bass', 'tripleoscillator'),
            'lead': ('Lead', 'tripleoscillator'),
            'pad': ('Pad', 'tripleoscillator')
        }
        
        track_name, instrument = track_configs.get(element_type, ('Track', 'tripleoscillator'))
        
        # Create track
        self.controller.add_track(track_name, 0)
        self.controller.set_instrument(track_name, instrument)
        
        # Apply pattern
        self.apply_numerical_pattern(pattern, track_name)
        
        return track_name


# ============================================================================
# INTELLIGENT NUMBER GENERATION
# ============================================================================

class IntelligentNumberGenerator:
    """Generate musical numbers with musical intelligence"""
    
    @staticmethod
    def generate_rhythm_numbers(density: float = 0.5, length: int = 48) -> List[int]:
        """
        Generate rhythm as position numbers
        density: 0.0-1.0 (how many notes)
        """
        positions = []
        
        # Key positions (downbeats)
        key_positions = [0, 12, 24, 36]  # Quarter notes
        
        # Add key positions
        for pos in key_positions:
            if density > 0.25:
                positions.append(pos)
        
        # Add offbeats if dense enough
        if density > 0.5:
            positions.extend([6, 18, 30, 42])  # 8th note offbeats
        
        # Add 16th notes if very dense
        if density > 0.75:
            positions.extend([3, 9, 15, 21, 27, 33, 39, 45])
        
        return sorted(positions)
    
    @staticmethod
    def generate_melody_numbers(key: int = 60, scale: str = 'minor', 
                              bars: int = 1) -> NumericalPattern:
        """Generate melody as numbers in a key/scale"""
        
        scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'pentatonic': [0, 2, 4, 7, 9],
            'blues': [0, 3, 5, 6, 7, 10]
        }
        
        scale_intervals = scales.get(scale, scales['minor'])
        
        notes = []
        position = 0
        
        for bar in range(bars):
            # Generate 8 notes per bar
            for i in range(8):
                # Pick note from scale
                scale_degree = i % len(scale_intervals)
                if i % 4 == 0:
                    scale_degree = 0  # Root on downbeats
                
                pitch = key + scale_intervals[scale_degree]
                
                # Vary octave occasionally
                if i % 7 == 0 and i > 0:
                    pitch += 12
                
                notes.append([
                    pitch,
                    position + (i * 6),  # 8th notes
                    6,  # 8th note length
                    70 + (20 if i % 4 == 0 else 0)  # Accent downbeats
                ])
        
        return NumericalPattern(notes=notes, length=bars * 48)
    
    @staticmethod
    def humanize_numbers(pattern: NumericalPattern, 
                        timing_variance: int = 2,
                        velocity_variance: int = 10) -> NumericalPattern:
        """Add human-like variations to numbers"""
        
        import random
        
        humanized_notes = []
        
        for note in pattern.notes:
            pitch, position, length, velocity = note
            
            # Humanize timing (except downbeats)
            if position % 12 != 0:  # Not a quarter note position
                position += random.randint(-timing_variance, timing_variance)
                position = max(0, position)  # Keep positive
            
            # Humanize velocity
            velocity += random.randint(-velocity_variance, velocity_variance)
            velocity = max(1, min(127, velocity))  # Keep in MIDI range
            
            humanized_notes.append([pitch, position, length, velocity])
        
        return NumericalPattern(notes=humanized_notes, length=pattern.length)


# ============================================================================
# COMPLETE NUMERICAL MUSIC SYSTEM
# ============================================================================

class NumericalMusicSystem:
    """Complete system for music as numbers"""
    
    def __init__(self, controller):
        self.controller = controller
        self.converter = NumbersToMusic(controller)
        self.generator = NumericalPatternGenerator()
        self.intelligent = IntelligentNumberGenerator()
    
    def generate_from_description(self, description: str) -> Dict[str, Any]:
        """
        Generate music from description, returning the numerical representation
        This is what GPT-5 would generate
        """
        
        description_lower = description.lower()
        
        # Generate appropriate patterns based on description
        patterns = {}
        
        # Drums
        if 'kick' in description_lower or 'beat' in description_lower:
            if 'techno' in description_lower:
                patterns['kick'] = self.generator.generate_kick_pattern('techno')
            elif 'break' in description_lower:
                patterns['kick'] = self.generator.generate_kick_pattern('breakbeat')
            else:
                patterns['kick'] = self.generator.generate_kick_pattern('four_floor')
        
        if 'hat' in description_lower or 'hihat' in description_lower:
            if 'trap' in description_lower:
                patterns['hihat'] = self.generator.generate_hihat_pattern('trap')
            else:
                patterns['hihat'] = self.generator.generate_hihat_pattern('sixteenth')
        
        # Bass
        if 'bass' in description_lower:
            if 'walking' in description_lower:
                patterns['bass'] = self.generator.generate_bassline(36, 'walking')
            elif 'rolling' in description_lower:
                patterns['bass'] = self.generator.generate_bassline(36, 'rolling')
            else:
                patterns['bass'] = self.generator.generate_bassline(36, 'simple')
        
        # Melody
        if 'melody' in description_lower or 'lead' in description_lower:
            key = 60  # C4
            if 'minor' in description_lower:
                patterns['melody'] = self.intelligent.generate_melody_numbers(key, 'minor')
            elif 'major' in description_lower:
                patterns['melody'] = self.intelligent.generate_melody_numbers(key, 'major')
            else:
                patterns['melody'] = self.intelligent.generate_melody_numbers(key, 'pentatonic')
        
        # Humanize if requested
        if 'human' in description_lower or 'natural' in description_lower:
            for name, pattern in patterns.items():
                patterns[name] = self.intelligent.humanize_numbers(pattern)
        
        return patterns
    
    def apply_numerical_music(self, patterns: Dict[str, NumericalPattern]) -> str:
        """Apply numerical patterns to create actual music"""
        
        # Create new project
        self.controller.create_new_project()
        self.controller.set_tempo(128)
        
        # Apply each pattern
        for element_type, pattern in patterns.items():
            self.converter.create_track_from_numbers(element_type, pattern)
        
        # Save project
        import time
        filename = f"numerical_music_{int(time.time())}.mmp"
        self.controller.save_project(filename)
        
        return filename
    
    def demonstrate_gpt5_generation(self):
        """Demonstrate what GPT-5 would generate"""
        
        print("GPT-5 Music Generation as Numbers")
        print("=" * 60)
        
        # This is what GPT-5 would generate
        gpt5_output = {
            "kick": {
                "notes": [
                    [36, 0, 12, 110],
                    [36, 12, 12, 100],
                    [36, 24, 12, 105],
                    [36, 36, 12, 100]
                ],
                "length": 48
            },
            "bass": {
                "notes": [
                    [36, 0, 10, 100],
                    [36, 12, 10, 90],
                    [43, 24, 10, 85],
                    [36, 36, 10, 95]
                ],
                "length": 48
            },
            "hihat": {
                "notes": [
                    [42, 0, 3, 70],
                    [42, 3, 3, 50],
                    [42, 6, 3, 60],
                    [42, 9, 3, 50],
                    [42, 12, 3, 70],
                    [42, 15, 3, 50],
                    [42, 18, 3, 60],
                    [42, 21, 3, 50],
                    [42, 24, 3, 70],
                    [42, 27, 3, 50],
                    [42, 30, 3, 60],
                    [42, 33, 3, 50],
                    [42, 36, 3, 70],
                    [42, 39, 3, 50],
                    [42, 42, 3, 60],
                    [42, 45, 3, 50]
                ],
                "length": 48
            }
        }
        
        print("\nGPT-5 generates these numbers:")
        print(json.dumps(gpt5_output, indent=2))
        
        print("\nThese numbers represent:")
        print("- Kick: 4/4 pattern with slight velocity variations")
        print("- Bass: Rolling pattern with fifth interval")
        print("- HiHat: 16th note pattern with alternating velocities")
        
        print("\nConverting to music...")
        
        # Convert to NumericalPattern objects
        patterns = {}
        for name, data in gpt5_output.items():
            patterns[name] = NumericalPattern(notes=data['notes'], length=data['length'])
        
        # Create music
        filename = self.apply_numerical_music(patterns)
        print(f"Created: {filename}")
        
        return filename


def test_numerical_system():
    """Test the numerical music system"""
    
    from lmms_complete_controller import LMMSCompleteController
    
    print("Testing Numerical Music System")
    print("=" * 60)
    
    controller = LMMSCompleteController()
    system = NumericalMusicSystem(controller)
    
    # Test 1: Generate patterns from description
    print("\n1. Generate from description: 'techno beat with rolling bass'")
    patterns = system.generate_from_description('techno beat with rolling bass')
    
    for name, pattern in patterns.items():
        print(f"\n{name}:")
        print(f"  Notes: {len(pattern.notes)}")
        print(f"  First few: {pattern.notes[:3]}")
    
    # Test 2: Create actual music
    print("\n2. Converting numbers to music...")
    filename = system.apply_numerical_music(patterns)
    print(f"Created: {filename}")
    
    # Test 3: Demonstrate GPT-5 generation
    print("\n3. Demonstrating GPT-5 number generation...")
    gpt5_file = system.demonstrate_gpt5_generation()
    print(f"GPT-5 generated music: {gpt5_file}")
    
    print("\n" + "=" * 60)
    print("Numerical Music System Test Complete")
    print("\nKey insights:")
    print("- Music is just numbers: [pitch, position, length, velocity]")
    print("- GPT-5 can generate these number sequences")
    print("- Patterns are predictable and learnable")
    print("- Humanization is just adding small random variations")


if __name__ == "__main__":
    test_numerical_system()