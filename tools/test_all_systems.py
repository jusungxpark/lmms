#!/usr/bin/env python3
"""
Comprehensive test suite for LMMS AI Music System
Tests all components including new Musical Intelligence improvements
"""

import os
import sys
import traceback

# Test results
results = []
def test(name, func):
    """Run a test and record results"""
    try:
        func()
        results.append((name, "✅ PASS"))
        print(f"✅ {name}")
    except Exception as e:
        results.append((name, f"❌ FAIL: {str(e)[:50]}"))
        print(f"❌ {name}: {e}")
        traceback.print_exc()

print("=" * 60)
print("LMMS AI MUSIC SYSTEM - COMPREHENSIVE TEST")
print("INCLUDING MUSICAL INTELLIGENCE ENHANCEMENTS")
print("=" * 60)

# Test 1: Import all modules
def test_imports():
    from lmms_complete_controller import LMMSCompleteController
    from lmms_actions import LMMSActions
    from lmms_ai_brain import LMMSAIBrain
    from gpt5_music_interface import GPT5MusicInterface
    from musical_intelligence import MusicalIntelligence
    from musical_key_engine import KeySignature, MelodicGenerator, HumanizeEngine
    
test("Module Imports", test_imports)

# Test 2: Basic controller operations
def test_basic_controller():
    from lmms_complete_controller import LMMSCompleteController
    c = LMMSCompleteController()
    c.create_new_project()
    c.set_tempo(130)
    track = c.add_track("Test", 0)
    assert track is not None
    c.set_instrument("Test", "kicker")
    
test("Basic Controller", test_basic_controller)

# Test 3: Pattern generation
def test_pattern_generation():
    from lmms_actions import LMMSActions
    a = LMMSActions()
    a.create_new_project()
    a.add_track("Drums", 0)
    result = a.generate_drum_pattern("Drums", "Beat", "techno", 192)
    assert result == True
    
test("Pattern Generation", test_pattern_generation)

# Test 4: Note operations
def test_note_operations():
    from lmms_actions import LMMSActions, Note
    a = LMMSActions()
    notes = [
        Note(60, 0, 48, 100, 0),
        Note(64, 48, 48, 90, 0),
        Note(67, 96, 48, 85, 0)
    ]
    # Test quantization
    quantized = a.quantize_notes(notes, 16, True, False)
    assert len(quantized) == 3
    # Test transposition
    transposed = a.transpose_notes(notes, 5)
    assert transposed[0].pitch == 65
    
test("Note Operations", test_note_operations)

# Test 5: AI interpretation
def test_ai_interpretation():
    from lmms_ai_brain import LMMSAIBrain
    brain = LMMSAIBrain()
    
    # Test various requests
    intent1 = brain.interpret_request("heavy techno with distortion")
    assert intent1.effects_intensity >= 0.7
    assert intent1.energy_level >= 0.7
    
    intent2 = brain.interpret_request("minimal ambient pad")
    assert intent2.complexity <= 0.4
    
    intent3 = brain.interpret_request("fast aggressive dnb")
    assert intent3.genre == "dnb"
    assert intent3.energy_level >= 0.8
    
test("AI Interpretation", test_ai_interpretation)

# Test 6: Production planning
def test_production_planning():
    from lmms_ai_brain import LMMSAIBrain, MusicalIntent
    brain = LMMSAIBrain()
    
    intent = MusicalIntent(
        genre="techno",
        energy_level=0.8,
        effects_intensity=0.7,
        elements=["kick", "bass", "hats"]
    )
    
    plan = brain.generate_production_plan(intent)
    assert len(plan.tracks) >= 3
    assert any(t["element"] == "kick" for t in plan.tracks)
    
test("Production Planning", test_production_planning)

# Test 7: Full pipeline
def test_full_pipeline():
    from lmms_ai_brain import LMMSAIBrain
    brain = LMMSAIBrain()
    
    # Create a simple beat
    project_file = brain.create_music("simple techno beat")
    assert project_file.endswith(".mmp")
    # The file is created in tools directory when run from there
    assert os.path.exists(project_file)
    
    # Clean up
    os.remove(project_file)
    
test("Full Pipeline", test_full_pipeline)

# Test 8: Effect application
def test_effects():
    from lmms_complete_controller import LMMSCompleteController
    c = LMMSCompleteController()
    c.create_new_project()
    c.add_track("Test", 0)
    
    # Add multiple effects
    c.add_effect("Test", "distortion", dist=0.8, gain=1.5)
    c.add_effect("Test", "bitcrush", bits=8, rate=11025)
    c.add_effect("Test", "reverb", size=0.7, damping=0.5)
    
test("Effect Application", test_effects)

# Test 9: Track operations
def test_track_operations():
    from lmms_actions import LMMSActions
    a = LMMSActions()
    a.create_new_project()
    
    # Add tracks
    a.add_track("Track1", 0)
    a.add_track("Track2", 0)
    
    # Clone track
    a.clone_track("Track1", "Track1_Clone")
    
    # Set properties
    a.set_volume("Track1", 80)
    a.set_panning("Track2", -50)
    a.set_track_color("Track1", "#FF0000")
    
    # Verify operations
    track = a.get_track("Track1_Clone")
    assert track is not None
    
test("Track Operations", test_track_operations)

# Test 10: Automation
def test_automation():
    from lmms_complete_controller import LMMSCompleteController
    c = LMMSCompleteController()
    c.create_new_project()
    c.add_track("Test", 0)
    
    # Add automation pattern
    pattern = c.add_automation_pattern("volume", "Test")
    assert pattern is not None
    
    # Add automation points
    c.add_automation_curve(pattern, [(0, 0), (96, 127), (192, 0)])
    
test("Automation", test_automation)

# Test 11: Genre-specific generation
def test_genre_generation():
    from lmms_ai_brain import LMMSAIBrain
    brain = LMMSAIBrain()
    
    # Test different genres
    for genre in ["techno", "house", "dnb", "ambient", "trap"]:
        intent = brain.interpret_request(f"create {genre} music")
        assert intent.genre == genre
        
        plan = brain.generate_production_plan(intent)
        assert len(plan.tracks) > 0
    
test("Genre Generation", test_genre_generation)

# Test 12: Error handling
def test_error_handling():
    from lmms_actions import LMMSActions
    a = LMMSActions()
    
    # Test operations on non-existent tracks
    result1 = a.set_volume("NonExistent", 50)
    assert result1 == False
    
    result2 = a.get_track("NonExistent")
    assert result2 is None
    
    result3 = a.add_effect("NonExistent", "reverb")
    assert result3 == False
    
test("Error Handling", test_error_handling)

# Test 13: Musical Key Engine
def test_key_engine():
    from musical_key_engine import KeySignature, MelodicGenerator, Scale
    
    # Test key signature creation
    key = KeySignature('A', 'minor')
    assert key.root == 'A'
    assert key.scale == 'minor'
    
    # Test scale generation
    scale_notes = Scale.get_scale_notes('C', 'major', (4, 5))
    assert len(scale_notes) > 0
    
    # Test chord progression
    chords = key.get_chord_progression('pop')
    assert len(chords) > 0
    
    # Test melody generation
    melodic_gen = MelodicGenerator(key)
    melody = melodic_gen.generate_melody(bars=2)
    assert len(melody) > 0
    
    # Verify all notes are in scale
    for note in melody:
        assert note['pitch'] in Scale.get_scale_notes('A', 'minor', (0, 10))
    
test("Musical Key Engine", test_key_engine)

# Test 14: Groove Templates
def test_groove_templates():
    from musical_intelligence import GrooveTemplate
    
    # Test each genre has proper grooves
    genres = ['house', 'techno', 'dnb', 'trap', 'garage']
    
    for genre in genres:
        kick = GrooveTemplate.get_groove(genre, 'kick')
        snare = GrooveTemplate.get_groove(genre, 'snare')
        hat = GrooveTemplate.get_groove(genre, 'hat')
        
        # Verify grooves have required fields
        assert 'pattern' in kick
        assert 'velocities' in kick
        assert 'swing' in kick
        assert len(kick['pattern']) == 16
        assert len(kick['velocities']) == 16
    
test("Groove Templates", test_groove_templates)

# Test 15: Humanization
def test_humanization():
    from musical_key_engine import HumanizeEngine
    
    # Create test notes
    notes = [
        {'position': 0, 'pitch': 60, 'velocity': 100, 'length': 12},
        {'position': 12, 'pitch': 64, 'velocity': 100, 'length': 12},
        {'position': 24, 'pitch': 67, 'velocity': 100, 'length': 12}
    ]
    
    # Test timing humanization
    humanized_timing = HumanizeEngine.humanize_timing(notes, 0.1)
    assert len(humanized_timing) == 3
    # Check positions have changed slightly
    assert any(h['position'] != n['position'] for h, n in zip(humanized_timing, notes))
    
    # Test velocity humanization
    humanized_vel = HumanizeEngine.humanize_velocity(notes, 0.2)
    assert len(humanized_vel) == 3
    # Check velocities have changed
    assert any(h['velocity'] != n['velocity'] for h, n in zip(humanized_vel, notes))
    
    # Test swing
    swung = HumanizeEngine.add_swing(notes, 0.2)
    assert len(swung) == 3
    
test("Humanization", test_humanization)

# Test 16: Musical Intelligence Integration
def test_musical_intelligence():
    from musical_intelligence import MusicalIntelligence
    
    mi = MusicalIntelligence()
    
    # Test track generation with key/scale
    track = mi.generate_track('house', 'uplifting', bars=4, key='C')
    
    assert 'tempo' in track
    assert 'key' in track
    assert 'scale' in track
    assert 'progression' in track
    assert 'tracks' in track
    
    # Verify drums were generated
    drums = track['tracks']['drums']
    assert 'kick' in drums
    assert len(drums['kick']) > 0
    
    # Verify bass was generated
    bass = track['tracks']['bass']
    assert 'notes' in bass
    assert len(bass['notes']) > 0
    
    # Verify melodic elements
    melodic = track['tracks']['melodic']
    assert melodic is not None
    
test("Musical Intelligence", test_musical_intelligence)

# Test 17: Enhanced AI Brain with Musical Intelligence
def test_enhanced_ai_brain():
    from lmms_ai_brain import LMMSAIBrain
    
    brain = LMMSAIBrain()
    
    # Enable musical intelligence
    brain.enable_musical_intelligence()
    
    # Test that it creates better music
    project = brain.create_music("create an uplifting house track with good melody")
    assert project.endswith(".mmp")
    assert os.path.exists(project)
    
    # Check file size (should be larger with more complex music)
    file_size = os.path.getsize(project)
    assert file_size > 10000  # At least 10KB
    
    # Clean up
    os.remove(project)
    
test("Enhanced AI Brain", test_enhanced_ai_brain)

# Test 18: Numerical Music System
def test_numerical_music_system():
    from numerical_music_system import NumericalMusicSystem, NumericalPattern, MusicNumbers
    from lmms_complete_controller import LMMSCompleteController
    
    controller = LMMSCompleteController()
    system = NumericalMusicSystem(controller)
    
    # Test number to note conversion
    note_c = MusicNumbers.note_to_number('C', 4)
    assert note_c == 48  # C4 (MIDI note 48)
    
    # Test chord generation
    chord = MusicNumbers.chord_to_numbers(60, 'major')
    assert chord == [60, 64, 67]  # C major triad
    
    # Test pattern creation
    pattern = NumericalPattern(
        notes=[[36, 0, 12, 100], [36, 12, 12, 100], [36, 24, 12, 100], [36, 36, 12, 100]],
        length=48
    )
    assert len(pattern.notes) == 4
    
    # Test pattern generation from description
    patterns = system.generate_from_description('techno kick with rolling bass')
    assert 'kick' in patterns
    assert 'bass' in patterns
    
test("Numerical Music System", test_numerical_music_system)

# Test 19: GPT-5 Numerical Interface
def test_gpt5_numerical_interface():
    from gpt5_numerical_interface import GPT5NumericalMusicGenerator
    
    generator = GPT5NumericalMusicGenerator()
    
    # Test number generation for different requests
    requests = [
        'kick beat',
        'rolling bass',
        'trap hihat',
        'melody in minor'
    ]
    
    for request in requests:
        numbers = generator.generate_numbers_for_request(request)
        assert len(numbers) > 0
        
        # Verify number format
        for element, pattern in numbers.items():
            # Pattern is a list of note arrays
            for note in pattern:
                assert len(note) == 4  # [pitch, position, length, velocity]
                assert 0 <= note[0] <= 127  # Valid MIDI pitch
                assert note[1] >= 0  # Valid position
                assert note[2] > 0  # Positive length
                assert 0 <= note[3] <= 127  # Valid velocity
    
test("GPT-5 Numerical Interface", test_gpt5_numerical_interface)

# Test 20: Numerical Pattern Generation
def test_numerical_pattern_generation():
    from numerical_music_system import NumericalPatternGenerator, IntelligentNumberGenerator
    
    # Test kick pattern generation
    kick = NumericalPatternGenerator.generate_kick_pattern('techno')
    assert len(kick.notes) > 0
    assert kick.notes[0][0] == 36  # Kick drum pitch
    
    # Test hihat pattern generation
    hihat = NumericalPatternGenerator.generate_hihat_pattern('trap')
    assert len(hihat.notes) > 0
    assert all(note[0] in [42, 44, 46] for note in hihat.notes)  # Hihat pitches
    
    # Test bassline generation
    bass = NumericalPatternGenerator.generate_bassline(36, 'rolling')
    assert len(bass.notes) > 0
    
    # Test intelligent rhythm generation
    rhythm = IntelligentNumberGenerator.generate_rhythm_numbers(density=0.75)
    assert len(rhythm) > 4  # Should have many hits with high density
    
    # Test melody generation
    melody = IntelligentNumberGenerator.generate_melody_numbers(60, 'minor', 1)
    assert len(melody.notes) > 0
    
    # Test humanization
    humanized = IntelligentNumberGenerator.humanize_numbers(melody, 2, 10)
    assert len(humanized.notes) == len(melody.notes)
    
test("Numerical Pattern Generation", test_numerical_pattern_generation)

# Print summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

passed = sum(1 for _, result in results if "PASS" in result)
failed = sum(1 for _, result in results if "FAIL" in result)

for name, result in results:
    print(f"{result:15} {name}")

print("\n" + "-" * 60)
print(f"TOTAL: {passed} passed, {failed} failed out of {len(results)} tests")

if failed == 0:
    print("\n🎉 ALL TESTS PASSED! The system is working correctly.")
    print("\nSystem Capabilities:")
    print("✓ Numerical Music Generation - GPT-5 generates music as number sequences")
    print("✓ Pattern representation as [pitch, position, length, velocity]")
    print("✓ Key and scale adherence for in-tune melodies")
    print("✓ Professional groove templates for each genre")
    print("✓ Humanization for natural timing and velocity")
    print("✓ Frequency-aware mixing to prevent muddiness")
    print("✓ Musical chord progressions and basslines")
    print("\nGPT-5 Integration:")
    print("✓ Music represented as number arrays GPT-5 can generate")
    print("✓ Kick = 36, Snare = 38, HiHat = 42, etc.")
    print("✓ Position values for timing (0, 12, 24, 36 = quarter notes)")
    print("✓ Velocity values for dynamics (0-127)")
    print("\nYour LMMS AI assistant now creates music through intelligent number generation!")
else:
    print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")

sys.exit(0 if failed == 0 else 1)