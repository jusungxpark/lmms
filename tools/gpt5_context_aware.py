#!/usr/bin/env python3
"""
Context-Aware GPT-5 Music Interface
Analyzes existing project context before making any changes, similar to Cursor's approach
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_ai_brain import LMMSAIBrain
from lmms_complete_controller import LMMSCompleteController


class ContextAnalysisMode(Enum):
    """Different modes of context analysis"""
    FULL = "full"           # Analyze entire project
    SURROUNDING = "surrounding"  # Analyze surrounding tracks/patterns
    SIMILAR = "similar"     # Find similar elements
    STYLE = "style"         # Analyze musical style
    STRUCTURE = "structure" # Analyze song structure


@dataclass
class ProjectContext:
    """Represents the analyzed context of a project"""
    tempo: int
    key: Optional[str]
    genre: Optional[str]
    tracks: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    effects: List[Dict[str, Any]]
    automation: List[Dict[str, Any]]
    style_characteristics: Dict[str, Any]
    structure: Dict[str, Any]
    suggestions: List[str]


class ContextAnalyzer:
    """Analyzes LMMS project context before making changes"""
    
    def __init__(self):
        self.controller = LMMSCompleteController()
        
    def analyze_project(self, project_file: str = None, mode: ContextAnalysisMode = ContextAnalysisMode.FULL) -> ProjectContext:
        """
        Analyze the current project context
        Similar to how Cursor analyzes surrounding code
        """
        
        if project_file and os.path.exists(project_file):
            tree = ET.parse(project_file)
            root = tree.getroot()
        else:
            # Use current project in controller
            root = self.controller.root
            
        context = ProjectContext(
            tempo=self._get_tempo(root),
            key=self._detect_key(root),
            genre=self._detect_genre(root),
            tracks=self._analyze_tracks(root),
            patterns=self._analyze_patterns(root),
            effects=self._analyze_effects(root),
            automation=self._analyze_automation(root),
            style_characteristics=self._analyze_style(root),
            structure=self._analyze_structure(root),
            suggestions=[]
        )
        
        # Generate context-aware suggestions
        context.suggestions = self._generate_suggestions(context, mode)
        
        return context
    
    def _get_tempo(self, root: ET.Element) -> int:
        """Extract tempo from project"""
        head = root.find('.//head')
        if head is not None:
            return int(head.get('bpm', 140))
        return 140
    
    def _detect_key(self, root: ET.Element) -> Optional[str]:
        """Detect the musical key by analyzing note patterns"""
        all_notes = []
        
        # Collect all notes from patterns
        for pattern in root.findall('.//pattern'):
            for note in pattern.findall('.//note'):
                pitch = int(note.get('key', 0))
                all_notes.append(pitch % 12)  # Reduce to chromatic scale
        
        if not all_notes:
            return None
            
        # Simple key detection based on note frequency
        note_freq = {}
        for note in all_notes:
            note_freq[note] = note_freq.get(note, 0) + 1
            
        # Map to likely keys based on common notes
        key_signatures = {
            'C': [0, 2, 4, 5, 7, 9, 11],  # C major
            'Am': [0, 2, 3, 5, 7, 8, 10],  # A minor
            'G': [0, 2, 4, 6, 7, 9, 11],   # G major
            'Em': [0, 2, 3, 6, 7, 8, 10],  # E minor
            'D': [1, 2, 4, 6, 7, 9, 11],   # D major
            'Bm': [1, 2, 3, 6, 7, 8, 10],  # B minor
        }
        
        # Find best matching key
        best_key = None
        best_score = 0
        
        for key, notes in key_signatures.items():
            score = sum(note_freq.get(n, 0) for n in notes)
            if score > best_score:
                best_score = score
                best_key = key
                
        return best_key
    
    def _detect_genre(self, root: ET.Element) -> Optional[str]:
        """Detect genre based on tempo, instruments, and patterns"""
        tempo = self._get_tempo(root)
        tracks = self._analyze_tracks(root)
        
        # Simple genre detection rules
        if 170 <= tempo <= 180:
            return "dnb"
        elif 140 <= tempo <= 150:
            if any('trap' in str(t).lower() for t in tracks):
                return "trap"
            return "dubstep"
        elif 128 <= tempo <= 135:
            if any('acid' in str(t).lower() or '303' in str(t).lower() for t in tracks):
                return "acid"
            return "techno"
        elif 120 <= tempo <= 128:
            return "house"
        elif tempo < 100:
            return "ambient"
        else:
            return "electronic"
    
    def _analyze_tracks(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Analyze all tracks in the project"""
        tracks = []
        
        for track in root.findall('.//track'):
            track_info = {
                'name': track.get('name', 'Unknown'),
                'type': track.get('type', 'instrument'),
                'muted': track.get('muted', '0') == '1',
                'solo': track.get('solo', '0') == '1',
                'volume': float(track.get('vol', '100')),
                'pan': float(track.get('pan', '0')),
                'instruments': [],
                'effects': [],
                'patterns': []
            }
            
            # Get instrument info
            for inst in track.findall('.//instrument'):
                track_info['instruments'].append(inst.get('name', 'Unknown'))
            
            # Get effect info
            for effect in track.findall('.//effect'):
                track_info['effects'].append(effect.get('name', 'Unknown'))
                
            # Get pattern info
            for pattern in track.findall('.//pattern'):
                track_info['patterns'].append({
                    'name': pattern.get('name', 'Unknown'),
                    'pos': int(pattern.get('pos', 0)),
                    'len': int(pattern.get('len', 192))
                })
            
            tracks.append(track_info)
            
        return tracks
    
    def _analyze_patterns(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Analyze patterns to understand musical content"""
        patterns = []
        
        for pattern in root.findall('.//pattern'):
            notes = pattern.findall('.//note')
            
            if notes:
                pitches = [int(n.get('key', 0)) for n in notes]
                velocities = [int(n.get('vol', 100)) for n in notes]
                
                pattern_info = {
                    'name': pattern.get('name', 'Unknown'),
                    'type': pattern.get('type', 'beat'),
                    'length': int(pattern.get('len', 192)),
                    'note_count': len(notes),
                    'pitch_range': (min(pitches), max(pitches)) if pitches else (0, 0),
                    'avg_velocity': sum(velocities) / len(velocities) if velocities else 0,
                    'density': len(notes) / (int(pattern.get('len', 192)) / 48)  # Notes per bar
                }
                
                patterns.append(pattern_info)
                
        return patterns
    
    def _analyze_effects(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Analyze effects used in the project"""
        effects = []
        
        for effect in root.findall('.//effect'):
            effect_info = {
                'name': effect.get('name', 'Unknown'),
                'wet': float(effect.get('wet', 1.0)),
                'autoquit': effect.get('autoquit', '1') == '1',
                'parameters': {}
            }
            
            # Collect all effect parameters
            for child in effect:
                if child.tag not in ['name', 'wet', 'autoquit']:
                    effect_info['parameters'][child.tag] = child.get('value', child.text)
                    
            effects.append(effect_info)
            
        return effects
    
    def _analyze_automation(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Analyze automation in the project"""
        automation = []
        
        for auto in root.findall('.//automationpattern'):
            auto_info = {
                'name': auto.get('name', 'Unknown'),
                'pos': int(auto.get('pos', 0)),
                'len': int(auto.get('len', 192)),
                'object_id': auto.get('object-id', ''),
                'points': []
            }
            
            # Get automation points
            for point in auto.findall('.//object'):
                auto_info['points'].append({
                    'pos': int(point.get('pos', 0)),
                    'value': float(point.get('value', 0))
                })
                
            automation.append(auto_info)
            
        return automation
    
    def _analyze_style(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze the musical style characteristics"""
        tracks = self._analyze_tracks(root)
        patterns = self._analyze_patterns(root)
        effects = self._analyze_effects(root)
        
        style = {
            'complexity': 'simple',
            'energy': 'medium',
            'mood': 'neutral',
            'production_style': 'clean',
            'arrangement_density': 'medium'
        }
        
        # Complexity based on track count and pattern density
        if len(tracks) > 8:
            style['complexity'] = 'complex'
        elif len(tracks) > 4:
            style['complexity'] = 'moderate'
            
        # Energy based on tempo and note density
        tempo = self._get_tempo(root)
        avg_density = sum(p.get('density', 0) for p in patterns) / len(patterns) if patterns else 0
        
        if tempo > 140 or avg_density > 8:
            style['energy'] = 'high'
        elif tempo < 110 or avg_density < 2:
            style['energy'] = 'low'
            
        # Production style based on effects
        effect_count = len(effects)
        has_distortion = any('dist' in e.get('name', '').lower() for e in effects)
        has_reverb = any('reverb' in e.get('name', '').lower() for e in effects)
        
        if has_distortion and effect_count > 5:
            style['production_style'] = 'heavy'
        elif has_reverb and effect_count > 3:
            style['production_style'] = 'atmospheric'
        elif effect_count < 2:
            style['production_style'] = 'minimal'
            
        return style
    
    def _analyze_structure(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze the song structure (intro, verse, chorus, etc.)"""
        patterns = self._analyze_patterns(root)
        
        structure = {
            'total_bars': 0,
            'sections': [],
            'repetitions': [],
            'variations': []
        }
        
        if patterns:
            # Calculate total length
            max_pos = max(p.get('length', 0) for p in patterns)
            structure['total_bars'] = max_pos // 48
            
            # Identify sections based on pattern positions
            # This is simplified - real analysis would be more complex
            if structure['total_bars'] >= 16:
                structure['sections'] = [
                    {'name': 'intro', 'start': 0, 'end': 4},
                    {'name': 'main', 'start': 4, 'end': 12},
                    {'name': 'outro', 'start': 12, 'end': 16}
                ]
                
        return structure
    
    def _generate_suggestions(self, context: ProjectContext, mode: ContextAnalysisMode) -> List[str]:
        """Generate context-aware suggestions"""
        suggestions = []
        
        # Suggestions based on what's missing or could be improved
        if not context.tracks:
            suggestions.append("Add some tracks to start building your music")
            
        if len(context.tracks) < 3:
            suggestions.append("Consider adding more elements (bass, lead, pads)")
            
        if not context.effects:
            suggestions.append("Add effects to enhance the sound (reverb, delay, compression)")
            
        if context.tempo and context.genre:
            if context.genre == "house" and not any("kick" in t.get('name', '').lower() for t in context.tracks):
                suggestions.append("Add a 4/4 kick pattern for house music")
                
        if context.style_characteristics.get('energy') == 'low' and context.genre in ['techno', 'dnb']:
            suggestions.append("Increase energy with faster hi-hats or more aggressive bass")
            
        if context.style_characteristics.get('production_style') == 'clean':
            suggestions.append("Consider adding compression and saturation for a fuller sound")
            
        return suggestions


class ContextAwareGPT5Interface:
    """
    GPT-5 interface that analyzes context before making changes
    Similar to how Cursor analyzes code context
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.analyzer = ContextAnalyzer()
        self.brain = LMMSAIBrain(api_key)
        self.current_context = None
        
    def process_request_with_context(self, request: str, project_file: str = None) -> Dict[str, Any]:
        """
        Process a request by first analyzing the context
        """
        
        # Step 1: Analyze current context
        print("Analyzing project context...")
        self.current_context = self.analyzer.analyze_project(project_file)
        
        # Step 2: Understand what exists
        context_summary = self._summarize_context(self.current_context)
        print(f"Current context: {context_summary}")
        
        # Step 3: Determine what changes are needed
        changes_needed = self._determine_changes(request, self.current_context)
        print(f"Changes needed: {changes_needed}")
        
        # Step 4: Apply changes intelligently
        result = self._apply_contextual_changes(request, changes_needed, self.current_context)
        
        return result
    
    def _summarize_context(self, context: ProjectContext) -> str:
        """Summarize the current project context"""
        summary_parts = []
        
        if context.tempo:
            summary_parts.append(f"{context.tempo} BPM")
            
        if context.genre:
            summary_parts.append(f"{context.genre} genre")
            
        if context.key:
            summary_parts.append(f"Key: {context.key}")
            
        if context.tracks:
            summary_parts.append(f"{len(context.tracks)} tracks")
            
        if context.effects:
            summary_parts.append(f"{len(context.effects)} effects")
            
        style = context.style_characteristics
        if style:
            summary_parts.append(f"{style.get('energy', 'medium')} energy")
            summary_parts.append(f"{style.get('production_style', 'clean')} production")
            
        return ", ".join(summary_parts) if summary_parts else "Empty project"
    
    def _determine_changes(self, request: str, context: ProjectContext) -> Dict[str, Any]:
        """
        Determine what changes are needed based on request and context
        This is like Cursor's diff preview
        """
        
        changes = {
            'add_tracks': [],
            'modify_tracks': [],
            'add_effects': [],
            'modify_patterns': [],
            'adjust_mix': [],
            'structural_changes': []
        }
        
        request_lower = request.lower()
        
        # Analyze request in context
        if 'add' in request_lower or 'more' in request_lower:
            # Adding to existing project
            if 'bass' in request_lower and not any('bass' in t.get('name', '').lower() for t in context.tracks):
                changes['add_tracks'].append({
                    'name': 'Bass',
                    'type': 'bass',
                    'reason': 'No bass track found, adding as requested'
                })
                
            if 'lead' in request_lower and not any('lead' in t.get('name', '').lower() for t in context.tracks):
                changes['add_tracks'].append({
                    'name': 'Lead',
                    'type': 'lead',
                    'reason': 'No lead track found, adding as requested'
                })
                
        if 'heavier' in request_lower or 'harder' in request_lower:
            # Modify existing to be heavier
            changes['add_effects'].append({
                'effect': 'distortion',
                'target': 'master',
                'reason': 'Making sound heavier as requested'
            })
            
            for track in context.tracks:
                if 'kick' in track.get('name', '').lower():
                    changes['modify_tracks'].append({
                        'track': track['name'],
                        'changes': {'volume': 110, 'punch': 'increase'},
                        'reason': 'Increasing kick punch for heavier sound'
                    })
                    
        if 'faster' in request_lower:
            # Tempo change needed
            current_tempo = context.tempo
            new_tempo = min(current_tempo + 20, 180)
            changes['structural_changes'].append({
                'type': 'tempo',
                'from': current_tempo,
                'to': new_tempo,
                'reason': 'Increasing tempo as requested'
            })
            
        if 'variation' in request_lower or 'different' in request_lower:
            # Add variations to existing patterns
            for pattern in context.patterns[:2]:  # Modify first 2 patterns
                changes['modify_patterns'].append({
                    'pattern': pattern['name'],
                    'modification': 'add_variation',
                    'reason': 'Adding variation as requested'
                })
                
        # Context-aware suggestions
        if not changes['add_tracks'] and not changes['modify_tracks'] and len(context.tracks) < 3:
            # Project is too minimal, suggest additions
            if context.genre == 'techno':
                changes['add_tracks'].append({
                    'name': 'Hats',
                    'type': 'hihat',
                    'reason': 'Adding hi-hats to complement existing techno elements'
                })
                
        return changes
    
    def _apply_contextual_changes(self, request: str, changes: Dict[str, Any], 
                                 context: ProjectContext) -> Dict[str, Any]:
        """
        Apply changes while respecting existing context
        """
        
        result = {
            'request': request,
            'context_before': self._summarize_context(context),
            'changes_applied': [],
            'warnings': [],
            'suggestions': context.suggestions
        }
        
        try:
            # Apply structural changes first
            for change in changes.get('structural_changes', []):
                if change['type'] == 'tempo':
                    self.brain.controller.set_tempo(change['to'])
                    result['changes_applied'].append(f"Changed tempo from {change['from']} to {change['to']} BPM")
                    
            # Add new tracks
            for track_change in changes.get('add_tracks', []):
                self.brain.controller.add_track(track_change['name'])
                result['changes_applied'].append(f"Added {track_change['name']} track: {track_change['reason']}")
                
            # Modify existing tracks
            for track_mod in changes.get('modify_tracks', []):
                track_name = track_mod['track']
                for param, value in track_mod['changes'].items():
                    if param == 'volume':
                        self.brain.controller.set_volume(track_name, value)
                    result['changes_applied'].append(f"Modified {track_name}: {track_mod['reason']}")
                    
            # Add effects
            for effect in changes.get('add_effects', []):
                if effect['target'] == 'master':
                    self.brain.controller.add_mixer_effect(0, effect['effect'])
                else:
                    self.brain.controller.add_effect(effect['target'], effect['effect'])
                result['changes_applied'].append(f"Added {effect['effect']}: {effect['reason']}")
                
            # Save the project
            project_file = self.brain.controller.save_project(f"context_aware_{int(time.time())}.mmp")
            result['project_file'] = project_file
            result['status'] = 'success'
            
            # Generate new context summary
            new_context = self.analyzer.analyze_project(project_file)
            result['context_after'] = self._summarize_context(new_context)
            
            # Warnings if needed
            if len(new_context.tracks) > 10:
                result['warnings'].append("Project has many tracks - consider grouping or buses")
                
            if new_context.style_characteristics.get('complexity') == 'complex':
                result['warnings'].append("Project complexity is high - ensure CPU can handle playback")
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            
        return result
    
    def suggest_next_actions(self) -> List[str]:
        """
        Suggest next actions based on current context
        Like Cursor's code completion suggestions
        """
        
        if not self.current_context:
            return ["Analyze the project first"]
            
        suggestions = []
        
        # Based on what's present/missing
        tracks = self.current_context.tracks
        effects = self.current_context.effects
        
        if len(tracks) < 3:
            suggestions.append("Add more instrument layers for a fuller sound")
            
        if not any('bass' in t.get('name', '').lower() for t in tracks):
            suggestions.append("Add a bass line to provide low-end foundation")
            
        if len(effects) < 2:
            suggestions.append("Add reverb and delay for spatial depth")
            
        if self.current_context.style_characteristics.get('energy') == 'low':
            suggestions.append("Increase energy with faster percussion or aggressive synths")
            
        # Genre-specific suggestions
        if self.current_context.genre == 'techno':
            if not any('acid' in str(t).lower() for t in tracks):
                suggestions.append("Add an acid line for classic techno sound")
                
        elif self.current_context.genre == 'house':
            if not any('pad' in str(t).lower() for t in tracks):
                suggestions.append("Add pads for atmospheric house vibes")
                
        return suggestions[:5]  # Return top 5 suggestions
    
    def preview_changes(self, request: str) -> Dict[str, Any]:
        """
        Preview what changes would be made without applying them
        Like Cursor's diff preview
        """
        
        if not self.current_context:
            self.current_context = self.analyzer.analyze_project()
            
        changes = self._determine_changes(request, self.current_context)
        
        preview = {
            'current_state': self._summarize_context(self.current_context),
            'proposed_changes': changes,
            'impact': self._assess_impact(changes, self.current_context),
            'alternatives': self._suggest_alternatives(request, self.current_context)
        }
        
        return preview
    
    def _assess_impact(self, changes: Dict[str, Any], context: ProjectContext) -> Dict[str, Any]:
        """Assess the impact of proposed changes"""
        
        impact = {
            'complexity_change': 'none',
            'style_change': 'none',
            'mix_balance': 'maintained',
            'risk_level': 'low'
        }
        
        # Assess complexity change
        new_track_count = len(context.tracks) + len(changes.get('add_tracks', []))
        if new_track_count > len(context.tracks) * 1.5:
            impact['complexity_change'] = 'significant increase'
            impact['risk_level'] = 'medium'
            
        # Assess style change
        if changes.get('add_effects'):
            for effect in changes['add_effects']:
                if effect['effect'] in ['distortion', 'bitcrush']:
                    impact['style_change'] = 'heavier/aggressive'
                elif effect['effect'] in ['reverb', 'delay']:
                    impact['style_change'] = 'more spacious'
                    
        return impact
    
    def _suggest_alternatives(self, request: str, context: ProjectContext) -> List[str]:
        """Suggest alternative approaches"""
        
        alternatives = []
        
        if 'heavier' in request.lower():
            alternatives.append("Instead of adding distortion, try layering kicks for natural heaviness")
            alternatives.append("Consider using compression and EQ to achieve weight without distortion")
            
        if 'variation' in request.lower():
            alternatives.append("Add automation to existing elements for dynamic variation")
            alternatives.append("Use filter sweeps and effects automation instead of new patterns")
            
        return alternatives


def main():
    """Demo the context-aware interface"""
    import time
    
    print("Context-Aware GPT-5 Music Interface")
    print("=" * 60)
    
    interface = ContextAwareGPT5Interface()
    
    # Example 1: Start with empty project
    print("\nExample 1: Creating from scratch with context awareness")
    result = interface.process_request_with_context("Create a minimal techno beat")
    print(f"Result: {result.get('status')}")
    if result.get('changes_applied'):
        for change in result['changes_applied']:
            print(f"  - {change}")
    
    # Example 2: Modify existing project
    print("\nExample 2: Adding to existing project")
    if result.get('project_file'):
        result2 = interface.process_request_with_context(
            "Make it heavier with more bass", 
            result['project_file']
        )
        print(f"Result: {result2.get('status')}")
        if result2.get('changes_applied'):
            for change in result2['changes_applied']:
                print(f"  - {change}")
    
    # Example 3: Get suggestions
    print("\nSuggested next actions:")
    suggestions = interface.suggest_next_actions()
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")
    
    # Example 4: Preview changes
    print("\nPreview mode:")
    preview = interface.preview_changes("Add variation and make it more energetic")
    print(f"Current: {preview['current_state']}")
    print(f"Impact: {preview['impact']['complexity_change']} complexity, {preview['impact']['risk_level']} risk")
    
    print("\nContext-aware interface ready.")


if __name__ == "__main__":
    main()