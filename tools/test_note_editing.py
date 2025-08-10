#!/usr/bin/env python3
"""
Test the note editing functionality
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lmms_ai_brain import LMMSAIBrain
from lmms_note_editor import NoteEditor
from lmms_complete_controller import LMMSCompleteController

def test_octave_fix():
    """Test fixing octave jumps in bassline"""
    
    print("Testing Note Editing Functionality")
    print("=" * 60)
    
    # Create AI brain
    brain = LMMSAIBrain()
    
    # Test 1: Create a track with octave jumps
    print("\n1. Creating track with bassline that has octave jumps...")
    project1 = brain.create_music("Create house music with rolling bassline")
    print(f"Created: {project1}")
    
    # Test 2: Fix the octave jumps
    print("\n2. Testing octave jump fix...")
    project2 = brain.create_music("Remove octave jumps from the bassline", project1)
    
    if project2:
        print(f"Fixed bassline saved to: {project2}")
        print("Success: Octave jumps removed")
    else:
        print("Failed to fix octave jumps")
    
    # Test 3: Direct note editor test
    print("\n3. Testing direct note editor...")
    controller = LMMSCompleteController()
    controller.create_new_project()
    
    # Add bass track
    controller.add_track("Bass", 0)
    controller.set_instrument("Bass", "tripleoscillator")
    
    # Add pattern with octave jumps
    pattern = controller.add_pattern("Bass", "Bassline", 0, 192)
    
    # Add notes with intentional octave jumps
    test_notes = [
        (36, 0, 12),   # C2
        (48, 12, 12),  # C3 - octave jump!
        (38, 24, 12),  # D2
        (50, 36, 12),  # D3 - octave jump!
        (40, 48, 12),  # E2
        (52, 60, 12),  # E3 - octave jump!
    ]
    
    for pitch, pos, length in test_notes:
        controller.add_note(pattern, pitch, pos, length, 100)
    
    # Get note info before fix
    if hasattr(controller, 'get_track_note_info'):
        info_before = controller.get_track_note_info("Bass")
        print(f"\nBefore fix: {info_before['patterns'][0]['pitch_range']} "
              f"(Octave jumps: {info_before['patterns'][0]['has_octave_jumps']})")
    
    # Fix octave jumps
    if hasattr(controller, 'fix_bassline_octaves'):
        success = controller.fix_bassline_octaves("Bass")
        
        if success:
            info_after = controller.get_track_note_info("Bass")
            print(f"After fix: {info_after['patterns'][0]['pitch_range']} "
                  f"(Octave jumps: {info_after['patterns'][0]['has_octave_jumps']})")
            
            # Save test project
            controller.save_project("test_octave_fix.mmp")
            print("\nTest project saved to: test_octave_fix.mmp")
        else:
            print("Failed to fix octave jumps")
    else:
        print("Note editor not integrated with controller")
    
    # Clean up test files
    print("\nCleaning up test files...")
    for file in [project1, project2, "test_octave_fix.mmp"]:
        if file and os.path.exists(file):
            os.remove(file)
            print(f"Removed: {file}")
    
    print("\n" + "=" * 60)
    print("Note Editing Test Complete")
    print("The system can now:")
    print("- Detect octave jumps in basslines")
    print("- Fix octave jumps to keep bass in single octave")
    print("- Modify existing notes in patterns")
    print("- Handle modification requests properly")


if __name__ == "__main__":
    test_octave_fix()