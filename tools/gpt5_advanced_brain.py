#!/usr/bin/env python3
"""
GPT-5 Advanced Brain - Multi-mode AI system for intelligent music creation
Prevents repetitive patterns and provides deep creative analysis
"""

import os
import sys
import json
import time
import hashlib
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime

# Import base components
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_ai_brain import LMMSAIBrain, MusicalIntent, ProductionPlan
from lmms_complete_controller import LMMSCompleteController

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class GPTMode(Enum):
    """Different GPT-5 operation modes for various tasks"""
    FAST = "gpt-5-fast"              # Quick responses, basic patterns
    BALANCED = "gpt-5"                # Standard mode, good quality
    DEEP_THINKING = "gpt-5-deep"      # Complex analysis, creative solutions
    RESEARCH = "gpt-5-research"       # Deep style analysis, learns from references
    CREATIVE = "gpt-5-creative"       # Maximum creativity, experimental
    ANALYTICAL = "gpt-5-analytical"   # Technical analysis mode


@dataclass
class CreativeMemory:
    """Stores previous creations to avoid repetition"""
    pattern_history: deque = field(default_factory=lambda: deque(maxlen=100))
    used_progressions: deque = field(default_factory=lambda: deque(maxlen=50))
    style_combinations: deque = field(default_factory=lambda: deque(maxlen=50))
    rhythm_hashes: set = field(default_factory=set)
    melody_hashes: set = field(default_factory=set)
    last_tempo: Optional[int] = None
    last_key: Optional[str] = None
    last_genre: Optional[str] = None
    creation_count: int = 0
    variation_seeds: List[int] = field(default_factory=list)
    
    def is_too_similar(self, pattern_hash: str, threshold: float = 0.8) -> bool:
        """Check if pattern is too similar to recent ones"""
        # Check exact matches in recent history
        recent = list(self.pattern_history)[-20:]
        if pattern_hash in recent:
            return True
        
        # Check similarity score (simplified)
        for prev_hash in recent[-10:]:
            if self._calculate_similarity(pattern_hash, prev_hash) > threshold:
                return True
        
        return False
    
    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes (simplified)"""
        # In real implementation, this would compare actual patterns
        matching = sum(1 for a, b in zip(hash1, hash2) if a == b)
        return matching / max(len(hash1), len(hash2))
    
    def add_creation(self, pattern_hash: str, tempo: int, key: str, genre: str):
        """Add a new creation to memory"""
        self.pattern_history.append(pattern_hash)
        self.last_tempo = tempo
        self.last_key = key
        self.last_genre = genre
        self.creation_count += 1
        
        # Generate new variation seed
        seed = int(hashlib.md5(f"{pattern_hash}{self.creation_count}".encode()).hexdigest()[:8], 16)
        self.variation_seeds.append(seed)
    
    def get_variation_multiplier(self) -> float:
        """Get a multiplier to increase variation over time"""
        # More variations as we create more to avoid repetition
        return 1.0 + (self.creation_count * 0.1)


class PatternGenerator:
    """Advanced pattern generation with anti-repetition algorithms"""
    
    def __init__(self, memory: CreativeMemory):
        self.memory = memory
        self.mutation_rate = 0.1
        
    def generate_unique_rhythm(self, genre: str, element: str, length: int = 16) -> List[int]:
        """Generate a unique rhythm pattern"""
        
        # Start with a base pattern
        base = self._get_base_pattern(genre, element)
        
        # Apply mutations until unique
        attempts = 0
        while attempts < 50:
            pattern = self._mutate_pattern(base, self.mutation_rate * self.memory.get_variation_multiplier())
            pattern_hash = self._hash_pattern(pattern)
            
            if pattern_hash not in self.memory.rhythm_hashes:
                self.memory.rhythm_hashes.add(pattern_hash)
                return pattern
            
            attempts += 1
            self.mutation_rate += 0.02  # Increase mutation rate with each attempt
        
        # If all else fails, generate completely random pattern
        return self._generate_random_pattern(length, genre, element)
    
    def _get_base_pattern(self, genre: str, element: str) -> List[int]:
        """Get base pattern for genre and element"""
        patterns = {
            'house': {
                'kick': [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
                'snare': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
                'hat': [0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0]
            },
            'techno': {
                'kick': [1,0,0,1,1,0,0,0,1,0,0,1,1,0,0,0],
                'snare': [0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,1],
                'hat': [1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1]
            },
            'dnb': {
                'kick': [1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
                'snare': [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
                'hat': [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
            },
            'dubstep': {
                'kick': [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
                'snare': [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
                'hat': [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            }
        }
        
        genre_patterns = patterns.get(genre.lower(), patterns['house'])
        return genre_patterns.get(element, [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0])
    
    def _mutate_pattern(self, pattern: List[int], rate: float) -> List[int]:
        """Mutate pattern with given rate"""
        mutated = pattern.copy()
        
        for i in range(len(mutated)):
            if random.random() < rate:
                # Different mutation strategies
                strategy = random.choice(['flip', 'shift', 'double', 'remove'])
                
                if strategy == 'flip':
                    mutated[i] = 1 - mutated[i]
                elif strategy == 'shift' and i > 0:
                    mutated[i], mutated[i-1] = mutated[i-1], mutated[i]
                elif strategy == 'double' and i < len(mutated) - 1:
                    mutated[i+1] = mutated[i]
                elif strategy == 'remove':
                    mutated[i] = 0
        
        # Ensure pattern isn't empty
        if sum(mutated) == 0:
            mutated[0] = 1  # At least one hit
        
        return mutated
    
    def _generate_random_pattern(self, length: int, genre: str, element: str) -> List[int]:
        """Generate completely random pattern based on genre characteristics"""
        density = self._get_density(genre, element)
        pattern = []
        
        for i in range(length):
            if element == 'kick' and i % 4 == 0:
                # Higher probability on downbeats for kicks
                pattern.append(1 if random.random() < density * 1.5 else 0)
            else:
                pattern.append(1 if random.random() < density else 0)
        
        return pattern
    
    def _get_density(self, genre: str, element: str) -> float:
        """Get hit density for genre and element"""
        densities = {
            'house': {'kick': 0.25, 'snare': 0.125, 'hat': 0.25},
            'techno': {'kick': 0.3, 'snare': 0.15, 'hat': 0.5},
            'dnb': {'kick': 0.2, 'snare': 0.125, 'hat': 0.7},
            'dubstep': {'kick': 0.125, 'snare': 0.0625, 'hat': 0.1},
            'trap': {'kick': 0.15, 'snare': 0.1, 'hat': 0.6}
        }
        
        genre_density = densities.get(genre.lower(), densities['house'])
        return genre_density.get(element, 0.25)
    
    def _hash_pattern(self, pattern: List[int]) -> str:
        """Create hash of pattern"""
        return hashlib.md5(''.join(map(str, pattern)).encode()).hexdigest()[:16]


class GPT5AdvancedBrain(LMMSAIBrain):
    """
    Advanced AI Brain with multiple GPT-5 modes and anti-repetition
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.memory = CreativeMemory()
        self.pattern_generator = PatternGenerator(self.memory)
        self.current_mode = GPTMode.BALANCED
        
    def set_mode(self, mode: GPTMode):
        """Set the GPT mode for processing"""
        self.current_mode = mode
        print(f"GPT Mode set to: {mode.value}")
    
    def interpret_request(self, request: str) -> MusicalIntent:
        """
        Enhanced request interpretation with mode-specific processing
        """
        # Determine best mode based on request complexity
        mode = self._determine_mode(request)
        self.set_mode(mode)
        
        if not self.api_key:
            return self._enhanced_creative_interpretation(request)
        
        # Mode-specific prompts
        prompt = self._get_mode_specific_prompt(request, mode)
        
        try:
            # Use appropriate model and parameters for mode
            model_config = self._get_model_config(mode)
            
            response = openai.ChatCompletion.create(
                model=model_config['model'],
                messages=[
                    {"role": "system", "content": self._get_system_message(mode)},
                    {"role": "user", "content": prompt}
                ],
                temperature=model_config['temperature'],
                max_tokens=model_config['max_tokens'],
                presence_penalty=model_config['presence_penalty'],
                frequency_penalty=model_config['frequency_penalty']
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            
            # Create intent with variations
            intent = self._create_varied_intent(intent_data)
            
            return intent
            
        except Exception as e:
            print(f"GPT interpretation failed: {e}, using creative fallback")
            return self._enhanced_creative_interpretation(request)
    
    def _determine_mode(self, request: str) -> GPTMode:
        """Determine best GPT mode based on request"""
        request_lower = request.lower()
        
        # Keywords for different modes
        if any(word in request_lower for word in ['quick', 'simple', 'fast', 'basic']):
            return GPTMode.FAST
        elif any(word in request_lower for word in ['like', 'style of', 'similar to', 'inspired by']):
            return GPTMode.RESEARCH
        elif any(word in request_lower for word in ['experimental', 'unique', 'creative', 'unusual']):
            return GPTMode.CREATIVE
        elif any(word in request_lower for word in ['analyze', 'technical', 'detailed', 'specific']):
            return GPTMode.ANALYTICAL
        elif any(word in request_lower for word in ['complex', 'intricate', 'sophisticated']):
            return GPTMode.DEEP_THINKING
        else:
            return GPTMode.BALANCED
    
    def _get_model_config(self, mode: GPTMode) -> Dict[str, Any]:
        """Get model configuration for mode"""
        configs = {
            GPTMode.FAST: {
                'model': 'gpt-3.5-turbo',  # Simulated GPT-5 fast
                'temperature': 0.3,
                'max_tokens': 500,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            GPTMode.BALANCED: {
                'model': 'gpt-4',  # Simulated GPT-5 balanced
                'temperature': 0.7,
                'max_tokens': 1500,
                'presence_penalty': 0.3,
                'frequency_penalty': 0.3
            },
            GPTMode.DEEP_THINKING: {
                'model': 'gpt-4-turbo-preview',  # Simulated GPT-5 deep
                'temperature': 0.6,
                'max_tokens': 3000,
                'presence_penalty': 0.5,
                'frequency_penalty': 0.5
            },
            GPTMode.RESEARCH: {
                'model': 'gpt-4-turbo-preview',  # Simulated GPT-5 research
                'temperature': 0.4,
                'max_tokens': 4000,
                'presence_penalty': 0.2,
                'frequency_penalty': 0.4
            },
            GPTMode.CREATIVE: {
                'model': 'gpt-4',  # Simulated GPT-5 creative
                'temperature': 0.9,
                'max_tokens': 2000,
                'presence_penalty': 0.7,
                'frequency_penalty': 0.7
            },
            GPTMode.ANALYTICAL: {
                'model': 'gpt-4',  # Simulated GPT-5 analytical
                'temperature': 0.2,
                'max_tokens': 2500,
                'presence_penalty': 0.1,
                'frequency_penalty': 0.1
            }
        }
        
        return configs.get(mode, configs[GPTMode.BALANCED])
    
    def _get_system_message(self, mode: GPTMode) -> str:
        """Get system message for mode"""
        messages = {
            GPTMode.FAST: "You are a quick music assistant. Provide fast, practical solutions.",
            
            GPTMode.BALANCED: """You are an expert music producer. Balance creativity with technical accuracy.
            Focus on creating unique patterns that don't repeat previous creations.""",
            
            GPTMode.DEEP_THINKING: """You are a master music producer and theorist. Think deeply about:
            - The emotional impact of each musical choice
            - How different elements interact harmonically and rhythmically
            - Creating completely unique patterns and progressions
            - Avoiding any repetition from previous works""",
            
            GPTMode.RESEARCH: """You are a music research AI that deeply analyzes artist styles.
            Extract the DNA of the requested style including:
            - Signature rhythm patterns and groove
            - Unique production techniques
            - Harmonic and melodic tendencies
            - Mix and mastering approach
            Create variations that capture the essence while being original.""",
            
            GPTMode.CREATIVE: """You are an experimental music AI. Your goal is to:
            - Create never-before-heard patterns and combinations
            - Push boundaries while maintaining musicality
            - Combine unexpected elements that work together
            - Generate multiple wildly different variations""",
            
            GPTMode.ANALYTICAL: """You are a technical music analysis AI. Focus on:
            - Precise technical specifications
            - Frequency analysis and sonic characteristics
            - Detailed production chain recommendations
            - Mathematical relationships in rhythm and harmony"""
        }
        
        return messages.get(mode, messages[GPTMode.BALANCED])
    
    def _get_mode_specific_prompt(self, request: str, mode: GPTMode) -> str:
        """Generate mode-specific prompt"""
        
        # Add memory context
        memory_context = f"""
        Previous creations to AVOID repeating:
        - Last tempo: {self.memory.last_tempo}
        - Last key: {self.memory.last_key}
        - Last genre: {self.memory.last_genre}
        - Patterns used: {len(self.memory.pattern_history)} unique patterns
        - Creation number: {self.memory.creation_count + 1}
        
        IMPORTANT: Generate completely NEW and DIFFERENT patterns!
        """
        
        if mode == GPTMode.RESEARCH:
            return f"""
            Deep style research for: "{request}"
            
            {memory_context}
            
            Analyze and extract:
            1. Rhythm DNA (specific patterns, not generic)
            2. Harmonic DNA (exact progressions and voicings)
            3. Production DNA (specific techniques and effects)
            4. Signature elements that define this style
            5. Generate 5 DIFFERENT variations that capture the essence
            
            Return JSON with detailed analysis and multiple unique options.
            """
        
        elif mode == GPTMode.CREATIVE:
            return f"""
            Maximum creativity for: "{request}"
            
            {memory_context}
            
            Generate something completely unique:
            1. Invent NEW rhythm patterns (not standard patterns)
            2. Create unexpected harmonic progressions
            3. Combine {random.choice(['organic', 'digital', 'found'])} with {random.choice(['synthetic', 'acoustic', 'processed'])} sounds
            4. Generate {random.randint(5, 8)} wildly different variations
            
            Randomization seed: {random.randint(1000, 9999)}
            
            Return JSON with multiple innovative options.
            """
        
        elif mode == GPTMode.DEEP_THINKING:
            return f"""
            Deep analysis for: "{request}"
            
            {memory_context}
            
            Consider deeply:
            1. Emotional journey and dynamics
            2. Tension and release patterns
            3. Frequency spectrum utilization
            4. Groove and pocket placement
            5. Generate {random.randint(4, 6)} sophisticated variations
            
            Each variation must be significantly different from others.
            
            Return comprehensive JSON with detailed variations.
            """
        
        else:
            # Default prompt with anti-repetition emphasis
            return f"""
            Analyze: "{request}"
            
            {memory_context}
            
            Create unique music with:
            - Fresh patterns different from the last {self.memory.creation_count} creations
            - Varied tempo (avoid {self.memory.last_tempo} BPM if recently used)
            - Different key from {self.memory.last_key}
            - Multiple creative variations
            
            Return JSON with musical intent and variations.
            """
    
    def _create_varied_intent(self, intent_data: Dict[str, Any]) -> MusicalIntent:
        """Create intent with built-in variations"""
        
        intent = MusicalIntent(
            genre=intent_data.get("genre"),
            mood=intent_data.get("mood"),
            energy_level=intent_data.get("energy_level", 0.5),
            complexity=intent_data.get("complexity", 0.5),
            tempo=self._vary_tempo(intent_data.get("tempo")),
            key=self._vary_key(intent_data.get("key")),
            time_signature=tuple(intent_data["time_signature"]) if intent_data.get("time_signature") else None,
            elements=intent_data.get("elements", []),
            effects_intensity=intent_data.get("effects_intensity", 0.5),
            characteristics=intent_data.get("characteristics", []),
            duration_bars=intent_data.get("duration_bars", 8),
            specific_requirements=intent_data.get("specific_requirements", {})
        )
        
        # Add variation instructions
        intent.specific_requirements['variation_level'] = self.memory.get_variation_multiplier()
        intent.specific_requirements['avoid_patterns'] = list(self.memory.pattern_history)[-5:]
        
        return intent
    
    def _vary_tempo(self, base_tempo: Optional[int]) -> Optional[int]:
        """Vary tempo to avoid repetition"""
        if not base_tempo:
            return None
        
        if base_tempo == self.memory.last_tempo:
            # Vary by 5-10 BPM
            variation = random.randint(5, 10) * random.choice([-1, 1])
            return max(60, min(200, base_tempo + variation))
        
        return base_tempo
    
    def _vary_key(self, base_key: Optional[str]) -> Optional[str]:
        """Vary key to avoid repetition"""
        if not base_key:
            return None
        
        if base_key == self.memory.last_key:
            # Choose a related but different key
            keys = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
            modifiers = ['', 'm', 'maj7', 'm7']
            
            new_key = random.choice(keys)
            new_modifier = random.choice(modifiers)
            
            return f"{new_key}{new_modifier}"
        
        return base_key
    
    def _enhanced_creative_interpretation(self, request: str) -> MusicalIntent:
        """Enhanced fallback with maximum creativity"""
        
        # Use pattern generator for unique patterns
        intent = super()._enhanced_rule_based_interpretation(request)
        
        # Add creative variations
        intent.specific_requirements = intent.specific_requirements or {}
        intent.specific_requirements['unique_patterns'] = True
        intent.specific_requirements['variation_seed'] = random.randint(1000, 9999)
        
        # Vary from previous creations
        if intent.tempo == self.memory.last_tempo:
            intent.tempo = random.randint(70, 170)
        
        if intent.key == self.memory.last_key:
            keys = ['C minor', 'D minor', 'E minor', 'F minor', 'G minor', 'A minor', 'B minor']
            intent.key = random.choice([k for k in keys if k != self.memory.last_key])
        
        return intent
    
    def generate_production_plan(self, intent: MusicalIntent) -> ProductionPlan:
        """Generate production plan with unique patterns"""
        
        # Set mode for plan generation
        if hasattr(intent, 'specific_requirements') and 'style_reference' in intent.specific_requirements:
            self.set_mode(GPTMode.RESEARCH)
        elif intent.complexity > 0.7:
            self.set_mode(GPTMode.DEEP_THINKING)
        else:
            self.set_mode(GPTMode.BALANCED)
        
        # Generate base plan
        plan = super().generate_production_plan(intent)
        
        # Replace patterns with unique ones
        for pattern in plan.patterns:
            element = pattern['track'].lower()
            
            # Generate unique rhythm
            unique_rhythm = self.pattern_generator.generate_unique_rhythm(
                intent.genre or 'house',
                element,
                16
            )
            
            # Convert to note pattern
            new_notes = []
            for i, hit in enumerate(unique_rhythm):
                if hit:
                    new_notes.append({
                        'pitch': self._get_pitch_for_element(element),
                        'position': i * 3,
                        'length': 3,
                        'velocity': 80 + random.randint(-20, 20)
                    })
            
            pattern['notes'] = new_notes
            pattern['unique_hash'] = self.pattern_generator._hash_pattern(unique_rhythm)
        
        # Update memory
        plan_hash = hashlib.md5(str(plan).encode()).hexdigest()[:16]
        self.memory.add_creation(
            plan_hash,
            intent.tempo or 120,
            intent.key or 'C',
            intent.genre or 'house'
        )
        
        return plan
    
    def _get_pitch_for_element(self, element: str) -> int:
        """Get MIDI pitch for element type"""
        pitches = {
            'kick': 36,
            'snare': 38,
            'hat': 42,
            'hihat': 42,
            'clap': 39,
            'bass': 36,
            'lead': 60,
            'pad': 48
        }
        
        for key, pitch in pitches.items():
            if key in element.lower():
                return pitch
        
        return 60  # Default middle C


def main():
    """Test the advanced GPT-5 brain"""
    
    brain = GPT5AdvancedBrain()
    
    test_requests = [
        "Create a beat like Daft Punk",
        "Make heavy techno with distortion",
        "Create a beat like Daft Punk",  # Test repetition avoidance
        "Quick house loop",
        "Experimental ambient soundscape"
    ]
    
    print("Testing GPT-5 Advanced Brain with Anti-Repetition")
    print("=" * 60)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\nRequest {i}: {request}")
        print("-" * 40)
        
        # Process request
        project_file = brain.create_music(request)
        
        print(f"Created: {project_file}")
        print(f"Mode used: {brain.current_mode.value}")
        print(f"Memory: {brain.memory.creation_count} creations")
        print(f"Unique patterns: {len(brain.memory.rhythm_hashes)}")
        
        # Show that patterns are different
        if brain.memory.pattern_history:
            recent = list(brain.memory.pattern_history)[-3:]
            print(f"Recent pattern hashes: {recent}")
        
        time.sleep(0.5)  # Small delay between creations
    
    print("\n" + "=" * 60)
    print("Test complete! All patterns should be unique.")
    print(f"Total unique rhythms generated: {len(brain.memory.rhythm_hashes)}")


if __name__ == "__main__":
    main()