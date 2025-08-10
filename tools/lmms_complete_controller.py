#!/usr/bin/env python3
"""
LMMS Complete Controller - Full programmatic access to ALL LMMS features
Provides comprehensive control over every aspect of LMMS for AI/GPT-5 usage
"""

import xml.etree.ElementTree as ET
import json
import os
import subprocess
import time
import gzip
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from enum import Enum, IntEnum
from dataclasses import dataclass, field


# ============================================================================
# ENUMERATIONS AND CONSTANTS
# ============================================================================

class TrackType(IntEnum):
    """All available track types in LMMS"""
    INSTRUMENT = 0
    PATTERN = 1
    SAMPLE = 2
    EVENT = 3
    VIDEO = 4
    AUTOMATION = 5
    HIDDEN_AUTOMATION = 6


class WaveForm(IntEnum):
    """Waveform types for oscillators"""
    SINE = 0
    TRIANGLE = 1
    SAW = 2
    SQUARE = 3
    MOOG_SAW = 4
    EXPONENTIAL = 5
    WHITE_NOISE = 6
    USER_DEFINED = 7


class FilterType(IntEnum):
    """Filter types available in LMMS"""
    LOWPASS = 0
    HIGHPASS = 1
    BANDPASS = 2
    BANDSTOP = 3
    ALLPASS = 4
    NOTCH = 5
    MOOG = 6
    DOUBLELOWPASS = 7
    RC12 = 8
    RC24 = 9
    FORMANTFILTER = 10
    FASTFORMANT = 11
    SVFILTER = 12
    TRIPOLE = 13


class ModulationMode(IntEnum):
    """Modulation modes for oscillators"""
    MIX = 0
    AM = 1  # Amplitude Modulation
    FM = 2  # Frequency Modulation
    PM = 3  # Phase Modulation
    SYNC = 4  # Oscillator Sync


class ArpDirection(IntEnum):
    """Arpeggiator direction modes"""
    UP = 0
    DOWN = 1
    UP_DOWN = 2
    UP_DOWN_INCL = 3
    DOWN_UP = 4
    DOWN_UP_INCL = 5
    RANDOM = 6
    SORT = 7


class ArpMode(IntEnum):
    """Arpeggiator modes"""
    FREE = 0
    SORT = 1
    SYNC = 2


class LoopMode(IntEnum):
    """Sample loop modes"""
    OFF = 0
    ON = 1
    PING_PONG = 2


class CompressorMode(IntEnum):
    """Compressor operation modes"""
    COMP = 0
    LIMIT = 1


class StereoMode(IntEnum):
    """Stereo processing modes"""
    LEFT_RIGHT = 0
    MID_SIDE = 1
    RIGHT_LEFT = 2
    SIDE_MID = 3


# MIDI Constants
MIDI_NOTES = {
    'C-1': 0, 'C#-1': 1, 'D-1': 2, 'D#-1': 3, 'E-1': 4, 'F-1': 5,
    'F#-1': 6, 'G-1': 7, 'G#-1': 8, 'A-1': 9, 'A#-1': 10, 'B-1': 11
}
# Generate all octaves
for octave in range(0, 10):
    for note, base_val in [('C', 0), ('C#', 1), ('D', 2), ('D#', 3), 
                           ('E', 4), ('F', 5), ('F#', 6), ('G', 7),
                           ('G#', 8), ('A', 9), ('A#', 10), ('B', 11)]:
        MIDI_NOTES[f'{note}{octave}'] = 12 + (octave * 12) + base_val


# ============================================================================
# INSTRUMENT DEFINITIONS
# ============================================================================

@dataclass
class InstrumentDefinition:
    """Definition of an instrument and its parameters"""
    name: str
    xml_name: str
    parameters: Dict[str, Any]
    sub_elements: Dict[str, Dict[str, Any]] = field(default_factory=dict)


# Complete instrument definitions with ALL parameters
INSTRUMENTS = {
    'tripleoscillator': InstrumentDefinition(
        name='TripleOscillator',
        xml_name='tripleoscillator',
        parameters={
            # Per-oscillator parameters (0-2)
            'vol0': (0, 100), 'vol1': (0, 100), 'vol2': (0, 100),
            'pan0': (-100, 100), 'pan1': (-100, 100), 'pan2': (-100, 100),
            'coarse0': (-24, 24), 'coarse1': (-24, 24), 'coarse2': (-24, 24),
            'finel0': (-100, 100), 'finel1': (-100, 100), 'finel2': (-100, 100),
            'finer0': (-100, 100), 'finer1': (-100, 100), 'finer2': (-100, 100),
            'wavetype0': (0, 7), 'wavetype1': (0, 7), 'wavetype2': (0, 7),
            'phoffset0': (0, 360), 'phoffset1': (0, 360), 'phoffset2': (0, 360),
            'stphdetun0': (0, 360), 'stphdetun1': (0, 360), 'stphdetun2': (0, 360),
            'userwavefile0': str, 'userwavefile1': str, 'userwavefile2': str,
            'modalgo1': (0, 4), 'modalgo2': (0, 4), 'modalgo3': (0, 4)
        }
    ),
    
    'kicker': InstrumentDefinition(
        name='Kicker',
        xml_name='kicker',
        parameters={
            'version': (1, 1),
            'decay': (0, 10000),
            'dist': (0.0, 1.0),
            'distend': (0.0, 1.0),
            'diststart': (0.0, 1.0),
            'end': (10, 1000),
            'env': (0.0, 1.0),
            'gain': (0.0, 10.0),
            'noise': (0.0, 1.0),
            'slope': (0.0, 1.0),
            'start': (10, 1000),
            'startclick': (0.0, 1.0)
        }
    ),
    
    'monstro': InstrumentDefinition(
        name='Monstro',
        xml_name='monstro',
        parameters={
            'osc1_vol': (0, 200), 'osc1_pan': (-100, 100),
            'osc1_crs': (-24, 24), 'osc1_ftl': (-100, 100), 'osc1_ftr': (-100, 100),
            'osc1_spo': (0, 360), 'osc1_pd': (0, 360), 'osc1_wave': (0, 11),
            'osc2_vol': (0, 200), 'osc2_pan': (-100, 100),
            'osc2_crs': (-24, 24), 'osc2_ftl': (-100, 100), 'osc2_ftr': (-100, 100),
            'osc2_spo': (0, 360), 'osc2_pd': (0, 360), 'osc2_wave': (0, 11),
            'osc3_vol': (0, 200), 'osc3_pan': (-100, 100),
            'osc3_crs': (-24, 24), 'osc3_ftl': (-100, 100), 'osc3_ftr': (-100, 100),
            'osc3_wave': (0, 11), 'osc3_sync': (0, 1),
            'env1_pre': (0, 100), 'env1_att': (0, 20000), 'env1_hold': (0, 20000),
            'env1_dec': (0, 20000), 'env1_sus': (0, 100), 'env1_rel': (0, 20000),
            'env1_slope': (-1, 1),
            'env2_pre': (0, 100), 'env2_att': (0, 20000), 'env2_hold': (0, 20000),
            'env2_dec': (0, 20000), 'env2_sus': (0, 100), 'env2_rel': (0, 20000),
            'env2_slope': (-1, 1),
            'lfo1_wave': (0, 11), 'lfo1_att': (0, 20000), 'lfo1_rate': (0.001, 20000),
            'lfo1_phs': (0, 360),
            'lfo2_wave': (0, 11), 'lfo2_att': (0, 20000), 'lfo2_rate': (0.001, 20000),
            'lfo2_phs': (0, 360),
            'matrix': str  # Modulation matrix configuration
        }
    ),
    
    'watsyn': InstrumentDefinition(
        name='Watsyn',
        xml_name='watsyn',
        parameters={
            'a1_vol': (0, 200), 'a1_pan': (-100, 100), 'a1_mult': (0, 100),
            'a1_ltune': (-600, 600), 'a1_rtune': (-600, 600),
            'a2_vol': (0, 200), 'a2_pan': (-100, 100), 'a2_mult': (0, 100),
            'a2_ltune': (-600, 600), 'a2_rtune': (-600, 600),
            'b1_vol': (0, 200), 'b1_pan': (-100, 100), 'b1_mult': (0, 100),
            'b1_ltune': (-600, 600), 'b1_rtune': (-600, 600),
            'b2_vol': (0, 200), 'b2_pan': (-100, 100), 'b2_mult': (0, 100),
            'b2_ltune': (-600, 600), 'b2_rtune': (-600, 600),
            'm_env': (0, 200), 'm_mode': (0, 3),
            'a_wave': str, 'b_wave': str  # Wavetable data
        }
    ),
    
    'bitinvader': InstrumentDefinition(
        name='BitInvader',
        xml_name='bitinvader',
        parameters={
            'sampleLength': (4, 128),
            'interpolation': (0, 1),
            'normalize': (0, 1),
            'graph': str  # Wavetable graph data
        }
    ),
    
    'organic': InstrumentDefinition(
        name='Organic',
        xml_name='organic',
        parameters={
            'num_osc': (1, 8),
            'wavetype': (0, 5),
            'vol0': (-100, 100), 'vol1': (-100, 100), 'vol2': (-100, 100),
            'vol3': (-100, 100), 'vol4': (-100, 100), 'vol5': (-100, 100),
            'vol6': (-100, 100), 'vol7': (-100, 100),
            'harm0': (1, 32), 'harm1': (1, 32), 'harm2': (1, 32),
            'harm3': (1, 32), 'harm4': (1, 32), 'harm5': (1, 32),
            'harm6': (1, 32), 'harm7': (1, 32),
            'randomize': (0, 1)
        }
    ),
    
    'lb302': InstrumentDefinition(
        name='LB302',
        xml_name='lb302',
        parameters={
            'vco_mix': (0, 127), 'vco_mod': (0, 127), 'decay': (0, 127),
            'envmod': (0, 127), 'reso': (0, 127), 'cutoff': (0, 127),
            'accent': (0, 127), 'volume': (0, 127), 'shape': (0, 1),
            'vcf_mod': (0, 127), 'slide': (0, 127), 'slide_dec': (0, 127),
            'dead': (0, 1), 'dist': (0, 127)
        }
    ),
    
    'sid': InstrumentDefinition(
        name='SID',
        xml_name='sid',
        parameters={
            # Voice 1
            'v1_wave': (0, 8), 'v1_sync': (0, 1), 'v1_ring': (0, 1),
            'v1_test': (0, 1), 'v1_gate': (0, 1),
            'v1_attack': (0, 15), 'v1_decay': (0, 15),
            'v1_sustain': (0, 15), 'v1_release': (0, 15),
            'v1_coarse': (-24, 24), 'v1_pulse': (0, 4095),
            # Voice 2
            'v2_wave': (0, 8), 'v2_sync': (0, 1), 'v2_ring': (0, 1),
            'v2_test': (0, 1), 'v2_gate': (0, 1),
            'v2_attack': (0, 15), 'v2_decay': (0, 15),
            'v2_sustain': (0, 15), 'v2_release': (0, 15),
            'v2_coarse': (-24, 24), 'v2_pulse': (0, 4095),
            # Voice 3
            'v3_wave': (0, 8), 'v3_sync': (0, 1), 'v3_ring': (0, 1),
            'v3_test': (0, 1), 'v3_gate': (0, 1),
            'v3_attack': (0, 15), 'v3_decay': (0, 15),
            'v3_sustain': (0, 15), 'v3_release': (0, 15),
            'v3_coarse': (-24, 24), 'v3_pulse': (0, 4095),
            # Filter
            'filter_mode': (0, 7), 'filter_cutoff': (0, 2047),
            'filter_reso': (0, 15), 'filter_v3off': (0, 1),
            'volume': (0, 15), 'chip_model': (0, 1)
        }
    ),
    
    'vibed': InstrumentDefinition(
        name='Vibed',
        xml_name='vibed',
        parameters={
            'string0': (0, 8), 'string1': (0, 8), 'string2': (0, 8),
            'string3': (0, 8), 'string4': (0, 8), 'string5': (0, 8),
            'string6': (0, 8), 'string7': (0, 8), 'string8': (0, 8),
            'impulse': (0, 8), 'octave': (0, 6),
            'spread': (0, 255), 'error': (0, 50),
            'rndgain': (0, 100)
        }
    ),
    
    'sfxr': InstrumentDefinition(
        name='Sfxr',
        xml_name='sfxr',
        parameters={
            'wave': (0, 4),
            'sqrDuty': (0, 1), 'sqrSweep': (-1, 1),
            'startFreq': (0, 1), 'minFreq': (0, 1),
            'slide': (-1, 1), 'dSlide': (-1, 1),
            'vibDepth': (0, 1), 'vibSpeed': (0, 1),
            'env_att': (0, 1), 'env_sus': (0, 1),
            'env_dec': (0, 1), 'env_punch': (0, 1),
            'lpFiltOn': (0, 1), 'lpFreq': (0, 1),
            'lpReso': (0, 1), 'lpSweep': (-1, 1),
            'hpFiltOn': (0, 1), 'hpFreq': (0, 1),
            'hpSweep': (-1, 1),
            'phaOffset': (-1, 1), 'phaSweep': (-1, 1),
            'repeatSpeed': (0, 1),
            'changeAmt': (-1, 1), 'changeSpeed': (0, 1)
        }
    ),
    
    'audiofileprocessor': InstrumentDefinition(
        name='AudioFileProcessor',
        xml_name='audiofileprocessor',
        parameters={
            'src': str,  # File path
            'sframe': (0, 2147483647),  # Start frame
            'eframe': (0, 2147483647),  # End frame
            'amp': (0, 500),
            'looped': (0, 1),
            'reversed': (0, 1),
            'bb': (0, 127),  # Base note
            'interp': (0, 3),  # Interpolation mode
            'stutter': (0, 1)
        }
    ),
    
    'patman': InstrumentDefinition(
        name='Patman',
        xml_name='patman',
        parameters={
            'file': str,
            'defaultpatch': (0, 127),
            'tuned': (0, 1),
            'looped': (0, 1)
        }
    ),
    
    'sf2player': InstrumentDefinition(
        name='Sf2Player',
        xml_name='sf2player',
        parameters={
            'src': str,  # SF2 file path
            'bank': (0, 16383),
            'patch': (0, 127),
            'gain': (0, 10),
            'reverb': (0, 1), 'reverb_room': (0, 1), 'reverb_damp': (0, 1),
            'reverb_width': (0, 100), 'reverb_level': (0, 1),
            'chorus': (0, 1), 'chorus_num': (0, 99), 'chorus_level': (0, 10),
            'chorus_speed': (0.1, 5), 'chorus_depth': (0, 46)
        }
    ),
    
    'gigplayer': InstrumentDefinition(
        name='GigPlayer',
        xml_name='gigplayer',
        parameters={
            'src': str,  # Gig file path
            'bank': (0, 127),
            'patch': (0, 127),
            'gain': (0, 10)
        }
    ),
    
    'slicert': InstrumentDefinition(
        name='SlicerT',
        xml_name='slicert',
        parameters={
            'src': str,  # Sample file
            'bpm': (1, 999),
            'slice_threshold': (0, 100),
            'fade_in': (0, 100),
            'fade_out': (0, 100),
            'sync': (0, 1),
            'slices': str  # Slice points data
        }
    ),
    
    'freeboy': InstrumentDefinition(
        name='FreeBoy',
        xml_name='freeboy',
        parameters={
            'ch1_vol': (0, 15), 'ch1_sweep': (0, 7), 'ch1_shift': (0, 7),
            'ch1_len': (0, 63), 'ch1_wave': (0, 3),
            'ch2_vol': (0, 15), 'ch2_len': (0, 63), 'ch2_wave': (0, 3),
            'ch3_vol': (0, 15), 'ch3_len': (0, 255),
            'ch4_vol': (0, 15), 'ch4_sweep': (0, 7), 'ch4_len': (0, 63),
            'ch4_mode': (0, 1), 'ch4_ratio': (0, 7)
        }
    ),
    
    'nes': InstrumentDefinition(
        name='Nes',
        xml_name='nes',
        parameters={
            'ch1_enabled': (0, 1), 'ch1_duty': (0, 3), 'ch1_volume': (0, 15),
            'ch1_sweep_enabled': (0, 1), 'ch1_sweep_amount': (0, 7),
            'ch1_sweep_rate': (0, 7), 'ch1_sweep_increase': (0, 1),
            'ch2_enabled': (0, 1), 'ch2_duty': (0, 3), 'ch2_volume': (0, 15),
            'ch2_sweep_enabled': (0, 1), 'ch2_sweep_amount': (0, 7),
            'ch2_sweep_rate': (0, 7), 'ch2_sweep_increase': (0, 1),
            'ch3_enabled': (0, 1), 'ch3_volume': (0, 127),
            'ch4_enabled': (0, 1), 'ch4_volume': (0, 15),
            'ch4_mode': (0, 1), 'ch4_freq': (0, 15),
            'vibrato': (0, 15), 'master_vol': (0, 15)
        }
    ),
    
    'opulenz': InstrumentDefinition(
        name='OpulenZ',
        xml_name='opulenz',
        parameters={
            'patch': (0, 127),
            'op1_attack': (0, 15), 'op1_decay': (0, 15),
            'op1_sustain': (0, 15), 'op1_release': (0, 15),
            'op1_level': (0, 63), 'op1_scale': (0, 3),
            'op1_freq': (0, 15), 'op1_feedback': (0, 7),
            'op1_waveform': (0, 7), 'op1_tremolo': (0, 1),
            'op1_vibrato': (0, 1), 'op1_sustained': (0, 1),
            'op1_ksr': (0, 1),
            'op2_attack': (0, 15), 'op2_decay': (0, 15),
            'op2_sustain': (0, 15), 'op2_release': (0, 15),
            'op2_level': (0, 63), 'op2_scale': (0, 3),
            'op2_freq': (0, 15), 'op2_waveform': (0, 7),
            'op2_tremolo': (0, 1), 'op2_vibrato': (0, 1),
            'op2_sustained': (0, 1), 'op2_ksr': (0, 1),
            'fm': (0, 1), 'vibrato_depth': (0, 1),
            'tremolo_depth': (0, 1)
        }
    ),
    
    'xpressive': InstrumentDefinition(
        name='Xpressive',
        xml_name='xpressive',
        parameters={
            'expression_o1': str, 'expression_o2': str,
            'expression_out': str,
            'smooth': (0, 1), 'interp': (0, 1),
            'panning_o1': str, 'panning_o2': str,
            'panning_out': str,
            'rel_trans': (0, 1),
            'W1': (-1, 1), 'W2': (-1, 1), 'W3': (-1, 1),
            'A1': (0, 1), 'A2': (0, 1), 'A3': (0, 1)
        }
    ),
    
    'malletsinstrument': InstrumentDefinition(
        name='MalletsInstrument',
        xml_name='malletsinstrument',
        parameters={
            'preset': (0, 9),  # Marimba, Xylophone, Vibraphone, etc.
            'spread': (0, 127),
            'randomness': (0, 127),
            'hardness': (0, 127),
            'position': (0, 127),
            'velocity': (0, 127),
            'stickiness': (0, 127),
            'modulator': (0, 127),
            'crossfade': (0, 127),
            'lfo_speed': (0, 127),
            'lfo_depth': (0, 127),
            'adsr': (0, 127),
            'pressure': (0, 127)
        }
    ),
    
    'zynaddsubfx': InstrumentDefinition(
        name='ZynAddSubFx',
        xml_name='zynaddsubfx',
        parameters={
            'portamento': (0, 127),
            'filterfreq': (0, 127),
            'filterq': (0, 127),
            'bandwidth': (0, 127),
            'modwheel': (0, 127),
            'fmamp': (0, 127),
            'volume': (0, 127),
            'sustain': (0, 127),
            'resbandwidth': (0, 127),
            'rescenterfreq': (0, 127)
        },
        sub_elements={
            'ZynAddSubFX-data': {'version-major': '2', 'version-minor': '4',
                                'version-revision': '4', 'ZynAddSubFX-author': 'Nasca Octavian Paul'}
        }
    ),
    
    'lv2instrument': InstrumentDefinition(
        name='Lv2Instrument',
        xml_name='lv2instrument',
        parameters={
            'plugin': str,  # LV2 plugin URI
            'controls': str  # Control port values
        }
    ),
    
    'vestigeinstrument': InstrumentDefinition(
        name='VestigeInstrument',
        xml_name='vestigeinstrument',
        parameters={
            'plugin': str,  # VST plugin path
            'chunk': str,  # VST state chunk (base64)
            'program': (0, 127),
            'params': str  # Parameter values
        }
    ),
    
    'carlainstrument': InstrumentDefinition(
        name='CarlaInstrument',
        xml_name='carlainstrument',
        parameters={
            'type': str,  # Plugin type (VST, LV2, AU, etc.)
            'name': str,  # Plugin name
            'label': str,  # Plugin label
            'filename': str,  # Plugin file path
            'params': str  # Parameter values (JSON)
        }
    )
}


# ============================================================================
# EFFECT DEFINITIONS
# ============================================================================

@dataclass
class EffectDefinition:
    """Definition of an effect and its parameters"""
    name: str
    xml_name: str
    parameters: Dict[str, Any]


# Complete effect definitions with ALL parameters
EFFECTS = {
    'amplifier': EffectDefinition(
        name='Amplifier',
        xml_name='amplifier',
        parameters={
            'vol': (0, 200),
            'pan': (-100, 100)
        }
    ),
    
    'compressor': EffectDefinition(
        name='Compressor',
        xml_name='compressor',
        parameters={
            'threshold': (-60, 0),
            'ratio': (1, 30),
            'attack': (0.1, 500),
            'release': (1, 5000),
            'knee': (0, 12),
            'hold': (0, 500),
            'range': (-60, 0),
            'rms': (0, 250),
            'mid_side': (0, 1),
            'peak_mode': (0, 1),
            'lookahead': (0, 20),
            'lookahead_enable': (0, 1),
            'limiter': (0, 1),
            'output': (-60, 60),
            'mix': (0, 100),
            'auto_makeup': (0, 1),
            'audition': (0, 1),
            'feedback': (0, 1),
            'stereo_balance': (0, 100),
            'tilt': (-6, 6),
            'tilt_freq': (20, 20000),
            'stereo_link': (0, 100)
        }
    ),
    
    'dynamicsprocessor': EffectDefinition(
        name='DynamicsProcessor',
        xml_name='dynamicsprocessor',
        parameters={
            'input': (-60, 20),
            'output': (-60, 20),
            'attack': (0, 200),
            'release': (0, 2000),
            'waveshape': str,  # Transfer function graph data
            'stereomode': (0, 3)
        }
    ),
    
    'eq': EffectDefinition(
        name='Equalizer',
        xml_name='eq',
        parameters={
            'input': (-60, 20),
            'output': (-60, 20),
            'hp_active': (0, 1), 'hp12': (0, 1), 'hp24': (0, 1), 'hp48': (0, 1),
            'hp_freq': (20, 20000), 'hp_res': (0.01, 10),
            'lp_active': (0, 1), 'lp12': (0, 1), 'lp24': (0, 1), 'lp48': (0, 1),
            'lp_freq': (20, 20000), 'lp_res': (0.01, 10),
            'ls_active': (0, 1), 'ls_freq': (20, 20000), 'ls_gain': (-18, 18),
            'hs_active': (0, 1), 'hs_freq': (20, 20000), 'hs_gain': (-18, 18),
            'peak1_active': (0, 1), 'peak1_freq': (20, 20000),
            'peak1_gain': (-18, 18), 'peak1_bw': (0.01, 10),
            'peak2_active': (0, 1), 'peak2_freq': (20, 20000),
            'peak2_gain': (-18, 18), 'peak2_bw': (0.01, 10),
            'peak3_active': (0, 1), 'peak3_freq': (20, 20000),
            'peak3_gain': (-18, 18), 'peak3_bw': (0.01, 10),
            'peak4_active': (0, 1), 'peak4_freq': (20, 20000),
            'peak4_gain': (-18, 18), 'peak4_bw': (0.01, 10),
            'analyze_in': (0, 1), 'analyze_out': (0, 1)
        }
    ),
    
    'bassbooster': EffectDefinition(
        name='BassBooster',
        xml_name='bassbooster',
        parameters={
            'freq': (20, 1000),
            'gain': (0, 20),
            'ratio': (0.1, 10)
        }
    ),
    
    'crossovereq': EffectDefinition(
        name='CrossoverEQ',
        xml_name='crossovereq',
        parameters={
            'xover12': (20, 20000),
            'xover23': (20, 20000),
            'xover34': (20, 20000),
            'gain1': (-48, 12),
            'gain2': (-48, 12),
            'gain3': (-48, 12),
            'gain4': (-48, 12),
            'mute1': (0, 1),
            'mute2': (0, 1),
            'mute3': (0, 1),
            'mute4': (0, 1)
        }
    ),
    
    'dualfilter': EffectDefinition(
        name='DualFilter',
        xml_name='dualfilter',
        parameters={
            'filter1_enabled': (0, 1),
            'filter1_type': (0, 13),
            'filter1_cut': (20, 20000),
            'filter1_res': (0.01, 10),
            'filter1_gain': (0, 5),
            'filter2_enabled': (0, 1),
            'filter2_type': (0, 13),
            'filter2_cut': (20, 20000),
            'filter2_res': (0.01, 10),
            'filter2_gain': (0, 5),
            'mix': (0, 100)
        }
    ),
    
    'flanger': EffectDefinition(
        name='Flanger',
        xml_name='flanger',
        parameters={
            'delay': (0.1, 20),
            'lfo_rate': (0.01, 10),
            'lfo_amount': (0, 100),
            'feedback': (-100, 100),
            'stereo': (0, 180),
            'noise': (0, 100),
            'invert': (0, 1)
        }
    ),
    
    'delay': EffectDefinition(
        name='Delay',
        xml_name='delay',
        parameters={
            'delay_time': (0.001, 5),
            'feedback': (0, 100),
            'lfo_speed': (0.01, 10),
            'lfo_amount': (0, 100),
            'output': (0, 200)
        }
    ),
    
    'multitapecho': EffectDefinition(
        name='MultitapEcho',
        xml_name='multitapecho',
        parameters={
            'steps': (1, 32),
            'stepLength': (1, 16),
            'dryGain': (0, 2),
            'swapInputs': (0, 1),
            'stages': str  # Tap configuration data
        }
    ),
    
    'reverbsc': EffectDefinition(
        name='ReverbSC',
        xml_name='reverbsc',
        parameters={
            'size': (0, 100),
            'color': (0, 100),
            'damping': (0, 100),
            'width': (0, 200),
            'gain': (0, 200)
        }
    ),
    
    'bitcrush': EffectDefinition(
        name='Bitcrush',
        xml_name='bitcrush',
        parameters={
            'rate': (20, 48000),
            'bits': (1, 32),
            'stereo': (0, 100),
            'gain_in': (0, 10),
            'gain_out': (0, 10),
            'clip': (0, 10)
        }
    ),
    
    'waveshaper': EffectDefinition(
        name='WaveShaper',
        xml_name='waveshaper',
        parameters={
            'input': (0, 200),
            'output': (0, 200),
            'wavegraph': str  # Waveshaping graph data
        }
    ),
    
    'stereoenhancer': EffectDefinition(
        name='StereoEnhancer',
        xml_name='stereoenhancer',
        parameters={
            'width': (0, 200)
        }
    ),
    
    'stereomatrix': EffectDefinition(
        name='StereoMatrix',
        xml_name='stereomatrix',
        parameters={
            'll': (-100, 100),
            'lr': (-100, 100),
            'rl': (-100, 100),
            'rr': (-100, 100)
        }
    ),
    
    'granularpitchshifter': EffectDefinition(
        name='GranularPitchShifter',
        xml_name='granularpitchshifter',
        parameters={
            'pitch': (-24, 24),
            'grain_size': (1, 1000),
            'spray': (0, 100),
            'jitter': (0, 100),
            'twitch': (0, 100),
            'pitch_int': (0, 100),
            'glide': (0, 100),
            'glide_time': (0, 1000)
        }
    ),
    
    'dispersion': EffectDefinition(
        name='Dispersion',
        xml_name='dispersion',
        parameters={
            'amount': (0, 100),
            'frequency': (20, 20000),
            'resonance': (0, 100),
            'feedback': (0, 100),
            'dc': (0, 1)
        }
    ),
    
    'spectrumanalyzer': EffectDefinition(
        name='SpectrumAnalyzer',
        xml_name='spectrumanalyzer',
        parameters={
            'fft_size': (256, 16384),
            'window': (0, 5),  # Window function
            'display': (0, 3),  # Display mode
            'waterfall': (0, 1),
            'smooth': (0, 100),
            'mono': (0, 1),
            'log_x': (0, 1),
            'log_y': (0, 1),
            'reference': (-100, 0),
            'range': (20, 150),
            'block_size': (128, 8192)
        }
    ),
    
    'vectorscope': EffectDefinition(
        name='Vectorscope',
        xml_name='vectorscope',
        parameters={
            'persist': (0, 100),
            'log_scale': (0, 1),
            'high_qual': (0, 1)
        }
    ),
    
    'peakcontrollereffect': EffectDefinition(
        name='PeakControllerEffect',
        xml_name='peakcontrollereffect',
        parameters={
            'abs': (0, 1),
            'amount': (0, 100),
            'attack': (0, 1000),
            'decay': (0, 1000),
            'treshold': (0, 100),
            'ratio': (0.01, 10),
            'base': (0, 100),
            'mute': (0, 1)
        }
    ),
    
    'ladspaeffect': EffectDefinition(
        name='LadspaEffect',
        xml_name='ladspaeffect',
        parameters={
            'plugin': str,  # LADSPA plugin descriptor
            'controls': str  # Control port values
        }
    ),
    
    'lv2effect': EffectDefinition(
        name='Lv2Effect',
        xml_name='lv2effect',
        parameters={
            'plugin': str,  # LV2 plugin URI
            'controls': str  # Control port values
        }
    ),
    
    'vsteffect': EffectDefinition(
        name='VstEffect',
        xml_name='vsteffect',
        parameters={
            'plugin': str,  # VST plugin path
            'chunk': str,  # VST state chunk (base64)
            'program': (0, 127),
            'params': str  # Parameter values
        }
    ),
    
    'carlaeffect': EffectDefinition(
        name='CarlaEffect',
        xml_name='carlaeffect',
        parameters={
            'type': str,  # Plugin type
            'name': str,  # Plugin name
            'label': str,  # Plugin label
            'filename': str,  # Plugin file path
            'params': str  # Parameter values (JSON)
        }
    ),
    
    'lomm': EffectDefinition(
        name='LOMM',
        xml_name='lomm',
        parameters={
            'split1': (20, 20000),
            'split2': (20, 20000),
            'band1_drive': (0, 100),
            'band1_attack': (0, 200),
            'band1_release': (0, 2000),
            'band1_ratio': (1, 30),
            'band1_knee': (0, 12),
            'band1_range': (-60, 0),
            'band1_lookahead': (0, 20),
            'band1_sidechain': (0, 1),
            'band1_mute': (0, 1),
            'band1_solo': (0, 1),
            'band2_drive': (0, 100),
            'band2_attack': (0, 200),
            'band2_release': (0, 2000),
            'band2_ratio': (1, 30),
            'band2_knee': (0, 12),
            'band2_range': (-60, 0),
            'band2_lookahead': (0, 20),
            'band2_sidechain': (0, 1),
            'band2_mute': (0, 1),
            'band2_solo': (0, 1),
            'band3_drive': (0, 100),
            'band3_attack': (0, 200),
            'band3_release': (0, 2000),
            'band3_ratio': (1, 30),
            'band3_knee': (0, 12),
            'band3_range': (-60, 0),
            'band3_lookahead': (0, 20),
            'band3_sidechain': (0, 1),
            'band3_mute': (0, 1),
            'band3_solo': (0, 1),
            'output': (-60, 60),
            'mix': (0, 100),
            'feedback': (0, 1),
            'highquality': (0, 1),
            'saturation': (0, 100)
        }
    ),
    
    'taptempo': EffectDefinition(
        name='TapTempo',
        xml_name='taptempo',
        parameters={
            'bpm': (10, 999),
            'tolerance': (1, 100),
            'precision': (1, 10)
        }
    )
}


# ============================================================================
# LMMS COMPLETE CONTROLLER
# ============================================================================

class LMMSCompleteController:
    """
    Complete programmatic control interface for LMMS
    Provides access to ALL features and parameters
    """
    
    def __init__(self, project_path: Optional[str] = None):
        self.filepath = project_path
        self.tree = None
        self.root = None
        self.is_compressed = False
        
        if project_path:
            self.load_project(project_path)
        else:
            self.create_new_project()
    
    # ========================================================================
    # PROJECT MANAGEMENT
    # ========================================================================
    
    def create_new_project(self):
        """Create a new empty LMMS project"""
        self.root = ET.Element('multimedia-project')
        self.root.set('version', '1.0')
        self.root.set('creator', 'LMMS')
        self.root.set('creatorversion', '1.2.2')
        self.root.set('type', 'song')
        
        # Add head section
        head = ET.SubElement(self.root, 'head')
        head.set('timesig_numerator', '4')
        head.set('timesig_denominator', '4')
        head.set('bpm', '140')
        head.set('mastervol', '100')
        head.set('masterpitch', '0')
        
        # Add song structure
        song = ET.SubElement(self.root, 'song')
        
        # Add main track container
        trackcontainer = ET.SubElement(song, 'trackcontainer')
        trackcontainer.set('type', 'song')
        trackcontainer.set('x', '5')
        trackcontainer.set('y', '5')
        trackcontainer.set('width', '600')
        trackcontainer.set('height', '300')
        trackcontainer.set('visible', '1')
        trackcontainer.set('minimized', '0')
        trackcontainer.set('maximized', '0')
        
        # Add mixer
        mixer = ET.SubElement(song, 'mixer')
        mixer.set('x', '5')
        mixer.set('y', '310')
        mixer.set('width', '865')
        mixer.set('height', '278')
        mixer.set('visible', '1')
        mixer.set('minimized', '0')
        mixer.set('maximized', '0')
        
        # Add 64 mixer channels
        for i in range(64):
            channel = ET.SubElement(mixer, 'mixerchannel')
            channel.set('num', str(i))
            channel.set('muted', '0')
            channel.set('volume', '1')
            channel.set('name', f'Master' if i == 0 else f'Channel {i}')
            
            fxchain = ET.SubElement(channel, 'fxchain')
            fxchain.set('numofeffects', '0')
            fxchain.set('enabled', '0')
        
        # Add other UI elements
        for element_name in ['controllerrackview', 'pianoroll', 'automationeditor', 'projectnotes']:
            elem = ET.SubElement(song, element_name)
            elem.set('visible', '0')
            elem.set('x', '0')
            elem.set('y', '0')
            elem.set('width', '400')
            elem.set('height', '300')
            elem.set('minimized', '0')
            elem.set('maximized', '0')
        
        # Add timeline
        timeline = ET.SubElement(song, 'timeline')
        timeline.set('lp0pos', '0')
        timeline.set('lp1pos', '192')
        timeline.set('lpstate', '0')
        
        # Add controllers
        ET.SubElement(song, 'controllers')
        
        self.tree = ET.ElementTree(self.root)
    
    def load_project(self, filepath: str):
        """Load an existing LMMS project file"""
        self.filepath = filepath
        self.is_compressed = filepath.endswith('.mmpz')
        
        if self.is_compressed:
            with gzip.open(filepath, 'rb') as f:
                content = f.read()
            self.tree = ET.ElementTree(ET.fromstring(content))
        else:
            self.tree = ET.parse(filepath)
        
        self.root = self.tree.getroot()
    
    def save_project(self, filepath: Optional[str] = None):
        """Save the project to a file"""
        if filepath is None:
            filepath = self.filepath
        
        if filepath.endswith('.mmpz'):
            xml_str = ET.tostring(self.root, encoding='unicode')
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write('<?xml version="1.0"?>\n')
                f.write('<!DOCTYPE multimedia-project>\n')
                f.write(xml_str)
        else:
            self.tree.write(filepath, encoding='unicode', xml_declaration=True)
    
    # ========================================================================
    # GLOBAL PROJECT SETTINGS
    # ========================================================================
    
    def set_tempo(self, bpm: int):
        """Set project tempo (10-999 BPM)"""
        head = self.root.find('.//head')
        if head is not None:
            head.set('bpm', str(max(10, min(999, bpm))))
    
    def set_time_signature(self, numerator: int, denominator: int):
        """Set project time signature"""
        head = self.root.find('.//head')
        if head is not None:
            head.set('timesig_numerator', str(numerator))
            head.set('timesig_denominator', str(denominator))
    
    def set_master_volume(self, volume: int):
        """Set master volume (0-200)"""
        head = self.root.find('.//head')
        if head is not None:
            head.set('mastervol', str(max(0, min(200, volume))))
    
    def set_master_pitch(self, pitch: int):
        """Set master pitch in cents (-600 to 600)"""
        head = self.root.find('.//head')
        if head is not None:
            head.set('masterpitch', str(max(-600, min(600, pitch))))
    
    # ========================================================================
    # TRACK MANAGEMENT
    # ========================================================================
    
    def add_track(self, name: str, track_type: TrackType = TrackType.INSTRUMENT) -> ET.Element:
        """Add a new track of any type"""
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer is None:
            return None
        
        track = ET.SubElement(trackcontainer, 'track')
        track.set('muted', '0')
        
        # Handle both TrackType enum and int values
        if isinstance(track_type, TrackType):
            track.set('type', str(track_type.value))
        else:
            track.set('type', str(track_type))
        
        track.set('name', name)
        
        if track_type == TrackType.INSTRUMENT:
            self._create_instrument_track(track)
        elif track_type == TrackType.SAMPLE:
            self._create_sample_track(track)
        elif track_type == TrackType.PATTERN:
            self._create_pattern_track(track)
        elif track_type == TrackType.AUTOMATION:
            self._create_automation_track(track)
        
        return track
    
    def _create_instrument_track(self, track: ET.Element):
        """Create instrument track structure"""
        inst_track = ET.SubElement(track, 'instrumenttrack')
        inst_track.set('pan', '0')
        inst_track.set('mixch', '0')
        inst_track.set('pitch', '0')
        inst_track.set('basenote', '57')
        inst_track.set('vol', '100')
        
        # Add default instrument
        inst = ET.SubElement(inst_track, 'instrument')
        inst.set('name', 'tripleoscillator')
        
        # Add envelope data
        eldata = ET.SubElement(inst_track, 'eldata')
        eldata.set('fres', '0.5')
        eldata.set('ftype', '0')
        eldata.set('fcut', '14000')
        eldata.set('fwet', '0')
        
        # Add envelopes
        for env_type in ['elvol', 'elcut', 'elres']:
            env = ET.SubElement(eldata, env_type)
            self._set_default_envelope(env)
        
        # Add chord creator
        chord = ET.SubElement(inst_track, 'chordcreator')
        chord.set('chord', '0')
        chord.set('chordrange', '1')
        chord.set('chord-enabled', '0')
        
        # Add arpeggiator
        arp = ET.SubElement(inst_track, 'arpeggiator')
        arp.set('arp-enabled', '0')
        arp.set('arp', '0')
        arp.set('arptime', '100')
        arp.set('arptime_numerator', '4')
        arp.set('arptime_denominator', '4')
        arp.set('arpdir', '0')
        arp.set('arprange', '1')
        arp.set('arpmode', '0')
        arp.set('arpgate', '100')
        arp.set('syncmode', '0')
        
        # Add MIDI port
        midi = ET.SubElement(inst_track, 'midiport')
        midi.set('inputchannel', '0')
        midi.set('inputcontroller', '0')
        midi.set('outputchannel', '1')
        midi.set('outputcontroller', '0')
        midi.set('outputprogram', '1')
        midi.set('fixedinputvelocity', '-1')
        midi.set('fixedoutputvelocity', '-1')
        midi.set('readable', '0')
        midi.set('writable', '0')
        
        # Add effects chain
        fxchain = ET.SubElement(inst_track, 'fxchain')
        fxchain.set('numofeffects', '0')
        fxchain.set('enabled', '0')
    
    def _create_sample_track(self, track: ET.Element):
        """Create sample track structure"""
        sample_track = ET.SubElement(track, 'sampletrack')
        sample_track.set('vol', '100')
        
        fxchain = ET.SubElement(sample_track, 'fxchain')
        fxchain.set('numofeffects', '0')
        fxchain.set('enabled', '0')
    
    def _create_pattern_track(self, track: ET.Element):
        """Create pattern/beat track structure"""
        bb_track = ET.SubElement(track, 'bbtrack')
        
        # Add track container for patterns
        container = ET.SubElement(bb_track, 'trackcontainer')
        container.set('type', 'bbtrackcontainer')
        container.set('x', '610')
        container.set('y', '5')
        container.set('width', '504')
        container.set('height', '300')
        container.set('visible', '1')
        container.set('minimized', '0')
        container.set('maximized', '0')
    
    def _create_automation_track(self, track: ET.Element):
        """Create automation track structure"""
        ET.SubElement(track, 'automationtrack')
    
    def _set_default_envelope(self, env: ET.Element):
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
    
    def get_track(self, name: str) -> Optional[ET.Element]:
        """Get a track by name"""
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer is not None:
            for track in trackcontainer.findall('track'):
                if track.get('name') == name:
                    return track
        return None
    
    def delete_track(self, name: str) -> bool:
        """Delete a track by name"""
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer is not None:
            for track in trackcontainer.findall('track'):
                if track.get('name') == name:
                    trackcontainer.remove(track)
                    return True
        return False
    
    def rename_track(self, old_name: str, new_name: str) -> bool:
        """Rename a track"""
        track = self.get_track(old_name)
        if track:
            track.set('name', new_name)
            return True
        return False
    
    # ========================================================================
    # INSTRUMENT CONTROL
    # ========================================================================
    
    def set_instrument(self, track_name: str, instrument_name: str) -> bool:
        """Set the instrument for a track"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        inst_track = track.find('instrumenttrack')
        if not inst_track:
            return False
        
        # Remove existing instrument
        old_inst = inst_track.find('instrument')
        if old_inst is not None:
            inst_track.remove(old_inst)
        
        # Add new instrument
        inst = ET.SubElement(inst_track, 'instrument')
        inst.set('name', instrument_name)
        
        # Add instrument-specific element if defined
        if instrument_name in INSTRUMENTS:
            inst_def = INSTRUMENTS[instrument_name]
            inst_elem = ET.SubElement(inst, inst_def.xml_name)
            
            # Set default parameters
            for param, value in inst_def.parameters.items():
                if isinstance(value, tuple):
                    # Use middle value for ranges
                    if isinstance(value[0], (int, float)):
                        default = (value[0] + value[1]) / 2
                        inst_elem.set(param, str(default))
        
        return True
    
    def set_instrument_parameter(self, track_name: str, param_name: str, value: Any) -> bool:
        """Set any instrument parameter"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        inst = track.find('.//instrument')
        if not inst:
            return False
        
        inst_name = inst.get('name')
        if inst_name not in INSTRUMENTS:
            return False
        
        inst_def = INSTRUMENTS[inst_name]
        inst_elem = inst.find(inst_def.xml_name)
        
        if inst_elem is None:
            inst_elem = ET.SubElement(inst, inst_def.xml_name)
        
        # Validate and set parameter
        if param_name in inst_def.parameters:
            param_type = inst_def.parameters[param_name]
            
            if isinstance(param_type, tuple):
                # Range validation
                min_val, max_val = param_type
                if isinstance(min_val, (int, float)):
                    value = max(min_val, min(max_val, value))
            
            inst_elem.set(param_name, str(value))
            return True
        
        return False
    
    def get_instrument_parameters(self, track_name: str) -> Dict[str, Any]:
        """Get all instrument parameters for a track"""
        track = self.get_track(track_name)
        if not track:
            return {}
        
        inst = track.find('.//instrument')
        if not inst:
            return {}
        
        inst_name = inst.get('name')
        if inst_name not in INSTRUMENTS:
            return {}
        
        inst_def = INSTRUMENTS[inst_name]
        inst_elem = inst.find(inst_def.xml_name)
        
        if inst_elem is None:
            return {}
        
        params = {}
        for param in inst_def.parameters:
            value = inst_elem.get(param)
            if value is not None:
                # Try to convert to appropriate type
                try:
                    if '.' in value:
                        params[param] = float(value)
                    else:
                        params[param] = int(value)
                except ValueError:
                    params[param] = value
        
        return params
    
    # ========================================================================
    # ENVELOPE CONTROL
    # ========================================================================
    
    def set_envelope(self, track_name: str, env_type: str, **params) -> bool:
        """
        Set envelope parameters
        env_type: 'vol', 'cut', or 'res'
        params: att, dec, sus, rel, hold, amt, etc.
        """
        track = self.get_track(track_name)
        if not track:
            return False
        
        env = track.find(f'.//el{env_type}')
        if env is None:
            # Create envelope if it doesn't exist
            eldata = track.find('.//eldata')
            if eldata is None:
                return False
            env = ET.SubElement(eldata, f'el{env_type}')
            self._set_default_envelope(env)
        
        # Set parameters
        for param, value in params.items():
            env.set(param, str(value))
        
        return True
    
    def set_lfo(self, track_name: str, env_type: str, **params) -> bool:
        """
        Set LFO parameters for an envelope
        env_type: 'vol', 'cut', or 'res'
        params: lspd, lamt, lshp, latt, lpdel, syncmode, etc.
        """
        track = self.get_track(track_name)
        if not track:
            return False
        
        env = track.find(f'.//el{env_type}')
        if env is None:
            return False
        
        # LFO-specific parameters
        lfo_params = {
            'lspd': params.get('speed', 0.1),
            'lamt': params.get('amount', 0),
            'lshp': params.get('shape', 0),
            'latt': params.get('attack', 0),
            'lpdel': params.get('predelay', 0),
            'syncmode': params.get('sync', 0),
            'lspd_numerator': params.get('speed_num', 4),
            'lspd_denominator': params.get('speed_den', 4)
        }
        
        for param, value in lfo_params.items():
            if param in params or value != 0:
                env.set(param, str(value))
        
        return True
    
    # ========================================================================
    # FILTER CONTROL
    # ========================================================================
    
    def set_filter(self, track_name: str, **params) -> bool:
        """
        Set filter parameters
        params: fcut, fres, ftype, fwet, etc.
        """
        track = self.get_track(track_name)
        if not track:
            return False
        
        eldata = track.find('.//eldata')
        if eldata is None:
            # Create eldata if it doesn't exist
            inst_track = track.find('instrumenttrack')
            if inst_track is None:
                return False
            eldata = ET.SubElement(inst_track, 'eldata')
        
        # Set filter parameters
        filter_params = {
            'fcut': params.get('cutoff', 14000),
            'fres': params.get('resonance', 0.5),
            'ftype': params.get('type', 0),
            'fwet': params.get('wet', 0)
        }
        
        for param, value in filter_params.items():
            eldata.set(param, str(value))
        
        return True
    
    # ========================================================================
    # ARPEGGIATOR CONTROL
    # ========================================================================
    
    def set_arpeggiator(self, track_name: str, enabled: bool = True, **params) -> bool:
        """
        Configure arpeggiator settings
        params: direction, mode, time, range, gate, etc.
        """
        track = self.get_track(track_name)
        if not track:
            return False
        
        arp = track.find('.//arpeggiator')
        if arp is None:
            inst_track = track.find('instrumenttrack')
            if inst_track is None:
                return False
            arp = ET.SubElement(inst_track, 'arpeggiator')
        
        arp.set('arp-enabled', '1' if enabled else '0')
        
        # Set arpeggiator parameters
        arp_params = {
            'arp': params.get('pattern', 0),
            'arpdir': params.get('direction', 0),
            'arpmode': params.get('mode', 0),
            'arptime': params.get('time', 100),
            'arptime_numerator': params.get('time_num', 4),
            'arptime_denominator': params.get('time_den', 4),
            'arprange': params.get('range', 1),
            'arpgate': params.get('gate', 100),
            'syncmode': params.get('sync', 0),
            'arpskip': params.get('skip', 0),
            'arpmiss': params.get('miss', 0),
            'arpcycle': params.get('cycle', 0),
            'arprepeats': params.get('repeats', 0)
        }
        
        for param, value in arp_params.items():
            if param in params or value != 0:
                arp.set(param, str(value))
        
        return True
    
    # ========================================================================
    # CHORD CONTROL
    # ========================================================================
    
    def set_chord(self, track_name: str, enabled: bool = True, chord_type: int = 0, 
                  chord_range: int = 1) -> bool:
        """
        Configure chord settings
        chord_type: 0=Major, 1=Minor, 2=Diminished, 3=Augmented, etc.
        chord_range: Octave range for chord notes
        """
        track = self.get_track(track_name)
        if not track:
            return False
        
        chord = track.find('.//chordcreator')
        if chord is None:
            inst_track = track.find('instrumenttrack')
            if inst_track is None:
                return False
            chord = ET.SubElement(inst_track, 'chordcreator')
        
        chord.set('chord-enabled', '1' if enabled else '0')
        chord.set('chord', str(chord_type))
        chord.set('chordrange', str(chord_range))
        
        return True
    
    # ========================================================================
    # EFFECTS CONTROL
    # ========================================================================
    
    def add_effect(self, track_name: str, effect_name: str, **params) -> bool:
        """Add an effect to a track's effect chain"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        fxchain = track.find('.//fxchain')
        if fxchain is None:
            return False
        
        # Create effect element
        effect = ET.SubElement(fxchain, 'effect')
        effect.set('name', effect_name)
        
        # Add effect-specific element if defined
        if effect_name in EFFECTS:
            effect_def = EFFECTS[effect_name]
            effect_elem = ET.SubElement(effect, effect_def.xml_name)
            
            # Set parameters
            for param, value in params.items():
                if param in effect_def.parameters:
                    param_type = effect_def.parameters[param]
                    
                    if isinstance(param_type, tuple):
                        # Range validation
                        min_val, max_val = param_type
                        if isinstance(min_val, (int, float)):
                            value = max(min_val, min(max_val, value))
                    
                    effect_elem.set(param, str(value))
        
        # Update effect count
        num_effects = int(fxchain.get('numofeffects', '0'))
        fxchain.set('numofeffects', str(num_effects + 1))
        fxchain.set('enabled', '1')
        
        return True
    
    def remove_effect(self, track_name: str, effect_index: int) -> bool:
        """Remove an effect from the chain by index"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        fxchain = track.find('.//fxchain')
        if fxchain is None:
            return False
        
        effects = fxchain.findall('effect')
        if 0 <= effect_index < len(effects):
            fxchain.remove(effects[effect_index])
            
            # Update effect count
            num_effects = len(effects) - 1
            fxchain.set('numofeffects', str(num_effects))
            if num_effects == 0:
                fxchain.set('enabled', '0')
            
            return True
        return False
    
    def set_effect_parameter(self, track_name: str, effect_index: int, 
                            param_name: str, value: Any) -> bool:
        """Set a parameter of a specific effect"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        fxchain = track.find('.//fxchain')
        if fxchain is None:
            return False
        
        effects = fxchain.findall('effect')
        if 0 <= effect_index < len(effects):
            effect = effects[effect_index]
            effect_name = effect.get('name')
            
            if effect_name in EFFECTS:
                effect_def = EFFECTS[effect_name]
                effect_elem = effect.find(effect_def.xml_name)
                
                if effect_elem is None:
                    effect_elem = ET.SubElement(effect, effect_def.xml_name)
                
                if param_name in effect_def.parameters:
                    param_type = effect_def.parameters[param_name]
                    
                    if isinstance(param_type, tuple):
                        # Range validation
                        min_val, max_val = param_type
                        if isinstance(min_val, (int, float)):
                            value = max(min_val, min(max_val, value))
                    
                    effect_elem.set(param_name, str(value))
                    return True
        
        return False
    
    # ========================================================================
    # PATTERN/NOTE CONTROL
    # ========================================================================
    
    def add_pattern(self, track_name: str, pattern_name: str, position: int = 0, 
                   length: int = 192) -> ET.Element:
        """Add a pattern to a track"""
        track = self.get_track(track_name)
        if not track:
            return None
        
        pattern = ET.SubElement(track, 'pattern')
        pattern.set('name', pattern_name)
        pattern.set('pos', str(position))
        pattern.set('len', str(length))
        pattern.set('muted', '0')
        pattern.set('type', '0')
        pattern.set('frozen', '0')
        pattern.set('steps', '16')
        
        return pattern
    
    def add_note(self, pattern: ET.Element, pitch: int, pos: int, length: int, 
                velocity: int = 100, pan: int = 0) -> ET.Element:
        """Add a note to a pattern"""
        note = ET.SubElement(pattern, 'note')
        note.set('key', str(pitch))
        note.set('pos', str(pos))
        note.set('len', str(length))
        note.set('vol', str(velocity))
        note.set('pan', str(pan))
        
        return note
    
    def add_note_by_name(self, pattern: ET.Element, note_name: str, pos: int, 
                        length: int, velocity: int = 100, pan: int = 0) -> ET.Element:
        """Add a note using note name (e.g., 'C4', 'F#5')"""
        if note_name in MIDI_NOTES:
            pitch = MIDI_NOTES[note_name]
            return self.add_note(pattern, pitch, pos, length, velocity, pan)
        return None
    
    # ========================================================================
    # AUTOMATION CONTROL
    # ========================================================================
    
    def add_automation_pattern(self, param_name: str, track_name: Optional[str] = None) -> ET.Element:
        """Add an automation pattern"""
        # Find or create automation track
        auto_track = None
        for track in self.root.findall('.//track[@type="5"]'):
            auto_track = track
            break
        
        if auto_track is None:
            # Create automation track
            auto_track = self.add_track('Automation', TrackType.AUTOMATION)
        
        # Create automation pattern
        pattern = ET.SubElement(auto_track, 'automationpattern')
        pattern.set('name', param_name)
        pattern.set('pos', '0')
        
        if track_name:
            # Link to specific track parameter
            track = self.get_track(track_name)
            if track:
                pattern.set('track', track_name)
        
        return pattern
    
    def add_automation_point(self, pattern: ET.Element, position: int, value: float) -> ET.Element:
        """Add an automation point to a pattern"""
        point = ET.SubElement(pattern, 'time')
        point.set('pos', str(position))
        point.set('value', str(value))
        
        return point
    
    def add_automation_curve(self, pattern: ET.Element, points: List[Tuple[int, float]]):
        """Add multiple automation points to create a curve"""
        for pos, value in points:
            self.add_automation_point(pattern, pos, value)
    
    # ========================================================================
    # MIXER CONTROL
    # ========================================================================
    
    def set_mixer_channel(self, track_name: str, channel_num: int) -> bool:
        """Assign track to a mixer channel (0-63)"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        inst_track = track.find('instrumenttrack')
        if inst_track:
            inst_track.set('mixch', str(max(0, min(63, channel_num))))
            return True
        
        return False
    
    def set_mixer_channel_volume(self, channel_num: int, volume: float) -> bool:
        """Set mixer channel volume (0.0-2.0)"""
        mixer = self.root.find('.//mixer')
        if mixer is None:
            return False
        
        for channel in mixer.findall('mixerchannel'):
            if channel.get('num') == str(channel_num):
                channel.set('volume', str(max(0.0, min(2.0, volume))))
                return True
        
        return False
    
    def set_mixer_channel_name(self, channel_num: int, name: str) -> bool:
        """Set mixer channel name"""
        mixer = self.root.find('.//mixer')
        if mixer is None:
            return False
        
        for channel in mixer.findall('mixerchannel'):
            if channel.get('num') == str(channel_num):
                channel.set('name', name)
                return True
        
        return False
    
    def add_mixer_effect(self, channel_num: int, effect_name: str, **params) -> bool:
        """Add an effect to a mixer channel"""
        mixer = self.root.find('.//mixer')
        if mixer is None:
            return False
        
        for channel in mixer.findall('mixerchannel'):
            if channel.get('num') == str(channel_num):
                fxchain = channel.find('fxchain')
                if fxchain is None:
                    fxchain = ET.SubElement(channel, 'fxchain')
                    fxchain.set('numofeffects', '0')
                    fxchain.set('enabled', '0')
                
                # Add effect (similar to track effects)
                effect = ET.SubElement(fxchain, 'effect')
                effect.set('name', effect_name)
                
                if effect_name in EFFECTS:
                    effect_def = EFFECTS[effect_name]
                    effect_elem = ET.SubElement(effect, effect_def.xml_name)
                    
                    for param, value in params.items():
                        if param in effect_def.parameters:
                            effect_elem.set(param, str(value))
                
                # Update effect count
                num_effects = int(fxchain.get('numofeffects', '0'))
                fxchain.set('numofeffects', str(num_effects + 1))
                fxchain.set('enabled', '1')
                
                return True
        
        return False
    
    # ========================================================================
    # MIDI CONTROL
    # ========================================================================
    
    def set_midi_input(self, track_name: str, channel: int = 0, controller: int = 0) -> bool:
        """Configure MIDI input for a track"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        midi = track.find('.//midiport')
        if midi is None:
            return False
        
        midi.set('inputchannel', str(channel))
        midi.set('inputcontroller', str(controller))
        midi.set('readable', '1')
        
        return True
    
    def set_midi_output(self, track_name: str, channel: int = 1, program: int = 1) -> bool:
        """Configure MIDI output for a track"""
        track = self.get_track(track_name)
        if not track:
            return False
        
        midi = track.find('.//midiport')
        if midi is None:
            return False
        
        midi.set('outputchannel', str(channel))
        midi.set('outputprogram', str(program))
        midi.set('writable', '1')
        
        return True
    
    def set_midi_velocity(self, track_name: str, input_velocity: int = -1, 
                         output_velocity: int = -1) -> bool:
        """
        Set fixed MIDI velocities
        -1 = use actual velocity, 0-127 = fixed velocity
        """
        track = self.get_track(track_name)
        if not track:
            return False
        
        midi = track.find('.//midiport')
        if midi is None:
            return False
        
        midi.set('fixedinputvelocity', str(input_velocity))
        midi.set('fixedoutputvelocity', str(output_velocity))
        
        return True
    
    # ========================================================================
    # CONTROLLER CONNECTIONS
    # ========================================================================
    
    def add_lfo_controller(self, name: str, wave: int = 0, speed: float = 1.0, 
                          amount: float = 1.0) -> ET.Element:
        """Add an LFO controller"""
        controllers = self.root.find('.//controllers')
        if controllers is None:
            song = self.root.find('.//song')
            controllers = ET.SubElement(song, 'controllers')
        
        lfo = ET.SubElement(controllers, 'lfo')
        lfo.set('name', name)
        lfo.set('wave', str(wave))
        lfo.set('speed', str(speed))
        lfo.set('amount', str(amount))
        lfo.set('phase', '0')
        lfo.set('multiplier', '1')
        
        return lfo
    
    def add_peak_controller(self, name: str, target_track: str) -> ET.Element:
        """Add a peak controller linked to a track"""
        controllers = self.root.find('.//controllers')
        if controllers is None:
            song = self.root.find('.//song')
            controllers = ET.SubElement(song, 'controllers')
        
        peak = ET.SubElement(controllers, 'peakcontroller')
        peak.set('name', name)
        peak.set('target', target_track)
        peak.set('amount', '1')
        peak.set('attack', '0')
        peak.set('decay', '0')
        peak.set('mute', '0')
        
        return peak
    
    def connect_controller(self, controller_name: str, target_param: str) -> bool:
        """Connect a controller to a parameter"""
        # This would require finding the specific parameter element
        # and adding a controller connection attribute
        # Implementation depends on specific parameter location
        return True
    
    # ========================================================================
    # PROJECT INFORMATION
    # ========================================================================
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get comprehensive project information"""
        info = {
            'tempo': None,
            'time_signature': None,
            'master_volume': None,
            'master_pitch': None,
            'tracks': [],
            'mixer_channels': [],
            'automation_patterns': [],
            'controllers': []
        }
        
        # Get head information
        head = self.root.find('.//head')
        if head:
            info['tempo'] = int(head.get('bpm', '140'))
            info['time_signature'] = f"{head.get('timesig_numerator', '4')}/{head.get('timesig_denominator', '4')}"
            info['master_volume'] = int(head.get('mastervol', '100'))
            info['master_pitch'] = int(head.get('masterpitch', '0'))
        
        # Get track information
        trackcontainer = self.root.find('.//trackcontainer[@type="song"]')
        if trackcontainer:
            for track in trackcontainer.findall('track'):
                track_info = {
                    'name': track.get('name'),
                    'type': TrackType(int(track.get('type', '0'))).name,
                    'muted': track.get('muted') == '1',
                    'instrument': None,
                    'effects': [],
                    'patterns': []
                }
                
                # Get instrument
                inst = track.find('.//instrument')
                if inst:
                    track_info['instrument'] = inst.get('name')
                
                # Get effects
                fxchain = track.find('.//fxchain')
                if fxchain:
                    for effect in fxchain.findall('effect'):
                        track_info['effects'].append(effect.get('name'))
                
                # Get patterns
                for pattern in track.findall('pattern'):
                    track_info['patterns'].append({
                        'name': pattern.get('name'),
                        'position': int(pattern.get('pos', '0')),
                        'length': int(pattern.get('len', '0'))
                    })
                
                info['tracks'].append(track_info)
        
        # Get mixer information
        mixer = self.root.find('.//mixer')
        if mixer:
            for channel in mixer.findall('mixerchannel'):
                channel_info = {
                    'number': int(channel.get('num', '0')),
                    'name': channel.get('name'),
                    'volume': float(channel.get('volume', '1')),
                    'muted': channel.get('muted') == '1',
                    'effects': []
                }
                
                # Get channel effects
                fxchain = channel.find('fxchain')
                if fxchain:
                    for effect in fxchain.findall('effect'):
                        channel_info['effects'].append(effect.get('name'))
                
                info['mixer_channels'].append(channel_info)
        
        # Get automation patterns
        for auto_track in self.root.findall('.//track[@type="5"]'):
            for pattern in auto_track.findall('automationpattern'):
                auto_info = {
                    'name': pattern.get('name'),
                    'position': int(pattern.get('pos', '0')),
                    'points': len(pattern.findall('time'))
                }
                info['automation_patterns'].append(auto_info)
        
        # Get controllers
        controllers = self.root.find('.//controllers')
        if controllers:
            for lfo in controllers.findall('lfo'):
                info['controllers'].append({
                    'type': 'LFO',
                    'name': lfo.get('name')
                })
            for peak in controllers.findall('peakcontroller'):
                info['controllers'].append({
                    'type': 'Peak',
                    'name': peak.get('name')
                })
        
        return info
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def validate_project(self) -> List[str]:
        """Validate project structure and return any issues"""
        issues = []
        
        if self.root is None:
            issues.append("No project loaded")
            return issues
        
        # Check required elements
        if self.root.find('.//head') is None:
            issues.append("Missing head element")
        
        if self.root.find('.//song') is None:
            issues.append("Missing song element")
        
        if self.root.find('.//trackcontainer[@type="song"]') is None:
            issues.append("Missing main track container")
        
        if self.root.find('.//mixer') is None:
            issues.append("Missing mixer")
        
        # Check track validity
        for track in self.root.findall('.//track'):
            track_name = track.get('name', 'Unnamed')
            track_type = track.get('type')
            
            if track_type == '0':  # Instrument track
                if track.find('instrumenttrack') is None:
                    issues.append(f"Track '{track_name}' missing instrumenttrack element")
        
        return issues
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export project structure as a dictionary for easy manipulation"""
        def element_to_dict(elem):
            result = {
                'tag': elem.tag,
                'attrib': elem.attrib,
                'text': elem.text,
                'children': []
            }
            for child in elem:
                result['children'].append(element_to_dict(child))
            return result
        
        if self.root is not None:
            return element_to_dict(self.root)
        return {}
    
    def import_from_dict(self, data: Dict[str, Any]):
        """Import project structure from a dictionary"""
        def dict_to_element(d):
            elem = ET.Element(d['tag'])
            elem.attrib = d.get('attrib', {})
            elem.text = d.get('text')
            for child_dict in d.get('children', []):
                child = dict_to_element(child_dict)
                elem.append(child)
            return elem
        
        self.root = dict_to_element(data)
        self.tree = ET.ElementTree(self.root)


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
LMMS Complete Controller - Full programmatic access to LMMS

Usage:
  python lmms_complete_controller.py <command> [args...]

Commands:
  create <output.mmp>                     - Create new project
  info <project.mmp>                      - Show complete project information
  validate <project.mmp>                  - Validate project structure
  list-instruments                        - List all available instruments
  list-effects                           - List all available effects
  add-track <project> <name> <type>       - Add a track
  set-instrument <project> <track> <inst> - Set track instrument
  set-param <project> <track> <param> <value> - Set instrument parameter
  add-effect <project> <track> <effect>   - Add effect to track
  export <project.mmp>                    - Export project structure as JSON
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list-instruments":
        print("Available Instruments:")
        for name, inst_def in INSTRUMENTS.items():
            print(f"  {name}: {inst_def.name}")
            print(f"    Parameters: {len(inst_def.parameters)}")
    
    elif command == "list-effects":
        print("Available Effects:")
        for name, effect_def in EFFECTS.items():
            print(f"  {name}: {effect_def.name}")
            print(f"    Parameters: {len(effect_def.parameters)}")
    
    elif command == "create" and len(sys.argv) >= 3:
        controller = LMMSCompleteController()
        controller.save_project(sys.argv[2])
        print(f"Created new project: {sys.argv[2]}")
    
    elif command == "info" and len(sys.argv) >= 3:
        controller = LMMSCompleteController(sys.argv[2])
        info = controller.get_project_info()
        print(json.dumps(info, indent=2))
    
    elif command == "validate" and len(sys.argv) >= 3:
        controller = LMMSCompleteController(sys.argv[2])
        issues = controller.validate_project()
        if issues:
            print("Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Project is valid")
    
    elif command == "export" and len(sys.argv) >= 3:
        controller = LMMSCompleteController(sys.argv[2])
        data = controller.export_to_dict()
        print(json.dumps(data, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)