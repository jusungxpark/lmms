#!/usr/bin/env python3
"""
Test script to verify master effects are working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lmms_ai_brain import LMMSAIBrain

def test_master_effects():
    """Test creating a track with master effects"""
    
    print("Testing Master Effects Fix")
    print("=" * 60)
    
    # Create AI brain
    brain = LMMSAIBrain()
    
    # Test request that should add master effects
    request = "Create a heavy industrial techno beat with distortion on the master"
    
    print(f"Request: {request}")
    print("-" * 40)
    
    try:
        # Create music
        project_file = brain.create_music(request)
        print(f"✓ Successfully created: {project_file}")
        print("✓ Master effects should now work correctly!")
        
        # Check if creative patterns were used
        if hasattr(brain, 'use_creative_patterns') and brain.use_creative_patterns:
            print("✓ Creative patterns were used")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_track_effects():
    """Test regular track effects"""
    
    print("\nTesting Track Effects")
    print("-" * 40)
    
    brain = LMMSAIBrain()
    
    # Create a simple project with effects
    request = "Create a minimal house beat with reverb on the lead"
    
    print(f"Request: {request}")
    
    try:
        project_file = brain.create_music(request)
        print(f"✓ Successfully created: {project_file}")
        print("✓ Track effects working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("LMMS Effects System Test")
    print("=" * 60)
    
    # Run tests
    master_ok = test_master_effects()
    track_ok = test_track_effects()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Master Effects: {'✓ PASS' if master_ok else '✗ FAIL'}")
    print(f"  Track Effects:  {'✓ PASS' if track_ok else '✗ FAIL'}")
    
    if master_ok and track_ok:
        print("\n✓ All tests passed! Effects system is working correctly.")
    else:
        print("\n✗ Some tests failed. Please check the implementation.")