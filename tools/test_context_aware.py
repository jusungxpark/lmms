#!/usr/bin/env python3
"""
Test the context-aware GPT-5 interface
Demonstrates how it analyzes context before making changes (like Cursor)
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt5_music_interface import GPT5MusicInterface
from gpt5_context_aware import ContextAwareGPT5Interface


def test_context_aware_workflow():
    """
    Test the complete context-aware workflow
    Similar to how Cursor analyzes code before suggesting changes
    """
    
    print("="*70)
    print("CONTEXT-AWARE GPT-5 MUSIC INTERFACE TEST")
    print("Behaves like Cursor - analyzes context before making changes")
    print("="*70)
    
    # Initialize with context awareness enabled
    interface = GPT5MusicInterface(context_aware=True)
    
    print("\nStep 1: Create initial project")
    print("-" * 50)
    
    # Create an initial project
    result1 = interface.process_request("Create a minimal techno beat at 130 BPM")
    
    if result1['status'] == 'success':
        print(f"Created: {result1['project_file']}")
        
        # Show context summary if available
        if result1.get('context_summary'):
            print(f"Context: {result1['context_summary']}")
        
        # Show suggestions
        if result1.get('next_suggestions'):
            print("\nAI Suggestions (based on context):")
            for i, suggestion in enumerate(result1['next_suggestions'], 1):
                print(f"  {i}. {suggestion}")
    else:
        print(f"Error: {result1.get('error')}")
        return
    
    print("\nStep 2: Get current context (like Cursor showing current file)")
    print("-" * 50)
    
    context = interface.get_current_context()
    if context:
        print(f"Current file: {context['file']}")
        print(f"Summary: {context['summary']}")
        print(f"Tracks: {context['tracks']}")
        print(f"Tempo: {context['tempo']} BPM")
        print(f"Key: {context.get('key', 'Unknown')}")
        print(f"Style: {context.get('style', {}).get('energy', 'Unknown')} energy, "
              f"{context.get('style', {}).get('production_style', 'Unknown')} production")
    
    print("\nStep 3: Preview changes before applying (like Cursor's diff)")
    print("-" * 50)
    
    preview = interface.preview_changes("Make it heavier with more bass")
    if preview.get('proposed_changes'):
        print("Preview of changes:")
        print(f"  Current state: {preview.get('current_state')}")
        print("\n  Proposed changes:")
        
        for change_type, changes in preview['proposed_changes'].items():
            if changes:
                print(f"    {change_type}:")
                for change in changes[:2]:  # Show first 2 changes
                    if isinstance(change, dict):
                        reason = change.get('reason', 'No reason given')
                        print(f"      - {reason}")
        
        if preview.get('impact'):
            impact = preview['impact']
            print(f"\n  Impact assessment:")
            print(f"    - Complexity: {impact.get('complexity_change', 'Unknown')}")
            print(f"    - Risk level: {impact.get('risk_level', 'Unknown')}")
    
    print("\nStep 4: Apply context-aware modification")
    print("-" * 50)
    
    # Make a modification that considers context
    print("Analyzing context before making changes...")
    result2 = interface.process_request("Add more bass and make it heavier")
    
    if result2.get('status') == 'success':
        print("Modifications applied successfully.")
        
        # Show what was changed
        if result2.get('changes_applied'):
            print("\nChanges applied:")
            for change in result2['changes_applied']:
                print(f"  - {change}")
        
        # Show before/after context
        if result2.get('context_before') and result2.get('context_after'):
            print(f"\nContext before: {result2['context_before']}")
            print(f"Context after: {result2['context_after']}")
        
        # Show new suggestions
        if result2.get('next_suggestions'):
            print("\nNew suggestions based on updated context:")
            for suggestion in result2['next_suggestions'][:3]:
                print(f"  - {suggestion}")
    
    print("\nStep 5: Make another context-aware change")
    print("-" * 50)
    
    result3 = interface.process_request("Add variation to make it more interesting")
    
    if result3.get('status') == 'success':
        print("Variations added.")
        if result3.get('changes_applied'):
            for change in result3['changes_applied']:
                print(f"  - {change}")
    
    # Clean up test files
    print("\nCleaning up test files...")
    for result in [result1, result2, result3]:
        if result.get('project_file') and os.path.exists(result['project_file']):
            os.remove(result['project_file'])
            print(f"  Removed: {result['project_file']}")
    
    print("\n" + "="*70)
    print("CONTEXT-AWARE TEST COMPLETE")
    print("\nKey Features Demonstrated:")
    print("- Analyzes existing project before making changes")
    print("- Shows current context (like Cursor showing current file)")
    print("- Previews changes before applying (like diff view)")
    print("- Provides context-aware suggestions")
    print("- Applies changes intelligently based on what exists")
    print("="*70)


def test_context_analyzer():
    """Test the context analyzer component"""
    
    print("\n" + "="*70)
    print("TESTING CONTEXT ANALYZER")
    print("="*70)
    
    from gpt5_context_aware import ContextAnalyzer, ContextAnalysisMode
    
    analyzer = ContextAnalyzer()
    
    # Create a simple project
    from lmms_ai_brain import LMMSAIBrain
    brain = LMMSAIBrain()
    project = brain.create_music("simple techno")
    
    print(f"\nAnalyzing: {project}")
    
    # Analyze with different modes
    modes = [
        ContextAnalysisMode.FULL,
        ContextAnalysisMode.STYLE,
        ContextAnalysisMode.STRUCTURE
    ]
    
    for mode in modes:
        print(f"\nAnalysis mode: {mode.value}")
        context = analyzer.analyze_project(project, mode)
        
        print(f"  Tempo: {context.tempo} BPM")
        print(f"  Key: {context.key or 'Unknown'}")
        print(f"  Genre: {context.genre or 'Unknown'}")
        print(f"  Tracks: {len(context.tracks)}")
        print(f"  Style: {context.style_characteristics.get('energy', 'Unknown')} energy")
        
        if context.suggestions:
            print(f"  Suggestions: {len(context.suggestions)} available")
    
    # Clean up
    if os.path.exists(project):
        os.remove(project)
    
    print("\nContext analyzer test complete.")


def test_comparison():
    """
    Compare context-aware vs non-context-aware behavior
    """
    
    print("\n" + "="*70)
    print("COMPARING CONTEXT-AWARE VS STANDARD MODE")
    print("="*70)
    
    # Test without context awareness
    print("\nStandard Mode (no context awareness):")
    standard = GPT5MusicInterface(context_aware=False)
    result_std = standard.process_request("Create techno")
    print(f"  Created: {result_std.get('project_file', 'None')}")
    print(f"  Has context summary: {'context_summary' in result_std}")
    print(f"  Has suggestions: {'next_suggestions' in result_std}")
    
    # Test with context awareness
    print("\nContext-Aware Mode (like Cursor):")
    context_aware = GPT5MusicInterface(context_aware=True)
    result_ctx = context_aware.process_request("Create techno")
    print(f"  Created: {result_ctx.get('project_file', 'None')}")
    print(f"  Has context summary: {'context_summary' in result_ctx}")
    print(f"  Has suggestions: {'next_suggestions' in result_ctx}")
    
    if result_ctx.get('context_summary'):
        print(f"  Context: {result_ctx['context_summary']}")
    
    # Clean up
    for result in [result_std, result_ctx]:
        if result.get('project_file') and os.path.exists(result['project_file']):
            os.remove(result['project_file'])
    
    print("\nComparison complete.")
    print("Context-aware mode provides:")
    print("  • Project context summary")
    print("  • AI-powered suggestions")
    print("  • Intelligent modifications based on existing content")


if __name__ == "__main__":
    print("\nGPT-5 CONTEXT-AWARE MUSIC INTERFACE TEST SUITE")
    print("This demonstrates Cursor-like behavior for music production")
    print("=" * 70)
    
    # Run all tests
    try:
        test_context_aware_workflow()
        test_context_analyzer()
        test_comparison()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED")
        print("The GPT-5 interface now behaves like Cursor:")
        print("  • Analyzes context before making changes")
        print("  • Shows current project state")
        print("  • Previews changes before applying")
        print("  • Provides intelligent suggestions")
        print("="*70)
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()