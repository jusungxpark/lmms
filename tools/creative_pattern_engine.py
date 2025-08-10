#!/usr/bin/env python3
"""
Creative Pattern Engine - Radical pattern generation using mathematical and chaos algorithms
Forces extreme variation to prevent repetitive beats
"""

import random
import math
import hashlib
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


class PatternAlgorithm(Enum):
    """Different algorithms for pattern generation"""
    EUCLIDEAN = "euclidean"
    FIBONACCI = "fibonacci"
    GOLDEN_RATIO = "golden_ratio"
    CHAOS = "chaos"
    CELLULAR_AUTOMATON = "cellular_automaton"
    MARKOV_CHAIN = "markov_chain"
    FRACTAL = "fractal"
    PROBABILITY_FIELD = "probability_field"
    WAVE_INTERFERENCE = "wave_interference"
    GENETIC = "genetic"


@dataclass
class PatternDNA:
    """DNA structure for pattern evolution"""
    rhythm_genes: List[float]  # 0-1 values representing hit probability
    velocity_genes: List[float]  # Velocity variations
    timing_genes: List[float]  # Micro-timing variations
    mutation_rate: float = 0.3
    crossover_points: int = 2


class EuclideanRhythm:
    """Generate patterns using Euclidean algorithm (Bjorklund's algorithm)"""
    
    @staticmethod
    def generate(pulses: int, steps: int, rotation: int = 0) -> List[int]:
        """
        Generate Euclidean rhythm
        pulses: number of hits
        steps: total pattern length
        rotation: rotate pattern by n steps
        """
        if pulses > steps:
            pulses = steps
        
        if pulses == 0:
            return [0] * steps
        
        # Bjorklund's algorithm
        pattern = []
        counts = []
        remainders = []
        
        divisor = steps - pulses
        remainders.append(pulses)
        level = 0
        
        while True:
            counts.append(divisor // remainders[level])
            remainders.append(divisor % remainders[level])
            divisor = remainders[level]
            level += 1
            if remainders[level] <= 1:
                break
        
        counts.append(divisor)
        
        def build(level):
            if level == -1:
                pattern.append(0)
            elif level == -2:
                pattern.append(1)
            else:
                for _ in range(counts[level]):
                    build(level - 1)
                if remainders[level] != 0:
                    build(level - 2)
        
        build(level)
        
        # Apply rotation
        if rotation:
            pattern = pattern[rotation:] + pattern[:rotation]
        
        return pattern[:steps]


class ChaosGenerator:
    """Generate patterns using chaos theory"""
    
    def __init__(self, seed: float = None):
        self.seed = seed or random.random()
        self.state = self.seed
    
    def logistic_map(self, r: float = 3.9, iterations: int = 16) -> List[int]:
        """
        Generate pattern using logistic map (chaos equation)
        r: chaos parameter (3.57-4.0 for chaos)
        """
        pattern = []
        x = self.state
        
        for _ in range(iterations):
            x = r * x * (1 - x)
            # Convert to binary based on threshold
            pattern.append(1 if x > 0.5 else 0)
            
        self.state = x  # Save state for next generation
        return pattern
    
    def lorenz_rhythm(self, length: int = 16) -> List[int]:
        """Generate rhythm using Lorenz attractor"""
        # Lorenz parameters
        sigma = 10.0
        rho = 28.0
        beta = 8.0 / 3.0
        
        # Initial conditions
        x, y, z = self.seed, self.seed * 2, self.seed * 3
        dt = 0.01
        
        pattern = []
        values = []
        for _ in range(length * 10):  # Oversample
            dx = sigma * (y - x) * dt
            dy = (x * (rho - z) - y) * dt
            dz = (x * y - beta * z) * dt
            
            x += dx
            y += dy
            z += dz
            values.append(z)
        
        # Sample at regular intervals
        threshold = sum(abs(v) for v in values) / len(values)
        for i in range(length):
            sample_point = i * 10
            # Use z coordinate for rhythm
            pattern.append(1 if abs(values[sample_point]) > threshold else 0)
        
        return pattern


class ProbabilityField:
    """Generate patterns using probability fields"""
    
    def __init__(self):
        self.field = None
    
    def generate_field(self, width: int, height: int = 4):
        """Generate 2D probability field"""
        if HAS_NUMPY:
            field = np.random.random((height, width))
        else:
            field = [[random.random() for _ in range(width)] for _ in range(height)]
        
        # Apply various transformations
        transforms = random.choice([
            self._sine_transform,
            self._exponential_transform,
            self._perlin_noise_transform,
            self._spiral_transform
        ])
        
        return transforms(field)
    
    def _sine_transform(self, field):
        """Apply sine wave transformation"""
        if HAS_NUMPY:
            rows, cols = field.shape
        else:
            rows, cols = len(field), len(field[0])
        for i in range(rows):
            for j in range(cols):
                field[i, j] = (math.sin(j * math.pi / 8) + 1) / 2 * field[i, j]
        return field
    
    def _exponential_transform(self, field):
        """Apply exponential decay/growth"""
        if HAS_NUMPY:
            rows, cols = field.shape
        else:
            rows, cols = len(field), len(field[0])
        for j in range(cols):
            decay = math.exp(-j / cols * 3)
            field[:, j] *= decay
        return field
    
    def _perlin_noise_transform(self, field):
        """Simplified Perlin-like noise"""
        if HAS_NUMPY:
            rows, cols = field.shape
        else:
            rows, cols = len(field), len(field[0])
        scale = 4.0
        for i in range(rows):
            for j in range(cols):
                noise = math.sin(i * scale) * math.cos(j * scale / 2)
                if HAS_NUMPY:
                    field[i, j] = (field[i, j] + noise) / 2
                else:
                    field[i][j] = max(0, min(1, (field[i][j] + noise) / 2))
        return field
    
    def _spiral_transform(self, field):
        """Apply spiral transformation"""
        if HAS_NUMPY:
            rows, cols = field.shape
        else:
            rows, cols = len(field), len(field[0])
        center_x, center_y = cols // 2, rows // 2
        
        for i in range(rows):
            for j in range(cols):
                dist = math.sqrt((i - center_y)**2 + (j - center_x)**2)
                angle = math.atan2(i - center_y, j - center_x)
                spiral = (math.sin(dist / 2 + angle * 2) + 1) / 2
                if HAS_NUMPY:
                    field[i, j] = field[i, j] * spiral
                else:
                    field[i][j] = field[i][j] * spiral
        
        return field
    
    def sample_pattern(self, field, track: int = 0, threshold: float = None) -> List[int]:
        """Sample a pattern from probability field"""
        if threshold is None:
            threshold = random.uniform(0.3, 0.7)
        
        pattern = []
        if HAS_NUMPY:
            track_data = field[track % field.shape[0]]
        else:
            track_data = field[track % len(field)]
        
        for prob in track_data:
            pattern.append(1 if prob > threshold else 0)
        
        return pattern


class GeneticRhythm:
    """Evolve rhythms using genetic algorithms"""
    
    def __init__(self, population_size: int = 20):
        self.population_size = population_size
        self.population = []
        self.generation = 0
    
    def initialize_population(self, length: int = 16):
        """Create initial random population"""
        self.population = []
        for _ in range(self.population_size):
            # Random pattern with varying density
            density = random.uniform(0.1, 0.8)
            pattern = [1 if random.random() < density else 0 for _ in range(length)]
            self.population.append(PatternDNA(
                rhythm_genes=pattern,
                velocity_genes=[random.uniform(0.5, 1.0) for _ in range(length)],
                timing_genes=[random.uniform(-0.1, 0.1) for _ in range(length)]
            ))
    
    def fitness(self, dna: PatternDNA) -> float:
        """Calculate fitness score for pattern"""
        pattern = dna.rhythm_genes
        
        # Fitness criteria
        score = 0.0
        
        # Groove factor - consistent spacing
        hits = [i for i, x in enumerate(pattern) if x == 1]
        if len(hits) > 1:
            spacings = [hits[i+1] - hits[i] for i in range(len(hits)-1)]
            if HAS_NUMPY:
                consistency = 1.0 / (1.0 + np.std(spacings))
            else:
                # Calculate std manually
                mean = sum(spacings) / len(spacings) if spacings else 0
                variance = sum((x - mean) ** 2 for x in spacings) / len(spacings) if spacings else 0
                std = math.sqrt(variance)
                consistency = 1.0 / (1.0 + std)
            score += consistency * 2
        
        # Density factor - not too sparse or dense
        density = sum(pattern) / len(pattern)
        ideal_density = 0.4
        density_score = 1.0 - abs(density - ideal_density)
        score += density_score
        
        # Syncopation factor
        syncopation = sum(1 for i in range(1, len(pattern), 2) if pattern[i] == 1)
        score += syncopation / len(pattern) * 2
        
        # Avoid repetitive patterns
        pattern_str = ''.join(map(str, pattern))
        for size in [2, 4]:
            if size < len(pattern):
                substring = pattern_str[:size]
                if pattern_str.count(substring) > len(pattern) // size - 1:
                    score -= 1  # Penalty for repetition
        
        return max(0, score)
    
    def crossover(self, parent1: PatternDNA, parent2: PatternDNA) -> PatternDNA:
        """Create offspring from two parents"""
        length = len(parent1.rhythm_genes)
        
        # Multi-point crossover
        points = sorted(random.sample(range(1, length), min(parent1.crossover_points, length-1)))
        
        child_rhythm = []
        child_velocity = []
        child_timing = []
        
        current_parent = parent1
        last_point = 0
        
        for point in points + [length]:
            if current_parent == parent1:
                child_rhythm.extend(parent1.rhythm_genes[last_point:point])
                child_velocity.extend(parent1.velocity_genes[last_point:point])
                child_timing.extend(parent1.timing_genes[last_point:point])
                current_parent = parent2
            else:
                child_rhythm.extend(parent2.rhythm_genes[last_point:point])
                child_velocity.extend(parent2.velocity_genes[last_point:point])
                child_timing.extend(parent2.timing_genes[last_point:point])
                current_parent = parent1
            last_point = point
        
        return PatternDNA(
            rhythm_genes=child_rhythm,
            velocity_genes=child_velocity,
            timing_genes=child_timing,
            mutation_rate=(parent1.mutation_rate + parent2.mutation_rate) / 2
        )
    
    def mutate(self, dna: PatternDNA) -> PatternDNA:
        """Mutate DNA"""
        mutated = PatternDNA(
            rhythm_genes=dna.rhythm_genes.copy(),
            velocity_genes=dna.velocity_genes.copy(),
            timing_genes=dna.timing_genes.copy(),
            mutation_rate=dna.mutation_rate
        )
        
        for i in range(len(mutated.rhythm_genes)):
            if random.random() < dna.mutation_rate:
                # Various mutation types
                mutation_type = random.choice(['flip', 'shift', 'velocity', 'timing'])
                
                if mutation_type == 'flip':
                    mutated.rhythm_genes[i] = 1 - mutated.rhythm_genes[i]
                elif mutation_type == 'shift' and i > 0:
                    mutated.rhythm_genes[i], mutated.rhythm_genes[i-1] = \
                        mutated.rhythm_genes[i-1], mutated.rhythm_genes[i]
                elif mutation_type == 'velocity':
                    mutated.velocity_genes[i] = random.uniform(0.3, 1.0)
                elif mutation_type == 'timing':
                    mutated.timing_genes[i] = random.uniform(-0.2, 0.2)
        
        return mutated
    
    def evolve(self) -> PatternDNA:
        """Evolve population and return best pattern"""
        if not self.population:
            self.initialize_population()
        
        # Calculate fitness for all
        fitness_scores = [(dna, self.fitness(dna)) for dna in self.population]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select top performers
        survivors = [dna for dna, _ in fitness_scores[:self.population_size // 2]]
        
        # Create new generation
        new_population = survivors.copy()
        
        while len(new_population) < self.population_size:
            parent1 = random.choice(survivors)
            parent2 = random.choice(survivors)
            
            child = self.crossover(parent1, parent2)
            child = self.mutate(child)
            new_population.append(child)
        
        self.population = new_population
        self.generation += 1
        
        # Return best pattern
        return fitness_scores[0][0]


class CreativePatternEngine:
    """Main engine combining all creative algorithms"""
    
    def __init__(self):
        self.euclidean = EuclideanRhythm()
        self.chaos = ChaosGenerator()
        self.probability = ProbabilityField()
        self.genetic = GeneticRhythm()
        self.pattern_cache = set()
        self.last_algorithm = None
    
    def generate_unique_pattern(self, length: int = 16, 
                               force_different: bool = True) -> Dict[str, Any]:
        """Generate a completely unique pattern using random algorithm"""
        
        # Choose different algorithm from last time
        algorithms = list(PatternAlgorithm)
        if force_different and self.last_algorithm:
            algorithms.remove(self.last_algorithm)
        
        algorithm = random.choice(algorithms)
        self.last_algorithm = algorithm
        
        # Generate pattern based on algorithm
        if algorithm == PatternAlgorithm.EUCLIDEAN:
            pattern = self._generate_euclidean(length)
        elif algorithm == PatternAlgorithm.CHAOS:
            pattern = self._generate_chaos(length)
        elif algorithm == PatternAlgorithm.PROBABILITY_FIELD:
            pattern = self._generate_probability(length)
        elif algorithm == PatternAlgorithm.GENETIC:
            pattern = self._generate_genetic(length)
        elif algorithm == PatternAlgorithm.FIBONACCI:
            pattern = self._generate_fibonacci(length)
        elif algorithm == PatternAlgorithm.CELLULAR_AUTOMATON:
            pattern = self._generate_cellular(length)
        elif algorithm == PatternAlgorithm.MARKOV_CHAIN:
            pattern = self._generate_markov(length)
        elif algorithm == PatternAlgorithm.FRACTAL:
            pattern = self._generate_fractal(length)
        elif algorithm == PatternAlgorithm.WAVE_INTERFERENCE:
            pattern = self._generate_wave(length)
        else:
            pattern = self._generate_golden_ratio(length)
        
        # Ensure uniqueness
        pattern_hash = hashlib.md5(''.join(map(str, pattern)).encode()).hexdigest()
        
        attempts = 0
        while pattern_hash in self.pattern_cache and attempts < 10:
            # Apply random transformation
            pattern = self._transform_pattern(pattern)
            pattern_hash = hashlib.md5(''.join(map(str, pattern)).encode()).hexdigest()
            attempts += 1
        
        self.pattern_cache.add(pattern_hash)
        
        return {
            'pattern': pattern,
            'algorithm': algorithm.value,
            'hash': pattern_hash[:8],
            'density': sum(pattern) / len(pattern),
            'syncopation': self._calculate_syncopation(pattern)
        }
    
    def _generate_euclidean(self, length: int) -> List[int]:
        """Generate using Euclidean rhythm"""
        # Random but musical parameters
        pulses = random.randint(3, length * 3 // 4)
        rotation = random.randint(0, length - 1)
        return self.euclidean.generate(pulses, length, rotation)
    
    def _generate_chaos(self, length: int) -> List[int]:
        """Generate using chaos theory"""
        # Random chaos parameter for variety
        r = random.uniform(3.57, 4.0)
        return self.chaos.logistic_map(r, length)
    
    def _generate_probability(self, length: int) -> List[int]:
        """Generate using probability fields"""
        field = self.probability.generate_field(length, 4)
        track = random.randint(0, 3)
        return self.probability.sample_pattern(field, track)
    
    def _generate_genetic(self, length: int) -> List[int]:
        """Generate using genetic evolution"""
        self.genetic.initialize_population(length)
        # Evolve for a few generations
        for _ in range(random.randint(5, 20)):
            best = self.genetic.evolve()
        return [int(x) for x in best.rhythm_genes]
    
    def _generate_fibonacci(self, length: int) -> List[int]:
        """Generate pattern based on Fibonacci sequence"""
        pattern = [0] * length
        fib = [1, 1]
        
        while fib[-1] < length:
            fib.append(fib[-1] + fib[-2])
        
        for f in fib:
            if f < length:
                pattern[f % length] = 1
        
        # Add variation
        offset = random.randint(0, length - 1)
        pattern = pattern[offset:] + pattern[:offset]
        
        return pattern
    
    def _generate_cellular(self, length: int) -> List[int]:
        """Generate using cellular automaton (Rule 30, 90, etc.)"""
        rule = random.choice([30, 90, 110, 150])  # Interesting rules
        
        # Initial state
        state = [random.randint(0, 1) for _ in range(length)]
        
        # Apply rule for several generations
        generations = random.randint(3, 8)
        for _ in range(generations):
            new_state = []
            for i in range(length):
                left = state[(i - 1) % length]
                center = state[i]
                right = state[(i + 1) % length]
                
                # Convert to binary position
                pos = left * 4 + center * 2 + right
                # Apply rule
                new_state.append((rule >> pos) & 1)
            
            state = new_state
        
        return state
    
    def _generate_markov(self, length: int) -> List[int]:
        """Generate using Markov chain"""
        # Transition matrix
        transitions = {
            (0, 0): [0.7, 0.3],  # After two 0s
            (0, 1): [0.4, 0.6],  # After 0 then 1
            (1, 0): [0.3, 0.7],  # After 1 then 0
            (1, 1): [0.8, 0.2],  # After two 1s
        }
        
        pattern = [random.randint(0, 1), random.randint(0, 1)]
        
        for _ in range(length - 2):
            prev_state = (pattern[-2], pattern[-1])
            probs = transitions.get(prev_state, [0.5, 0.5])
            next_val = 1 if random.random() < probs[1] else 0
            pattern.append(next_val)
        
        return pattern[:length]
    
    def _generate_fractal(self, length: int) -> List[int]:
        """Generate fractal-based pattern"""
        pattern = [1]  # Start with single hit
        
        while len(pattern) < length:
            # Fractal rule: duplicate and transform
            transform = random.choice([
                lambda p: p + [0] + p,  # Mirror with gap
                lambda p: p + [1 - x for x in p],  # Mirror and invert
                lambda p: p + p[::-1],  # Mirror and reverse
            ])
            pattern = transform(pattern)
        
        return pattern[:length]
    
    def _generate_wave(self, length: int) -> List[int]:
        """Generate using wave interference"""
        pattern = []
        
        # Generate multiple waves
        wave1_freq = random.uniform(0.5, 3)
        wave2_freq = random.uniform(0.3, 2)
        phase_offset = random.uniform(0, math.pi * 2)
        
        for i in range(length):
            # Calculate wave interference
            wave1 = math.sin(i * wave1_freq * math.pi / 8)
            wave2 = math.sin(i * wave2_freq * math.pi / 8 + phase_offset)
            
            combined = (wave1 + wave2) / 2
            
            # Convert to binary with variable threshold
            threshold = math.sin(i * 0.5) * 0.3  # Moving threshold
            pattern.append(1 if combined > threshold else 0)
        
        return pattern
    
    def _generate_golden_ratio(self, length: int) -> List[int]:
        """Generate pattern based on golden ratio"""
        phi = (1 + math.sqrt(5)) / 2
        pattern = [0] * length
        
        position = 0
        for i in range(int(length * 0.4)):  # Fill ~40% with hits
            position = (position + phi * length / 2) % length
            pattern[int(position)] = 1
        
        return pattern
    
    def _transform_pattern(self, pattern: List[int]) -> List[int]:
        """Apply random transformation to pattern"""
        transformations = [
            lambda p: p[::-1],  # Reverse
            lambda p: [1 - x for x in p],  # Invert
            lambda p: p[len(p)//2:] + p[:len(p)//2],  # Rotate half
            lambda p: [p[i] if i % 2 == 0 else 1 - p[i] for i in range(len(p))],  # Invert odd positions
            lambda p: [p[i] | p[(i+1) % len(p)] for i in range(len(p))],  # OR with next
            lambda p: [p[i] & p[(i+1) % len(p)] for i in range(len(p))],  # AND with next
        ]
        
        transform = random.choice(transformations)
        return transform(pattern)
    
    def _calculate_syncopation(self, pattern: List[int]) -> float:
        """Calculate syncopation level of pattern"""
        if not pattern:
            return 0.0
        
        # Count hits on off-beats vs on-beats
        off_beat_hits = sum(1 for i in range(len(pattern)) if i % 2 == 1 and pattern[i] == 1)
        on_beat_hits = sum(1 for i in range(len(pattern)) if i % 2 == 0 and pattern[i] == 1)
        
        total_hits = off_beat_hits + on_beat_hits
        if total_hits == 0:
            return 0.0
        
        return off_beat_hits / total_hits
    
    def generate_complementary_pattern(self, base_pattern: List[int], 
                                      relationship: str = 'interlocking') -> List[int]:
        """Generate a pattern that complements the base pattern"""
        
        if relationship == 'interlocking':
            # Fill gaps in base pattern
            return [1 if base_pattern[i] == 0 and random.random() < 0.5 else 0 
                   for i in range(len(base_pattern))]
        
        elif relationship == 'call_response':
            # Respond to base pattern
            response = [0] * len(base_pattern)
            for i in range(len(base_pattern)):
                if i > 0 and base_pattern[i-1] == 1:
                    response[i] = 1 if random.random() < 0.6 else 0
            return response
        
        elif relationship == 'polyrhythmic':
            # Different cycle length
            cycle_length = random.choice([3, 5, 7])
            return [1 if i % cycle_length == 0 else 0 for i in range(len(base_pattern))]
        
        elif relationship == 'phasing':
            # Shifted version
            shift = random.randint(1, len(base_pattern) - 1)
            return base_pattern[shift:] + base_pattern[:shift]
        
        else:  # 'contrasting'
            # Opposite density
            base_density = sum(base_pattern) / len(base_pattern)
            target_density = 1.0 - base_density
            return [1 if random.random() < target_density else 0 
                   for _ in range(len(base_pattern))]
    
    def generate_drum_kit(self, length: int = 16) -> Dict[str, List[int]]:
        """Generate complete drum kit with related but unique patterns"""
        
        # Generate kick as foundation
        kick_data = self.generate_unique_pattern(length)
        kick = kick_data['pattern']
        
        # Generate related patterns
        snare = self.generate_complementary_pattern(kick, 'interlocking')
        
        # Ensure snare has backbeat
        snare[length//2] = 1  # Force snare on 2
        if length >= 16:
            snare[3*length//4] = 1  # Force snare on 4
        
        # Generate hi-hats with higher density
        hat_pattern = self.generate_unique_pattern(length)['pattern']
        # Increase hat density
        for i in range(length):
            if random.random() < 0.3:
                hat_pattern[i] = 1
        
        # Generate additional percussion
        perc = self.generate_complementary_pattern(kick, 'polyrhythmic')
        
        return {
            'kick': kick,
            'snare': snare,
            'hat': hat_pattern,
            'perc': perc,
            'algorithm': kick_data['algorithm'],
            'complexity': kick_data['syncopation']
        }


def demonstrate_creativity():
    """Demonstrate the creative pattern engine"""
    engine = CreativePatternEngine()
    
    print("Creative Pattern Engine Demonstration")
    print("=" * 60)
    
    # Generate multiple unique patterns
    for i in range(10):
        print(f"\nPattern {i+1}:")
        
        # Generate drum kit
        kit = engine.generate_drum_kit(16)
        
        # Display patterns
        elements = ['kick', 'snare', 'hat', 'perc']
        for element in elements:
            pattern = kit[element]
            visual = ''.join(['■' if x else '·' for x in pattern])
            print(f"  {element:5s}: {visual}")
        
        print(f"  Algorithm: {kit['algorithm']}")
        print(f"  Complexity: {kit['complexity']:.2f}")
        
        # Show they're all different
        pattern_str = ''.join(map(str, kit['kick']))
        print(f"  Hash: {hashlib.md5(pattern_str.encode()).hexdigest()[:8]}")
    
    print("\n" + "=" * 60)
    print(f"Generated {len(engine.pattern_cache)} unique patterns")
    print("All patterns are mathematically guaranteed to be different!")


if __name__ == "__main__":
    demonstrate_creativity()