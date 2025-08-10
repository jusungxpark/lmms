#!/usr/bin/env python3
"""
Test edge cases and error handling for BANDMATE AI
"""

import json
from test_assistant import simulate_gpt5_response, test_action_execution

# Edge case queries
EDGE_CASES = [
    # Ambiguous requests
    "make it better",
    "do something cool",
    "fix this",
    
    # Invalid parameters
    "set tempo to 10000",
    "pan the track 200% left",
    "set volume to -50",
    
    # Complex multi-step requests
    "create a full EDM track with intro, buildup, drop, and outro",
    "make it sound like deadmau5 but with more jazz influences",
    
    # Contradictory requests
    "make it faster but keep the tempo at 120",
    "add silence with lots of reverb",
    
    # Technical requests
    "apply FFT analysis and boost 2.5kHz by 3dB",
    "implement parallel compression with 3:1 ratio and -10dB threshold",
]

def test_edge_cases():
    print("=" * 80)
    print("EDGE CASE TESTING")
    print("=" * 80)
    
    for query in EDGE_CASES:
        print(f"\nQuery: \"{query}\"")
        response = simulate_gpt5_response(query)
        print(f"Intent: {response['intent']}")
        
        if response['intent'] == 'unknown_request':
            print("✅ Correctly handled as unknown/ambiguous")
        else:
            print(f"Actions: {len(response['actions'])}")
            for action in response['actions']:
                result = test_action_execution(action)
                if not result['success']:
                    print(f"  ⚠️  {result.get('error', 'Error')}")

def test_parameter_validation():
    print("\n" + "=" * 80)
    print("PARAMETER VALIDATION TESTING")
    print("=" * 80)
    
    test_cases = [
        {"action": "setTempo", "params": {"bpm": 10000}, "should_fail": True},
        {"action": "setTempo", "params": {"bpm": 120}, "should_fail": False},
        {"action": "setTrackPan", "params": {"name": "Track", "pan": 200}, "should_fail": True},
        {"action": "setTrackPan", "params": {"name": "Track", "pan": -50}, "should_fail": False},
        {"action": "addTrack", "params": {"type": "invalid_type", "name": "Test"}, "should_fail": True},
        {"action": "addTrack", "params": {"type": "instrument", "name": "Test"}, "should_fail": False},
        {"action": "generateDrumPattern", "params": {"style": "unknown", "bars": 4}, "should_fail": True},
        {"action": "generateDrumPattern", "params": {"style": "house", "bars": 4}, "should_fail": False},
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        result = test_action_execution(test)
        expected = "fail" if test["should_fail"] else "pass"
        actual = "fail" if not result["success"] else "pass"
        
        if expected == actual:
            print(f"✅ {test['action']} validation: {expected} (as expected)")
            passed += 1
        else:
            print(f"❌ {test['action']} validation: expected {expected}, got {actual}")
            failed += 1
    
    print(f"\nValidation tests: {passed} passed, {failed} failed")

def test_action_chaining():
    print("\n" + "=" * 80)
    print("ACTION CHAINING TEST")
    print("=" * 80)
    
    # Test a complex chain of actions
    complex_query = "Create a complete house track"
    response = {
        "intent": "create_complete_track",
        "actions": [
            {"action": "newProject", "params": {}},
            {"action": "setTempo", "params": {"bpm": 128}},
            {"action": "setTimeSignature", "params": {"numerator": 4, "denominator": 4}},
            {"action": "addTrack", "params": {"type": "instrument", "name": "Kick"}},
            {"action": "addTrack", "params": {"type": "instrument", "name": "Bass"}},
            {"action": "addTrack", "params": {"type": "instrument", "name": "Lead"}},
            {"action": "generateDrumPattern", "params": {"style": "house", "bars": 8}},
            {"action": "generateBassline", "params": {"style": "walking", "key": "C", "bars": 8}},
            {"action": "addEffect", "params": {"track": "Lead", "effect": "reverb"}},
            {"action": "addEffect", "params": {"track": "Kick", "effect": "compressor"}},
            {"action": "sidechain", "params": {"source": "Kick", "target": "Bass", "amount": 60}},
            {"action": "setLoop", "params": {"start": 1, "end": 9, "enable": True}},
            {"action": "duplicateClips", "params": {"track": "all", "times": 4}},
            {"action": "exportAudio", "params": {"path": "house_track.wav", "format": "wav"}},
        ]
    }
    
    print(f"Testing {len(response['actions'])} chained actions...")
    all_valid = True
    
    for i, action in enumerate(response['actions'], 1):
        result = test_action_execution(action)
        action_str = f"{action['action']}({json.dumps(action.get('params', {}))})"
        
        if result['success']:
            print(f"  [{i:2d}] ✅ {action_str}")
        else:
            print(f"  [{i:2d}] ❌ {action_str}: {result.get('error', 'Failed')}")
            all_valid = False
    
    if all_valid:
        print("\n✅ Action chain validation PASSED")
    else:
        print("\n❌ Action chain validation FAILED")

if __name__ == "__main__":
    test_edge_cases()
    test_parameter_validation()
    test_action_chaining()
    
    print("\n" + "=" * 80)
    print("Edge case testing complete!")
    print("=" * 80)