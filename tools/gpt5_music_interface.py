#!/usr/bin/env python3
"""
GPT-5 Music Interface - Natural language to music production
This interface allows GPT-5 to understand any musical request and create it intelligently
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
import subprocess
import time

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_ai_brain import LMMSAIBrain, MusicalIntent, ProductionPlan
from lmms_actions import Note
from gpt5_context_aware import ContextAwareGPT5Interface, ContextAnalyzer, ProjectContext


class GPT5MusicInterface:
    """
    Interface for GPT-5 to create music based on natural language requests
    This system uses multiple AI layers for maximum intelligence
    """
    
    def __init__(self, api_key: Optional[str] = None, context_aware: bool = True):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.brain = LMMSAIBrain(self.api_key)
        self.session_history = []
        self.context_aware = context_aware
        self.context_interface = ContextAwareGPT5Interface(self.api_key) if context_aware else None
        self.current_project = None
        
        if self.api_key and HAS_OPENAI:
            openai.api_key = self.api_key
        elif self.api_key and not HAS_OPENAI:
            print("Warning: API key provided but OpenAI library not available")
            self.api_key = None
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """
        Process any musical request with full AI intelligence
        Now with context awareness like Cursor
        """
        
        # Add to session history for context
        self.session_history.append({"role": "user", "request": request})
        
        # Check if we should use context-aware processing
        if self.context_aware and self.context_interface:
            # Determine if this is a modification request or new creation
            request_lower = request.lower()
            is_modification = any(word in request_lower for word in [
                'add', 'change', 'modify', 'make it', 'more', 'less', 
                'heavier', 'lighter', 'faster', 'slower', 'variation'
            ])
            
            if is_modification and self.current_project:
                # Use context-aware processing for modifications
                print("Analyzing existing project context...")
                result = self.context_interface.process_request_with_context(
                    request, 
                    self.current_project
                )
                
                if result.get('project_file'):
                    self.current_project = result['project_file']
                    
                # Add context-aware suggestions
                if result.get('status') == 'success':
                    result['next_suggestions'] = self.context_interface.suggest_next_actions()
                    
                return result
            
            # For new projects, check if we should analyze context from templates
            elif 'like' in request_lower or 'similar to' in request_lower:
                # Analyze reference for context
                print("Analyzing reference style for context...")
                # This would analyze a reference track/style
                pass
        
        # Standard processing (original behavior)
        # Use GPT to enhance and clarify the request if needed
        enhanced_request = self._enhance_request(request)
        
        # Create the music
        result = {
            "original_request": request,
            "enhanced_request": enhanced_request,
            "status": "processing"
        }
        
        try:
            # Let the AI brain handle everything
            project_file = self.brain.create_music(enhanced_request)
            self.current_project = project_file  # Store for context-aware modifications
            
            # Analyze what was created
            analysis = self._analyze_creation(project_file, enhanced_request)
            
            result.update({
                "status": "success",
                "project_file": project_file,
                "analysis": analysis,
                "instructions": f"Open {project_file} in LMMS to hear the music"
            })
            
            # If context-aware, add suggestions
            if self.context_aware and self.context_interface:
                # Analyze the newly created project
                context = self.context_interface.analyzer.analyze_project(project_file)
                result['context_summary'] = self.context_interface._summarize_context(context)
                result['next_suggestions'] = context.suggestions[:3] if context.suggestions else []
            
            # Add to history
            self.session_history.append({"role": "assistant", "result": result})
            
        except Exception as e:
            result.update({
                "status": "error",
                "error": str(e)
            })
        
        return result
    
    def _enhance_request(self, request: str) -> str:
        """
        Use GPT to enhance and clarify the musical request
        """
        if not self.api_key:
            return request
        
        # Check if request needs enhancement
        if len(request.split()) < 5:  # Short request, might need details
            prompt = f"""
            The user wants to create music with this request: "{request}"
            
            Enhance this request with musical details while preserving the original intent.
            Consider adding:
            - Genre specification if unclear
            - Tempo indication if not specified
            - Musical elements that would fit
            - Production characteristics
            
            Keep the enhanced request natural and musical.
            If the request is already clear and complete, return it as is.
            
            Context from session: {json.dumps(self.session_history[-3:]) if len(self.session_history) > 0 else "New session"}
            """
            
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a music production assistant who helps clarify musical requests."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                enhanced = response.choices[0].message.content.strip()
                print(f"Enhanced request: {enhanced}")
                return enhanced
                
            except:
                return request
        
        return request
    
    def _analyze_creation(self, project_file: str, request: str) -> Dict[str, Any]:
        """
        Analyze what was created and provide insights
        """
        analysis = {
            "created_file": project_file,
            "request_fulfilled": True,
            "description": "Music created based on your request"
        }
        
        if self.api_key:
            # Use GPT to provide a description of what was created
            prompt = f"""
            A music file was created based on this request: "{request}"
            
            Provide a brief, enthusiastic description of what was likely created,
            mentioning the genre, mood, and key characteristics.
            Keep it under 50 words.
            """
            
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a music journalist describing new tracks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=100
                )
                
                analysis["description"] = response.choices[0].message.content.strip()
                
            except:
                pass
        
        return analysis
    
    def process_batch_requests(self, requests: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple musical requests
        """
        results = []
        for request in requests:
            print(f"\nProcessing: {request}")
            result = self.process_request(request)
            results.append(result)
            time.sleep(1)  # Avoid overwhelming the system
        
        return results
    
    def preview_changes(self, request: str) -> Dict[str, Any]:
        """
        Preview what changes would be made without applying them
        Like Cursor's diff preview before accepting changes
        """
        if self.context_aware and self.context_interface:
            return self.context_interface.preview_changes(request)
        else:
            return {
                "message": "Context-aware mode is not enabled",
                "suggestion": "Initialize with context_aware=True to enable preview"
            }
    
    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the current project context
        Like Cursor showing the current file/function context
        """
        if not self.current_project:
            return None
            
        if self.context_aware and self.context_interface:
            context = self.context_interface.analyzer.analyze_project(self.current_project)
            return {
                "file": self.current_project,
                "summary": self.context_interface._summarize_context(context),
                "tracks": len(context.tracks),
                "tempo": context.tempo,
                "key": context.key,
                "genre": context.genre,
                "style": context.style_characteristics,
                "suggestions": context.suggestions
            }
        return {"file": self.current_project}
    
    def suggest_variations(self, original_request: str) -> List[str]:
        """
        Suggest variations of a musical request
        """
        if not self.api_key:
            # Rule-based variations
            variations = []
            if "techno" in original_request.lower():
                variations = [
                    original_request.replace("techno", "house"),
                    original_request + " with more energy",
                    original_request + " but minimal"
                ]
            else:
                variations = [
                    original_request + " with heavy bass",
                    original_request + " in a darker style",
                    original_request + " with complex rhythms"
                ]
            return variations[:3]
        
        prompt = f"""
        Given this music request: "{original_request}"
        
        Suggest 3 interesting variations that would create different but related music.
        Make each variation distinct but keep them musically coherent.
        Return as a JSON array of strings.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative music producer suggesting variations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=200
            )
            
            variations = json.loads(response.choices[0].message.content)
            return variations[:3]
            
        except:
            return []
    
    def interactive_mode(self):
        """
        Interactive mode for continuous music creation
        """
        print("GPT-5 Music Interface - Interactive Mode")
        if self.context_aware:
            print("Context-Aware Mode: ENABLED")
        print("Type your musical requests, or 'quit' to exit")
        print("Examples:")
        print("  - 'make a heavy techno beat'")
        print("  - 'create something dark and minimal'")
        print("  - 'I want aggressive drums with distortion'")
        if self.context_aware:
            print("  - 'add more bass' (modifies existing project)")
            print("  - 'make it heavier' (context-aware modification)")
        print("\nCommands:")
        print("  - context: Show current project context")
        print("  - preview: Preview changes before applying")
        print("  - suggestions: Get AI suggestions")
        print("-" * 50)
        
        while True:
            request = input("\n> ").strip()
            
            if request.lower() in ['quit', 'exit', 'q']:
                print("Goodbye.")
                break
            
            if request.lower() == 'help':
                self._show_help()
                continue
            
            if request.lower() == 'context':
                # Show current context
                context = self.get_current_context()
                if context:
                    print("\nCurrent Project Context:")
                    print(f"  File: {context.get('file', 'None')}")
                    print(f"  Summary: {context.get('summary', 'Empty')}")
                    print(f"  Tracks: {context.get('tracks', 0)}")
                    print(f"  Tempo: {context.get('tempo', 'Unknown')} BPM")
                    print(f"  Key: {context.get('key', 'Unknown')}")
                    if context.get('suggestions'):
                        print("\nSuggestions:")
                        for s in context['suggestions'][:3]:
                            print(f"  - {s}")
                else:
                    print("No project loaded yet. Create some music first!")
                continue
            
            if request.lower().startswith('preview'):
                # Preview changes
                if len(request.split(' ', 1)) > 1:
                    preview_request = request.split(' ', 1)[1]
                    preview = self.preview_changes(preview_request)
                    print("\nPreview of changes:")
                    print(f"  Current: {preview.get('current_state', 'Unknown')}")
                    if preview.get('proposed_changes'):
                        print("  Proposed changes:")
                        for key, changes in preview['proposed_changes'].items():
                            if changes:
                                print(f"    - {key}: {len(changes)} changes")
                    if preview.get('impact'):
                        print(f"  Impact: {preview['impact'].get('risk_level', 'unknown')} risk")
                else:
                    print("Usage: preview <your request>")
                continue
            
            if request.lower() == 'suggestions':
                # Get AI suggestions
                if self.context_aware and self.context_interface and self.current_project:
                    suggestions = self.context_interface.suggest_next_actions()
                    print("\nAI Suggestions based on current context:")
                    for i, s in enumerate(suggestions, 1):
                        print(f"  {i}. {s}")
                else:
                    print("Create a project first to get contextual suggestions")
                continue
            
            if request.lower().startswith('variations'):
                # Show variations of last request
                if self.session_history:
                    last_request = self.session_history[-1].get("request", "")
                    variations = self.suggest_variations(last_request)
                    print("\nVariations you could try:")
                    for i, var in enumerate(variations, 1):
                        print(f"  {i}. {var}")
                continue
            
            # Process the request
            print(f"\nCreating music...")
            result = self.process_request(request)
            
            if result["status"] == "success":
                print(f"Success. {result['analysis']['description']}")
                print(f"File: {result['project_file']}")
                print(f"Open this file in LMMS to hear your music")
                
                # Suggest variations
                variations = self.suggest_variations(request)
                if variations:
                    print("\nYou might also like:")
                    for var in variations[:2]:
                        print(f"  - {var}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
    
    def _show_help(self):
        """Show help information"""
        print("""
        Music Creation Help
        
        You can make requests like:
        - Genre-based: "create techno", "make house music", "generate dnb"
        - Mood-based: "something dark", "uplifting track", "aggressive beat"
        - Technical: "heavy distortion", "minimal drums", "complex bassline"
        - Combined: "dark techno with heavy bass and minimal drums"
        
        Commands:
        - variations: Show variations of your last request
        - help: Show this help
        - quit: Exit the program
        
        Tips:
        - Be descriptive about what you want
        - Mention specific elements (kick, bass, lead, etc.)
        - Describe the mood or energy level
        - Specify effects or production style
        """)


class GPT5ActionInterface:
    """
    Direct action interface for GPT-5 to control LMMS
    This provides granular control when needed
    """
    
    def __init__(self):
        self.brain = LMMSAIBrain()
        self.current_project = None
    
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific musical action
        """
        actions = {
            "create_track": self._create_track,
            "add_effect": self._add_effect,
            "generate_pattern": self._generate_pattern,
            "set_tempo": self._set_tempo,
            "add_automation": self._add_automation,
            "modify_sound": self._modify_sound
        }
        
        if action in actions:
            return actions[action](params)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    
    def _create_track(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a track with specified parameters"""
        track_type = params.get("type", "synth")
        name = params.get("name", "Track")
        characteristics = params.get("characteristics", [])
        
        # Use AI brain to determine best settings
        inst_config = self.brain.knowledge.get_instrument_for_element(
            track_type, characteristics
        )
        
        self.brain.controller.add_track(name)
        self.brain.controller.set_instrument(name, inst_config["instrument"])
        
        for param, value in inst_config["params"].items():
            self.brain.controller.set_instrument_parameter(name, param, value)
        
        return {"status": "success", "track": name, "instrument": inst_config["instrument"]}
    
    def _add_effect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add an effect to a track"""
        track = params.get("track")
        effect_type = params.get("effect")
        intensity = params.get("intensity", 0.5)
        
        # Map intensity to effect parameters
        if intensity > 0.7:
            level = "heavy"
        elif intensity > 0.4:
            level = "moderate"
        else:
            level = "light"
        
        effect_params = self.brain.knowledge.EFFECT_INTENSITY_MAPPINGS.get(
            level, {}
        ).get(effect_type, {})
        
        self.brain.controller.add_effect(track, effect_type, **effect_params)
        
        return {"status": "success", "effect": effect_type, "parameters": effect_params}
    
    def _generate_pattern(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a pattern"""
        track = params.get("track")
        pattern_type = params.get("type", "basic")
        length = params.get("length", 192)
        complexity = params.get("complexity", 0.5)
        
        # Generate notes
        notes = self.brain._generate_pattern_notes(
            pattern_type, length, complexity, 0.7
        )
        
        # Add to track
        pattern = self.brain.controller.add_pattern(track, f"{pattern_type}_pattern", 0, length)
        for note_data in notes:
            note = Note(**note_data)
            pattern.append(note.to_xml())
        
        return {"status": "success", "pattern": f"{pattern_type}_pattern", "notes": len(notes)}
    
    def _set_tempo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set project tempo"""
        tempo = params.get("tempo", 128)
        self.brain.controller.set_tempo(tempo)
        return {"status": "success", "tempo": tempo}
    
    def _add_automation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add automation to a parameter"""
        target = params.get("target")
        parameter = params.get("parameter")
        curve = params.get("curve", "linear")
        
        # Create automation pattern
        pattern = self.brain.controller.add_automation_pattern(parameter, target)
        
        # Add points based on curve type
        if curve == "sweep":
            points = [(0, 0), (192, 127)]
        elif curve == "pulse":
            points = [(0, 0), (48, 127), (96, 0), (144, 127), (192, 0)]
        else:
            points = [(0, 64), (192, 64)]
        
        self.brain.controller.add_automation_curve(pattern, points)
        
        return {"status": "success", "automation": parameter, "curve": curve}
    
    def _modify_sound(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Modify sound characteristics"""
        track = params.get("track")
        characteristic = params.get("characteristic")
        amount = params.get("amount", 0.5)
        
        # Map characteristic to parameter changes
        if characteristic == "brightness":
            self.brain.controller.set_filter(track, cutoff=int(14000 * amount))
        elif characteristic == "warmth":
            self.brain.controller.set_filter(track, cutoff=int(5000 * (1 - amount)))
        elif characteristic == "punch":
            self.brain.controller.set_envelope(track, "vol", att=0.001 * (1 - amount))
        
        return {"status": "success", "modified": characteristic, "amount": amount}


def main():
    """Main entry point with different modes"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPT-5 Music Interface")
    parser.add_argument("request", nargs="*", help="Musical request")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Start interactive mode")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--batch", help="Process batch requests from file")
    
    args = parser.parse_args()
    
    # Set API key if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    
    # Create interface
    interface = GPT5MusicInterface()
    
    if args.interactive:
        interface.interactive_mode()
    elif args.batch:
        with open(args.batch, 'r') as f:
            requests = [line.strip() for line in f if line.strip()]
        results = interface.process_batch_requests(requests)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['original_request']}")
            print(f"   Status: {result['status']}")
            if result['status'] == 'success':
                print(f"   File: {result['project_file']}")
    elif args.request:
        request = " ".join(args.request)
        result = interface.process_request(request)
        
        if result["status"] == "success":
            print(f"\nMusic created successfully.")
            print(f"File: {result['project_file']}")
            print(f"{result['analysis']['description']}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
    else:
        # Start interactive mode by default
        interface.interactive_mode()


if __name__ == "__main__":
    main()