#!/usr/bin/env python3
"""
Musical Intelligence System - Creates actually good-sounding music
Focuses on musicality, groove, harmony, and professional production
"""

import random
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import the key engine for proper musical scale adherence
try:
    from musical_key_engine import KeySignature, MelodicGenerator, HumanizeEngine, Scale
    HAS_KEY_ENGINE = True
except ImportError:
    HAS_KEY_ENGINE = False


class GrooveTemplate:
    """Professional groove templates that actually sound good"""
    
    # KICK PATTERNS - Musical and genre-appropriate
    KICK_GROOVES = {
        'house_4x4': {
            'pattern': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
            'velocities': [127,0,0,0, 110,0,0,0, 120,0,0,0, 110,0,0,0],
            'swing': 0.0
        },
        'house_garage': {
            'pattern': [1,0,0,0, 0,0,0,1, 1,0,0,0, 0,0,0,0],
            'velocities': [120,0,0,0, 0,0,0,90, 115,0,0,0, 0,0,0,0],
            'swing': 0.15
        },
        'techno_driving': {
            'pattern': [1,0,0,1, 1,0,0,0, 1,0,0,1, 1,0,0,0],
            'velocities': [127,0,0,70, 120,0,0,0, 125,0,0,70, 120,0,0,0],
            'swing': 0.0
        },
        'techno_minimal': {
            'pattern': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0],
            'velocities': [120,0,0,0, 0,0,0,0, 115,0,0,0, 0,0,80,0],
            'swing': 0.0
        },
        'dnb_classic': {
            'pattern': [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0],
            'velocities': [120,0,0,0, 0,0,0,0, 0,0,110,0, 0,0,0,0],
            'swing': 0.0
        },
        'trap_minimal': {
            'pattern': [1,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0],
            'velocities': [127,0,0,0, 0,0,0,0, 0,0,0,0, 100,0,0,0],
            'swing': 0.0
        },
        'hip_hop_boom_bap': {
            'pattern': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0],
            'velocities': [120,0,0,0, 0,0,60,0, 0,0,100,0, 0,0,0,0],
            'swing': 0.25
        }
    }
    
    # SNARE/CLAP PATTERNS - Backbeat focused
    SNARE_GROOVES = {
        'backbeat': {
            'pattern': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
            'velocities': [0,0,0,0, 100,0,0,0, 0,0,0,0, 100,0,0,0],
            'swing': 0.0
        },
        'garage_snare': {
            'pattern': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,1],
            'velocities': [0,0,0,0, 100,0,0,0, 0,0,0,0, 100,0,0,60],
            'swing': 0.1
        },
        'dnb_snare': {
            'pattern': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
            'velocities': [0,0,0,0, 0,0,0,0, 120,0,0,0, 0,0,0,0],
            'swing': 0.0
        },
        'trap_snare': {
            'pattern': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0],
            'velocities': [0,0,0,0, 0,0,0,0, 0,0,0,0, 110,0,0,0],
            'swing': 0.0
        },
        'techno_clap': {
            'pattern': [0,0,0,0, 1,0,0,1, 0,0,0,0, 1,0,0,0],
            'velocities': [0,0,0,0, 90,0,0,50, 0,0,0,0, 90,0,0,0],
            'swing': 0.0
        }
    }
    
    # HI-HAT PATTERNS - Add groove and movement
    HAT_GROOVES = {
        'straight_16ths': {
            'pattern': [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1],
            'velocities': [70,50,60,50, 70,50,60,50, 70,50,60,50, 70,50,60,50],
            'swing': 0.0
        },
        'house_hats': {
            'pattern': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1],
            'velocities': [0,70,0,60, 0,70,0,60, 0,70,0,60, 0,70,0,60],
            'swing': 0.0
        },
        'garage_skip': {
            'pattern': [1,0,1,1, 0,1,1,0, 1,0,1,1, 0,1,1,0],
            'velocities': [70,0,50,60, 0,65,55,0, 70,0,50,60, 0,65,55,0],
            'swing': 0.2
        },
        'trap_hats': {
            'pattern': [1,0,1,0, 1,1,0,1, 1,0,1,0, 1,1,1,1],
            'velocities': [80,0,60,0, 70,70,0,60, 80,0,60,0, 70,60,50,40],
            'swing': 0.0
        },
        'techno_minimal': {
            'pattern': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
            'velocities': [0,0,60,0, 0,0,60,0, 0,0,60,0, 0,0,60,0],
            'swing': 0.0
        },
        'dnb_ride': {
            'pattern': [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1],
            'velocities': [60,55,58,55, 60,55,58,55, 60,55,58,55, 60,55,58,55],
            'swing': 0.0
        }
    }
    
    @staticmethod
    def get_groove(genre: str, element: str) -> Dict[str, Any]:
        """Get appropriate groove for genre and element"""
        
        genre_map = {
            'house': {
                'kick': 'house_4x4',
                'snare': 'backbeat',
                'hat': 'house_hats'
            },
            'techno': {
                'kick': 'techno_driving',
                'snare': 'techno_clap',
                'hat': 'techno_minimal'
            },
            'dnb': {
                'kick': 'dnb_classic',
                'snare': 'dnb_snare',
                'hat': 'dnb_ride'
            },
            'trap': {
                'kick': 'trap_minimal',
                'snare': 'trap_snare',
                'hat': 'trap_hats'
            },
            'garage': {
                'kick': 'house_garage',
                'snare': 'garage_snare',
                'hat': 'garage_skip'
            }
        }
        
        if genre in genre_map and element in genre_map[genre]:
            groove_name = genre_map[genre][element]
            
            if element == 'kick':
                return GrooveTemplate.KICK_GROOVES.get(groove_name, GrooveTemplate.KICK_GROOVES['house_4x4'])
            elif element == 'snare':
                return GrooveTemplate.SNARE_GROOVES.get(groove_name, GrooveTemplate.SNARE_GROOVES['backbeat'])
            elif element == 'hat':
                return GrooveTemplate.HAT_GROOVES.get(groove_name, GrooveTemplate.HAT_GROOVES['straight_16ths'])
        
        # Default grooves
        if element == 'kick':
            return GrooveTemplate.KICK_GROOVES['house_4x4']
        elif element == 'snare':
            return GrooveTemplate.SNARE_GROOVES['backbeat']
        else:
            return GrooveTemplate.HAT_GROOVES['straight_16ths']


class HarmonicEngine:
    """Generate musical chord progressions and basslines"""
    
    # Musical chord progressions that actually work
    PROGRESSIONS = {
        'house_classic': ['Am', 'F', 'C', 'G'],  # vi-IV-I-V
        'house_deep': ['Dm7', 'G7', 'Cmaj7', 'Am7'],
        'techno_dark': ['Am', 'Am', 'Am', 'Am'],  # Drone
        'techno_melodic': ['Am', 'F', 'G', 'Em'],
        'dnb_liquid': ['F#m', 'D', 'A', 'E'],
        'trap_dark': ['Cm', 'Cm', 'Gm', 'Fm'],
        'future_bass': ['Cmaj7', 'Am7', 'Dm7', 'G7'],
        'emotional': ['Am', 'F', 'C', 'Em'],
        'uplifting': ['C', 'G', 'Am', 'F'],
        'minimal': ['Am', 'Am', 'Dm', 'Dm']
    }
    
    # Note values for chords (MIDI)
    CHORD_NOTES = {
        'C': [36, 40, 43],      'Cm': [36, 39, 43],     'Cmaj7': [36, 40, 43, 47],
        'D': [38, 42, 45],      'Dm': [38, 41, 45],     'Dm7': [38, 41, 45, 48],
        'E': [40, 44, 47],      'Em': [40, 43, 47],     'Em7': [40, 43, 47, 50],
        'F': [41, 45, 48],      'Fm': [41, 44, 48],     'Fmaj7': [41, 45, 48, 52],
        'G': [43, 47, 50],      'Gm': [43, 46, 50],     'G7': [43, 47, 50, 53],
        'A': [45, 49, 52],      'Am': [45, 48, 52],     'Am7': [45, 48, 52, 55],
        'B': [47, 51, 54],      'Bm': [47, 50, 54],     'Bmaj7': [47, 51, 54, 58],
        'F#m': [42, 45, 49],    'C#m': [37, 40, 44],    'G#m': [44, 47, 51]
    }
    
    @staticmethod
    def get_progression(genre: str, mood: str = None) -> List[str]:
        """Get chord progression for genre/mood"""
        
        if mood == 'dark':
            return HarmonicEngine.PROGRESSIONS.get('techno_dark')
        elif mood == 'uplifting':
            return HarmonicEngine.PROGRESSIONS.get('uplifting')
        elif mood == 'emotional':
            return HarmonicEngine.PROGRESSIONS.get('emotional')
        
        # Genre-based selection
        if 'house' in genre:
            return HarmonicEngine.PROGRESSIONS.get('house_classic')
        elif 'techno' in genre:
            return HarmonicEngine.PROGRESSIONS.get('techno_melodic')
        elif 'dnb' in genre or 'drum' in genre:
            return HarmonicEngine.PROGRESSIONS.get('dnb_liquid')
        elif 'trap' in genre:
            return HarmonicEngine.PROGRESSIONS.get('trap_dark')
        else:
            return HarmonicEngine.PROGRESSIONS.get('house_classic')
    
    @staticmethod
    def generate_bassline(chord_progression: List[str], pattern_length: int = 16) -> List[Dict]:
        """Generate musical bassline following chord progression"""
        notes = []
        
        for bar_idx, chord in enumerate(chord_progression):
            bar_start = bar_idx * pattern_length
            
            # Get root note of chord
            chord_notes = HarmonicEngine.CHORD_NOTES.get(chord, [36, 40, 43])
            root = chord_notes[0]
            fifth = chord_notes[2] if len(chord_notes) > 2 else root + 7
            
            # Create bassline pattern
            bass_pattern = [
                (0, root, 6, 100),   # Root on downbeat
                (6, root, 3, 80),    # Ghost note
                (12, fifth, 6, 90),  # Fifth for movement
                (24, root, 6, 95),   # Back to root
                (36, root, 3, 70),   # Ghost
            ]
            
            for pos, pitch, length, velocity in bass_pattern:
                if pos < pattern_length:
                    notes.append({
                        'position': bar_start + pos,
                        'pitch': pitch,
                        'length': length,
                        'velocity': velocity
                    })
        
        return notes
    
    @staticmethod
    def generate_chord_stabs(chord_progression: List[str], pattern_length: int = 16) -> List[Dict]:
        """Generate chord stabs/pads"""
        notes = []
        
        for bar_idx, chord in enumerate(chord_progression):
            bar_start = bar_idx * pattern_length
            
            chord_notes = HarmonicEngine.CHORD_NOTES.get(chord, [48, 52, 55])
            
            # Shift up for mid-range
            chord_notes = [n + 12 for n in chord_notes]
            
            # Create rhythmic chord pattern
            positions = [0, 18, 36]  # Syncopated rhythm
            
            for pos in positions:
                if pos < pattern_length:
                    for note in chord_notes:
                        notes.append({
                            'position': bar_start + pos,
                            'pitch': note,
                            'length': 12,
                            'velocity': 70 + random.randint(-10, 10)
                        })
        
        return notes


class MixingEngine:
    """Intelligent mixing and EQ to prevent frequency clashing"""
    
    @staticmethod
    def get_eq_settings(element: str, genre: str) -> Dict[str, Any]:
        """Get frequency-aware EQ settings"""
        
        eq_presets = {
            'kick': {
                'hp_freq': 30,      # Remove sub-30Hz rumble
                'lp_freq': 8000,    # Remove unnecessary highs
                'boost_freq': 60,   # Punch frequency
                'boost_gain': 3,
                'notch_freq': 250,  # Remove muddiness
                'notch_gain': -2
            },
            'bass': {
                'hp_freq': 40,
                'lp_freq': 3000,
                'boost_freq': 100,
                'boost_gain': 2,
                'notch_freq': 60,   # Leave room for kick
                'notch_gain': -3
            },
            'snare': {
                'hp_freq': 150,
                'lp_freq': 12000,
                'boost_freq': 200,  # Body
                'boost_gain': 2,
                'boost2_freq': 5000, # Snap
                'boost2_gain': 3
            },
            'hat': {
                'hp_freq': 500,     # Remove all lows
                'lp_freq': 18000,
                'boost_freq': 8000,
                'boost_gain': 2,
                'shelf_freq': 10000,
                'shelf_gain': 1
            },
            'lead': {
                'hp_freq': 200,
                'lp_freq': 12000,
                'boost_freq': 2000,
                'boost_gain': 2,
                'presence_freq': 5000,
                'presence_gain': 1
            },
            'pad': {
                'hp_freq': 100,
                'lp_freq': 10000,
                'notch_freq': 500,  # Remove muddiness
                'notch_gain': -2,
                'air_freq': 12000,
                'air_gain': 1
            }
        }
        
        return eq_presets.get(element, {})
    
    @staticmethod
    def get_compression_settings(element: str) -> Dict[str, Any]:
        """Get appropriate compression settings"""
        
        comp_presets = {
            'kick': {
                'threshold': -12,
                'ratio': 4,
                'attack': 5,
                'release': 50,
                'knee': 2
            },
            'bass': {
                'threshold': -15,
                'ratio': 3,
                'attack': 10,
                'release': 100,
                'knee': 2
            },
            'snare': {
                'threshold': -10,
                'ratio': 3,
                'attack': 2,
                'release': 80,
                'knee': 1
            },
            'hat': {
                'threshold': -18,
                'ratio': 2,
                'attack': 0.5,
                'release': 30,
                'knee': 1
            },
            'master': {
                'threshold': -6,
                'ratio': 2,
                'attack': 10,
                'release': 100,
                'knee': 3
            }
        }
        
        return comp_presets.get(element, {})
    
    @staticmethod
    def get_sidechain_settings(source: str, target: str) -> Dict[str, Any]:
        """Get sidechain compression settings"""
        
        if source == 'kick' and target == 'bass':
            return {
                'threshold': -20,
                'ratio': 8,
                'attack': 0.1,
                'release': 100,
                'amount': 0.7
            }
        elif source == 'kick' and target in ['pad', 'lead']:
            return {
                'threshold': -15,
                'ratio': 4,
                'attack': 0.1,
                'release': 150,
                'amount': 0.5
            }
        
        return {}


class MusicalIntelligence:
    """Main class for generating actually good music"""
    
    def __init__(self):
        self.groove = GrooveTemplate()
        self.harmony = HarmonicEngine()
        self.mixing = MixingEngine()
        self.key_signature = None
        self.melodic_generator = None
    
    def generate_track(self, genre: str, mood: str = None, 
                      bars: int = 4, tempo: int = None, key: str = None) -> Dict[str, Any]:
        """Generate a complete, good-sounding track"""
        
        # Determine tempo
        if not tempo:
            tempo = self._get_tempo_for_genre(genre)
        
        # Set up key signature if key engine is available
        if HAS_KEY_ENGINE:
            # Determine key and scale based on genre/mood
            if not key:
                key = self._get_key_for_genre(genre, mood)
            scale = self._get_scale_for_mood(mood, genre)
            
            self.key_signature = KeySignature(key, scale)
            self.melodic_generator = MelodicGenerator(self.key_signature)
            
            # Get chord progression from key signature
            prog_type = self._get_progression_type(genre, mood)
            chord_objects = self.key_signature.get_chord_progression(prog_type)
            
            # Convert to format expected by rest of system
            progression = []
            for chord in chord_objects:
                chord_name = chord['root']
                if chord['type'] == 'minor':
                    chord_name += 'm'
                elif chord['type'] == 'dim':
                    chord_name += 'dim'
                elif chord['type'] == 'maj7':
                    chord_name += 'maj7'
                elif chord['type'] == 'min7':
                    chord_name += 'm7'
                progression.append(chord_name)
        else:
            # Fall back to original progression
            progression = self.harmony.get_progression(genre, mood)
        
        # Generate drum patterns with proper groove and humanization
        drums = self._generate_drums(genre, bars)
        
        # Humanize drums if available
        if HAS_KEY_ENGINE:
            for element in ['kick', 'snare', 'hat']:
                if element in drums and drums[element]:
                    drums[element] = HumanizeEngine.humanize_timing(drums[element], 0.05)
                    drums[element] = HumanizeEngine.humanize_velocity(drums[element], 0.15)
        
        # Generate bassline following harmony
        bass = self._generate_bass(progression, genre, bars)
        
        # Generate melodic elements with proper key adherence
        melodic = self._generate_melodic(progression, genre, mood, bars)
        
        # Apply mixing and effects
        mix_settings = self._generate_mix_settings(genre)
        
        return {
            'tempo': tempo,
            'key': key if HAS_KEY_ENGINE else 'C',
            'scale': scale if HAS_KEY_ENGINE else 'major',
            'progression': progression,
            'tracks': {
                'drums': drums,
                'bass': bass,
                'melodic': melodic
            },
            'mixing': mix_settings,
            'arrangement': self._generate_arrangement(bars)
        }
    
    def _get_tempo_for_genre(self, genre: str) -> int:
        """Get appropriate tempo for genre"""
        tempos = {
            'house': 125,
            'techno': 130,
            'dnb': 174,
            'dubstep': 140,
            'trap': 140,
            'garage': 130,
            'ambient': 90,
            'trance': 138
        }
        
        for key in tempos:
            if key in genre.lower():
                return tempos[key]
        
        return 128  # Default
    
    def _get_key_for_genre(self, genre: str, mood: str = None) -> str:
        """Get appropriate key for genre/mood"""
        
        # Mood-based keys
        if mood:
            if 'dark' in mood.lower():
                return random.choice(['A', 'D', 'F#', 'C#'])
            elif 'happy' in mood.lower() or 'uplifting' in mood.lower():
                return random.choice(['C', 'G', 'D', 'F'])
            elif 'sad' in mood.lower() or 'emotional' in mood.lower():
                return random.choice(['A', 'E', 'B', 'F#'])
        
        # Genre-based defaults
        genre_keys = {
            'house': ['C', 'F', 'G', 'A'],
            'techno': ['A', 'D', 'E', 'C'],
            'dnb': ['F#', 'D', 'A', 'E'],
            'trap': ['C', 'F', 'Bb', 'Eb'],
            'trance': ['A', 'E', 'D', 'G']
        }
        
        for key in genre_keys:
            if key in genre.lower():
                return random.choice(genre_keys[key])
        
        return 'C'  # Default
    
    def _get_scale_for_mood(self, mood: str = None, genre: str = None) -> str:
        """Get appropriate scale for mood/genre"""
        
        if mood:
            if 'dark' in mood.lower():
                return random.choice(['minor', 'harmonic_minor', 'phrygian'])
            elif 'happy' in mood.lower():
                return 'major'
            elif 'uplifting' in mood.lower():
                return random.choice(['major', 'lydian'])
            elif 'sad' in mood.lower():
                return 'minor'
            elif 'emotional' in mood.lower():
                return random.choice(['minor', 'dorian'])
            elif 'exotic' in mood.lower():
                return random.choice(['arabian', 'japanese', 'hungarian_minor'])
        
        # Genre defaults
        if genre:
            if 'techno' in genre.lower():
                return random.choice(['minor', 'dorian', 'phrygian'])
            elif 'house' in genre.lower():
                return random.choice(['major', 'minor'])
            elif 'trap' in genre.lower():
                return random.choice(['minor', 'harmonic_minor'])
        
        return 'minor'  # Default to minor for electronic music
    
    def _get_progression_type(self, genre: str, mood: str = None) -> str:
        """Get chord progression type for genre/mood"""
        
        if mood:
            if 'dark' in mood.lower():
                return 'minimal'
            elif 'sad' in mood.lower():
                return 'sad'
            elif 'uplifting' in mood.lower():
                return 'epic'
            elif 'emotional' in mood.lower():
                return 'sad'
        
        # Genre-based
        if 'house' in genre.lower():
            return 'pop'
        elif 'techno' in genre.lower():
            return 'minimal'
        elif 'jazz' in genre.lower():
            return 'jazz'
        
        return 'pop'
    
    def _generate_drums(self, genre: str, bars: int) -> Dict[str, Any]:
        """Generate drum patterns with groove"""
        
        # Get groove templates
        kick_groove = self.groove.get_groove(genre, 'kick')
        snare_groove = self.groove.get_groove(genre, 'snare')
        hat_groove = self.groove.get_groove(genre, 'hat')
        
        drums = {
            'kick': [],
            'snare': [],
            'hat': []
        }
        
        # Generate patterns for each bar
        for bar in range(bars):
            bar_start = bar * 48  # 48 ticks per bar
            
            # Add variation every 4 bars
            variation = bar % 4 == 3
            
            # Kick pattern
            for i, hit in enumerate(kick_groove['pattern']):
                if hit:
                    # Add swing
                    swing_offset = 0
                    if i % 2 == 1 and kick_groove['swing'] > 0:
                        swing_offset = int(kick_groove['swing'] * 3)
                    
                    drums['kick'].append({
                        'position': bar_start + (i * 3) + swing_offset,
                        'pitch': 36,  # C2
                        'velocity': kick_groove['velocities'][i],
                        'length': 12
                    })
            
            # Snare pattern
            for i, hit in enumerate(snare_groove['pattern']):
                if hit:
                    # Add variation fills
                    if variation and i == 15:
                        # Snare fill
                        for j in range(4):
                            drums['snare'].append({
                                'position': bar_start + (i * 3) - (j * 3),
                                'pitch': 38,
                                'velocity': 80 + (j * 10),
                                'length': 3
                            })
                    else:
                        drums['snare'].append({
                            'position': bar_start + (i * 3),
                            'pitch': 38,  # D2
                            'velocity': snare_groove['velocities'][i],
                            'length': 9
                        })
            
            # Hi-hat pattern with variations
            for i, hit in enumerate(hat_groove['pattern']):
                if hit:
                    # Occasional open hats
                    is_open = (i % 8 == 7) and random.random() < 0.3
                    
                    # Add swing to off-beats
                    swing_offset = 0
                    if i % 2 == 1 and hat_groove['swing'] > 0:
                        swing_offset = int(hat_groove['swing'] * 2)
                    
                    drums['hat'].append({
                        'position': bar_start + (i * 3) + swing_offset,
                        'pitch': 46 if is_open else 42,  # Open/closed hat
                        'velocity': hat_groove['velocities'][i] + random.randint(-5, 5),
                        'length': 6 if is_open else 3
                    })
        
        # Add EQ and compression settings
        drums['kick_eq'] = self.mixing.get_eq_settings('kick', genre)
        drums['kick_comp'] = self.mixing.get_compression_settings('kick')
        drums['snare_eq'] = self.mixing.get_eq_settings('snare', genre)
        drums['snare_comp'] = self.mixing.get_compression_settings('snare')
        drums['hat_eq'] = self.mixing.get_eq_settings('hat', genre)
        
        return drums
    
    def _generate_bass(self, progression: List[str], genre: str, bars: int) -> Dict[str, Any]:
        """Generate musical bassline"""
        
        bass_notes = []
        
        # Use key engine if available for scale-aware bass
        if HAS_KEY_ENGINE and self.melodic_generator:
            # Convert progression strings back to chord objects
            chord_objects = []
            for chord_str in progression:
                root = chord_str[0]
                if len(chord_str) > 1 and chord_str[1] in ['#', 'b']:
                    root = chord_str[:2]
                    type_str = chord_str[2:]
                else:
                    type_str = chord_str[1:]
                
                chord_type = 'major'
                if 'm7' in type_str:
                    chord_type = 'min7'
                elif 'maj7' in type_str:
                    chord_type = 'maj7'
                elif 'm' in type_str:
                    chord_type = 'minor'
                elif 'dim' in type_str:
                    chord_type = 'dim'
                
                chord_objects.append({'root': root, 'type': chord_type})
            
            # Generate scale-aware bassline
            bass_notes = self.melodic_generator.generate_bass_line(chord_objects, bars)
            
            # Add humanization
            bass_notes = HumanizeEngine.humanize_timing(bass_notes, 0.03)
            bass_notes = HumanizeEngine.humanize_velocity(bass_notes, 0.1)
            
            # Add swing for certain genres
            if genre.lower() in ['house', 'garage', 'jazz']:
                bass_notes = HumanizeEngine.add_swing(bass_notes, 0.15)
        else:
            # Original bass generation
            for bar in range(bars):
                chord_idx = bar % len(progression)
                chord = progression[chord_idx]
                bar_start = bar * 48
                
                # Get chord notes
                chord_notes = self.harmony.CHORD_NOTES.get(chord, [36, 40, 43])
                root = chord_notes[0]
                
                # Different bass patterns for different genres
                if 'house' in genre.lower():
                    # Rolling bassline
                    pattern = [
                        (0, root, 10, 100),
                        (12, root, 10, 90),
                        (24, root + 12, 10, 85),  # Octave up
                        (36, root, 10, 95)
                    ]
                elif 'techno' in genre.lower():
                    # Driving bassline
                    pattern = [
                        (0, root, 11, 100),
                        (12, root, 11, 95),
                        (24, root, 11, 95),
                        (36, root, 11, 90)
                    ]
                elif 'dnb' in genre.lower():
                    # Reese bass pattern
                    pattern = [
                        (0, root, 48, 100),  # Long sustained note
                    ]
                else:
                    # Default pattern
                    pattern = [
                        (0, root, 20, 100),
                        (24, chord_notes[2] if len(chord_notes) > 2 else root + 7, 20, 90)
                    ]
                
                for pos, pitch, length, velocity in pattern:
                    bass_notes.append({
                        'position': bar_start + pos,
                        'pitch': pitch,
                        'velocity': velocity,
                        'length': length
                    })
        
        return {
            'notes': bass_notes,
            'eq': self.mixing.get_eq_settings('bass', genre),
            'compression': self.mixing.get_compression_settings('bass'),
            'sidechain': self.mixing.get_sidechain_settings('kick', 'bass')
        }
    
    def _generate_melodic(self, progression: List[str], genre: str, 
                         mood: str, bars: int) -> Dict[str, Any]:
        """Generate melodic elements (pads, leads, arps)"""
        
        melodic = {}
        
        # Use key engine if available for scale-aware melodies
        if HAS_KEY_ENGINE and self.melodic_generator:
            # Generate a proper melody that stays in key
            if mood in ['uplifting', 'emotional', 'happy'] or 'trance' in genre or 'house' in genre:
                melody = self.melodic_generator.generate_melody(
                    bars=bars, 
                    notes_per_bar=16 if 'trance' in genre else 8,
                    octave_range=(5, 6)
                )
                
                # Humanize the melody
                melody = HumanizeEngine.humanize_timing(melody, 0.08)
                melody = HumanizeEngine.humanize_velocity(melody, 0.2)
                
                melodic['lead'] = {
                    'notes': melody,
                    'eq': self.mixing.get_eq_settings('lead', genre)
                }
            
            # Generate arpeggios for certain genres
            if 'trance' in genre or 'house' in genre or mood == 'uplifting':
                # Convert progression for arpeggiator
                chord_objects = []
                for chord_str in progression:
                    root = chord_str[0]
                    if len(chord_str) > 1 and chord_str[1] in ['#', 'b']:
                        root = chord_str[:2]
                        type_str = chord_str[2:]
                    else:
                        type_str = chord_str[1:]
                    
                    chord_type = 'major'
                    if 'm' in type_str:
                        chord_type = 'minor'
                    elif 'dim' in type_str:
                        chord_type = 'dim'
                    
                    chord_objects.append({'root': root, 'type': chord_type})
                
                arp_pattern = 'updown' if 'trance' in genre else 'up'
                arp_notes = self.melodic_generator.generate_arpeggio(
                    chord_objects, bars, pattern=arp_pattern
                )
                
                melodic['arp'] = {
                    'notes': arp_notes,
                    'eq': self.mixing.get_eq_settings('lead', genre)
                }
            
            # Generate pads for non-minimal genres
            if genre not in ['techno', 'minimal']:
                pad_notes = []
                for bar in range(bars):
                    chord_idx = bar % len(progression)
                    chord_str = progression[chord_idx]
                    bar_start = bar * 48
                    
                    # Parse chord
                    root = chord_str[0]
                    if len(chord_str) > 1 and chord_str[1] in ['#', 'b']:
                        root = chord_str[:2]
                        type_str = chord_str[2:]
                    else:
                        type_str = chord_str[1:]
                    
                    chord_type = 'major'
                    if 'm7' in type_str:
                        chord_type = 'min7'
                    elif 'maj7' in type_str:
                        chord_type = 'maj7'
                    elif 'm' in type_str:
                        chord_type = 'minor'
                    
                    # Get chord tones in proper octave
                    chord_notes = Scale.get_chord_tones(root, chord_type, 4)
                    
                    # Create sustained pad with slight variations
                    for note in chord_notes:
                        pad_notes.append({
                            'position': bar_start + random.randint(0, 2),  # Slight timing offset
                            'pitch': note,
                            'velocity': 50 + random.randint(-5, 5),
                            'length': 48 - random.randint(1, 3)  # Slight length variation
                        })
                
                melodic['pad'] = {
                    'notes': pad_notes,
                    'eq': self.mixing.get_eq_settings('pad', genre)
                }
        else:
            # Fall back to original melodic generation
            # Generate chord stabs/pads
            if genre not in ['techno', 'minimal']:
                pad_notes = []
                
                for bar in range(bars):
                    chord_idx = bar % len(progression)
                    chord = progression[chord_idx]
                    bar_start = bar * 48
                    
                    chord_notes = self.harmony.CHORD_NOTES.get(chord, [48, 52, 55])
                    # Shift to mid range
                    chord_notes = [n + 24 for n in chord_notes]
                    
                    # Sustained pad
                    for note in chord_notes:
                        pad_notes.append({
                            'position': bar_start,
                            'pitch': note,
                            'velocity': 60,
                            'length': 48  # Full bar
                        })
                
                melodic['pad'] = {
                    'notes': pad_notes,
                    'eq': self.mixing.get_eq_settings('pad', genre)
                }
            
            # Add lead melody for some genres
            if mood in ['uplifting', 'emotional'] or 'trance' in genre:
                lead_notes = self._generate_melody(progression, bars)
                melodic['lead'] = {
                    'notes': lead_notes,
                    'eq': self.mixing.get_eq_settings('lead', genre)
                }
        
        return melodic
    
    def _generate_melody(self, progression: List[str], bars: int) -> List[Dict]:
        """Generate a simple melodic line"""
        notes = []
        
        # Simple melodic patterns
        patterns = [
            [0, 12, 24, 30, 36],  # Rising pattern
            [0, 6, 24, 36],       # Syncopated
            [0, 18, 24, 42],      # Off-beat
        ]
        
        for bar in range(bars):
            chord_idx = bar % len(progression)
            chord = progression[chord_idx]
            bar_start = bar * 48
            
            chord_notes = self.harmony.CHORD_NOTES.get(chord, [60, 64, 67])
            # Shift up for lead
            chord_notes = [n + 24 for n in chord_notes]
            
            pattern = random.choice(patterns)
            
            for pos in pattern:
                if pos < 48:
                    # Pick notes from chord
                    pitch = random.choice(chord_notes)
                    notes.append({
                        'position': bar_start + pos,
                        'pitch': pitch,
                        'velocity': 70 + random.randint(-10, 10),
                        'length': 6
                    })
        
        return notes
    
    def _generate_mix_settings(self, genre: str) -> Dict[str, Any]:
        """Generate mixing settings for the track"""
        
        return {
            'master_eq': {
                'hp_freq': 20,
                'lp_freq': 20000,
                'low_shelf': 1 if genre in ['house', 'techno'] else 0,
                'high_shelf': 1 if genre in ['trance', 'dnb'] else 0
            },
            'master_compression': self.mixing.get_compression_settings('master'),
            'reverb_send': {
                'amount': 0.2 if genre in ['house', 'techno'] else 0.3,
                'size': 0.4,
                'damping': 0.5
            },
            'delay_send': {
                'amount': 0.15,
                'time': '1/8' if genre in ['house', 'techno'] else '1/4',
                'feedback': 0.3
            }
        }
    
    def _generate_arrangement(self, bars: int) -> Dict[str, Any]:
        """Generate song arrangement structure"""
        
        return {
            'intro': 4 if bars > 8 else 2,
            'main': bars,
            'breakdown': 4 if bars > 8 else 0,
            'outro': 4 if bars > 8 else 2,
            'total_bars': bars + 8 if bars > 8 else bars + 4
        }


def test_musical_intelligence():
    """Test the musical intelligence system"""
    
    mi = MusicalIntelligence()
    
    print("Musical Intelligence Test")
    print("=" * 60)
    
    test_cases = [
        ('house', 'uplifting'),
        ('techno', 'dark'),
        ('dnb', None),
        ('trap', 'dark')
    ]
    
    for genre, mood in test_cases:
        print(f"\nGenerating {genre} track" + (f" ({mood})" if mood else ""))
        print("-" * 40)
        
        track = mi.generate_track(genre, mood, bars=4)
        
        print(f"Tempo: {track['tempo']} BPM")
        print(f"Progression: {' -> '.join(track['progression'])}")
        print(f"Kick hits: {len(track['tracks']['drums']['kick'])}")
        print(f"Bass notes: {len(track['tracks']['bass']['notes'])}")
        
        if 'pad' in track['tracks']['melodic']:
            print(f"Pad notes: {len(track['tracks']['melodic']['pad']['notes'])}")
        
        print(f"Mix settings: Reverb={track['mixing']['reverb_send']['amount']}, "
              f"Delay={track['mixing']['delay_send']['amount']}")


if __name__ == "__main__":
    test_musical_intelligence()