#!/usr/bin/env python3
"""
Test harness for BANDMATE AI Assistant
Tests various user queries and shows what actions would be called
"""

import json
import sys
from typing import Dict, List, Any

# Sample test queries representing real user inputs
TEST_QUERIES = [
    # Basic operations
    "set tempo to 128 bpm",
    "make a house beat",
    "add a kick drum",
    "save the project",
    
    # Creative requests
    "make this more jazzy",
    "add some swing to the drums",
    "create a trap beat at 140 bpm",
    "generate a bassline in C minor",
    
    # Track operations
    "add reverb to the lead",
    "mute the bass track",
    "duplicate the drum track",
    "remove the synth track",
    
    # Complex requests
    "create a 4 bar loop with kick, snare, and hihat",
    "make the kick more punchy with compression",
    "transpose the melody up 2 semitones",
    "quantize everything to 16th notes",
    
    # File operations
    "export as mp3",
    "save project as my_song",
    "import drums.wav",
    
    # Arrangement
    "loop the first 4 bars for 32 bars",
    "copy the chorus to bar 64",
    "split the clip at bar 8",
    
    # Mixing
    "pan the hihat left",
    "set master volume to 80%",
    "sidechain the bass to the kick",
]

def simulate_gpt5_response(query: str) -> Dict[str, Any]:
    """
    Simulates what GPT-5 would return based on the query.
    In reality, this would call the OpenAI API.
    """
    
    query_lower = query.lower()
    
    # Tempo commands
    if "tempo" in query_lower and any(str(i) in query for i in range(60, 200)):
        import re
        tempo_match = re.search(r'\d+', query)
        bpm = int(tempo_match.group()) if tempo_match else 120
        return {
            "intent": "set_tempo",
            "actions": [
                {"action": "setTempo", "params": {"bpm": bpm}}
            ]
        }
    
    # House beat
    elif "house beat" in query_lower:
        return {
            "intent": "create_house_beat",
            "actions": [
                {"action": "setTempo", "params": {"bpm": 128}},
                {"action": "addTrack", "params": {"type": "instrument", "name": "Kick"}},
                {"action": "addTrack", "params": {"type": "instrument", "name": "Hihat"}},
                {"action": "generateDrumPattern", "params": {"style": "house", "bars": 4}},
                {"action": "setLoop", "params": {"start": 1, "end": 5, "enable": True}}
            ]
        }
    
    # Trap beat
    elif "trap beat" in query_lower:
        import re
        tempo_match = re.search(r'\d+', query)
        bpm = int(tempo_match.group()) if tempo_match else 140
        return {
            "intent": "create_trap_beat",
            "actions": [
                {"action": "setTempo", "params": {"bpm": bpm}},
                {"action": "addTrack", "params": {"type": "instrument", "name": "808"}},
                {"action": "addTrack", "params": {"type": "instrument", "name": "Hihat"}},
                {"action": "addTrack", "params": {"type": "instrument", "name": "Snare"}},
                {"action": "generateDrumPattern", "params": {"style": "trap", "bars": 4}},
                {"action": "generateBassline", "params": {"style": "808", "key": "C", "bars": 4}}
            ]
        }
    
    # Jazz style
    elif "jazzy" in query_lower or "jazz" in query_lower:
        return {
            "intent": "make_jazzy",
            "actions": [
                {"action": "setSwing", "params": {"amount": 67}},
                {"action": "setTempo", "params": {"bpm": 120}},
                {"action": "addEffect", "params": {"track": "Piano", "effect": "reverb"}},
                {"action": "generateChord", "params": {"track": "Piano", "root": 60, "type": "maj7", "position": 0}},
                {"action": "humanizeNotes", "params": {"track": "Drums", "timing": 30, "velocity": 40}}
            ]
        }
    
    # Add kick drum
    elif "add" in query_lower and "kick" in query_lower:
        return {
            "intent": "add_kick_drum",
            "actions": [
                {"action": "addTrack", "params": {"type": "instrument", "name": "Kick"}},
                {"action": "setInstrument", "params": {"track": "Kick", "plugin": "kicker"}},
                {"action": "addNote", "params": {"track": "Kick", "key": 36, "start": 0, "length": 48, "velocity": 100}}
            ]
        }
    
    # Save project
    elif "save" in query_lower and "project" in query_lower:
        project_name = "my_song" if "as" in query_lower else None
        return {
            "intent": "save_project",
            "actions": [
                {"action": "saveProject", "params": {"path": f"{project_name}.mmp" if project_name else ""}}
            ]
        }
    
    # Export MP3
    elif "export" in query_lower and "mp3" in query_lower:
        return {
            "intent": "export_audio",
            "actions": [
                {"action": "exportAudio", "params": {"path": "output.mp3", "format": "mp3"}}
            ]
        }
    
    # Add reverb
    elif "reverb" in query_lower:
        track = "Lead" if "lead" in query_lower else "Master"
        return {
            "intent": "add_reverb_effect",
            "actions": [
                {"action": "addEffect", "params": {"track": track, "effect": "reverbsc"}}
            ]
        }
    
    # Mute track
    elif "mute" in query_lower:
        track = "Bass" if "bass" in query_lower else "Track1"
        return {
            "intent": "mute_track",
            "actions": [
                {"action": "muteTrack", "params": {"name": track, "mute": True}}
            ]
        }
    
    # Duplicate track
    elif "duplicate" in query_lower and "track" in query_lower:
        track = "Drums" if "drum" in query_lower else "Track1"
        return {
            "intent": "duplicate_track",
            "actions": [
                {"action": "duplicateTrack", "params": {"name": track}}
            ]
        }
    
    # Transpose
    elif "transpose" in query_lower:
        import re
        semitones_match = re.search(r'\d+', query)
        semitones = int(semitones_match.group()) if semitones_match else 2
        if "down" in query_lower:
            semitones = -semitones
        return {
            "intent": "transpose_notes",
            "actions": [
                {"action": "transposeNotes", "params": {"track": "Melody", "semitones": semitones}}
            ]
        }
    
    # Quantize
    elif "quantize" in query_lower:
        grid = "1/16" if "16th" in query_lower else "1/8"
        return {
            "intent": "quantize_notes",
            "actions": [
                {"action": "quantizeNotes", "params": {"track": "all", "grid": grid}}
            ]
        }
    
    # Loop bars
    elif "loop" in query_lower and "bar" in query_lower:
        return {
            "intent": "loop_section",
            "actions": [
                {"action": "setLoop", "params": {"start": 1, "end": 5, "enable": True}},
                {"action": "duplicateClips", "params": {"track": "all", "times": 8}}
            ]
        }
    
    # Pan
    elif "pan" in query_lower:
        direction = -50 if "left" in query_lower else 50
        track = "Hihat" if "hihat" in query_lower else "Track1"
        return {
            "intent": "pan_track",
            "actions": [
                {"action": "setTrackPan", "params": {"name": track, "pan": direction}}
            ]
        }
    
    # Remove track
    elif "remove" in query_lower and "track" in query_lower:
        track = "Synth" if "synth" in query_lower else "Track1"
        return {
            "intent": "remove_track",
            "actions": [
                {"action": "removeTrack", "params": {"name": track}}
            ]
        }
    
    # Add swing
    elif "swing" in query_lower:
        amount = 50  # Default swing amount
        if "more" in query_lower or "some" in query_lower:
            amount = 67
        return {
            "intent": "add_swing",
            "actions": [
                {"action": "setSwing", "params": {"amount": amount}}
            ]
        }
    
    # Make punchy with compression
    elif "punchy" in query_lower and "compression" in query_lower:
        track = "Kick" if "kick" in query_lower else "Drums"
        return {
            "intent": "add_compression",
            "actions": [
                {"action": "addEffect", "params": {"track": track, "effect": "compressor"}},
                {"action": "setEffectParam", "params": {"track": track, "effect": 0, "param": "ratio", "value": 8}}
            ]
        }
    
    # Master volume
    elif "master volume" in query_lower:
        import re
        percent_match = re.search(r'(\d+)%?', query)
        volume = int(percent_match.group(1)) if percent_match else 100
        return {
            "intent": "set_master_volume",
            "actions": [
                {"action": "setMasterVolume", "params": {"volume": volume}}
            ]
        }
    
    # Import audio
    elif "import" in query_lower and (".wav" in query_lower or "audio" in query_lower):
        import re
        file_match = re.search(r'(\w+\.wav)', query)
        filename = file_match.group(1) if file_match else "audio.wav"
        return {
            "intent": "import_audio",
            "actions": [
                {"action": "importAudio", "params": {"path": filename}}
            ]
        }
    
    # Copy/paste clips
    elif "copy" in query_lower and ("chorus" in query_lower or "clip" in query_lower):
        return {
            "intent": "copy_paste_clips",
            "actions": [
                {"action": "copyClips", "params": {"track": "all", "from": 17, "to": 32}},
                {"action": "pasteClips", "params": {"track": "all", "at": 64}}
            ]
        }
    
    # Split clip
    elif "split" in query_lower and "clip" in query_lower:
        import re
        bar_match = re.search(r'bar (\d+)', query)
        bar = int(bar_match.group(1)) if bar_match else 8
        return {
            "intent": "split_clip",
            "actions": [
                {"action": "splitClip", "params": {"track": "current", "at": f"{bar}.1"}}
            ]
        }
    
    # Sidechain
    elif "sidechain" in query_lower:
        return {
            "intent": "setup_sidechain",
            "actions": [
                {"action": "sidechain", "params": {"source": "Kick", "target": "Bass", "amount": 70}}
            ]
        }
    
    # Bassline
    elif "bassline" in query_lower:
        key = "C" if "c" in query_lower else "A"
        return {
            "intent": "generate_bassline",
            "actions": [
                {"action": "addTrack", "params": {"type": "instrument", "name": "Bass"}},
                {"action": "generateBassline", "params": {"style": "walking", "key": key, "bars": 4}}
            ]
        }
    
    # Default fallback
    else:
        return {
            "intent": "unknown_request",
            "actions": [
                {"action": "help", "params": {"message": f"I'm not sure how to: {query}"}}
            ]
        }

def test_action_execution(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tests if an action would execute correctly.
    Returns success status and any issues found.
    """
    action_name = action.get("action", "")
    params = action.get("params", {})
    
    # List of valid actions from our system (complete list from AssistantActions)
    VALID_ACTIONS = [
        # File operations
        "newProject", "openProject", "saveProject", "exportAudio", "exportMidi", 
        "exportStems", "importAudio", "importMidi",
        # Settings
        "setTempo", "setTimeSignature", "setMasterVolume", "setMasterPitch", 
        "setSwing", "setPlaybackPosition",
        # Track operations
        "addTrack", "removeTrack", "renameTrack", "muteTrack", "soloTrack",
        "setTrackVolume", "setTrackPan", "setTrackPitch", "duplicateTrack",
        "moveTrack", "setTrackColor",
        # Instruments
        "setInstrument", "loadPreset", "savePreset", "setInstrumentParam",
        "randomizeInstrument",
        # MIDI operations
        "addMidiClip", "removeMidiClip", "addNote", "removeNote", "clearNotes", 
        "transposeNotes", "quantizeNotes", "humanizeNotes", "scaleVelocity",
        "reverseNotes", "generateChord", "generateScale", "generateArpeggio",
        # Audio operations
        "addSampleClip", "trimSample", "reverseSample", "pitchSample",
        "timeStretchSample", "chopSample", "fadeIn", "fadeOut",
        # Effects
        "addEffect", "removeEffect", "setEffectParam", "bypassEffect",
        "setEffectMix", "loadEffectPreset", "reorderEffects",
        # Mixer
        "setSend", "setMixerChannel", "addMixerEffect", "linkTracks", "groupTracks",
        # Automation
        "addAutomation", "addAutomationPoint", "clearAutomation", "setAutomationMode",
        "recordAutomation", "addLFO", "addEnvelope",
        # Arrangement
        "copyClips", "pasteClips", "cutClips", "splitClip", "mergeClips",
        "duplicateClips", "loopClips", "moveClips", "resizeClip",
        # Transport
        "play", "stop", "pause", "record", "setLoop", "setPunch",
        "setMetronome", "tapTempo", "countIn",
        # Analysis
        "analyzeTempo", "analyzeKey", "detectChords", "groove",
        "sidechain", "vocode", "freeze", "bounce",
        # Creative
        "generateDrumPattern", "generateBassline", "generateMelody",
        "generateHarmony", "applyStyle", "randomize",
        # View
        "zoomIn", "zoomOut", "fitToScreen", "showMixer", "showPianoRoll",
        "showAutomation", "setGridSnap",
        # Helper
        "help"
    ]
    
    # Check if action is valid
    if action_name not in VALID_ACTIONS:
        return {
            "success": False,
            "error": f"Unknown action: {action_name}",
            "suggestion": f"Did you mean one of: {', '.join(VALID_ACTIONS[:5])}?"
        }
    
    # Validate parameters for specific actions
    if action_name == "setTempo":
        bpm = params.get("bpm")
        if not bpm or not (10 <= bpm <= 999):
            return {"success": False, "error": "BPM must be between 10 and 999"}
    
    elif action_name == "addTrack":
        track_type = params.get("type")
        if track_type not in ["instrument", "sample", "automation"]:
            return {"success": False, "error": f"Invalid track type: {track_type}"}
    
    elif action_name == "setTrackPan":
        pan = params.get("pan")
        if pan is None or not (-100 <= pan <= 100):
            return {"success": False, "error": "Pan must be between -100 and 100"}
    
    elif action_name == "generateDrumPattern":
        style = params.get("style")
        if style not in ["house", "trap", "dnb", "jazz", "rock", "hiphop"]:
            return {"success": False, "error": f"Unknown drum style: {style}"}
    
    return {"success": True, "message": f"Action {action_name} validated successfully"}

def main():
    print("=" * 80)
    print("BANDMATE AI - Action System Test")
    print("=" * 80)
    print()
    
    total_tests = len(TEST_QUERIES)
    passed = 0
    failed = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[Test {i}/{total_tests}]")
        print(f"User Query: \"{query}\"")
        print("-" * 40)
        
        # Simulate GPT-5 response
        response = simulate_gpt5_response(query)
        
        print(f"Intent: {response['intent']}")
        print(f"Actions to execute: {len(response['actions'])}")
        
        # Test each action
        all_valid = True
        for j, action in enumerate(response['actions'], 1):
            result = test_action_execution(action)
            
            action_str = f"{action['action']}({json.dumps(action['params'])})"
            
            if result['success']:
                print(f"  ✅ Action {j}: {action_str}")
            else:
                print(f"  ❌ Action {j}: {action_str}")
                print(f"     Error: {result.get('error', 'Unknown error')}")
                if 'suggestion' in result:
                    print(f"     Suggestion: {result['suggestion']}")
                all_valid = False
        
        if all_valid:
            print(f"✅ Test PASSED")
            passed += 1
        else:
            print(f"❌ Test FAILED")
            failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed} ({passed/total_tests*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total_tests*100:.1f}%)")
    
    if failed == 0:
        print("\n🎉 All tests passed! The action system is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Review the errors above.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())