#!/usr/bin/env python3
"""Code quality checker for BeatBot"""

import re
import sys
from pathlib import Path

def check_file(filepath):
    """Check a Python file for common issues"""
    issues = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines, 1):
        # Check for trailing whitespace
        if line.rstrip() != line.rstrip('\n').rstrip('\r'):
            issues.append(f'{filepath.name}:{i}: Trailing whitespace')
        
        # Check for tabs (should use spaces)
        if '\t' in line:
            issues.append(f'{filepath.name}:{i}: Tab character (use spaces)')
        
        # Check for very long lines
        if len(line.rstrip()) > 150:
            issues.append(f'{filepath.name}:{i}: Line too long ({len(line.rstrip())} > 150 chars)')
        
        # Check for print statements that should be logging
        if 'print(' in line and 'print(f' not in line and '__main__' not in str(filepath):
            if not any(x in line for x in ['# DEBUG', '# TODO', 'demo', 'test']):
                issues.append(f'{filepath.name}:{i}: Consider using logging instead of print')
    
    return issues

def main():
    """Check all Python files in beatbot"""
    beatbot_dir = Path(__file__).parent
    
    python_files = [
        'beatbot.py',
        'planner.py', 
        'planner_enhanced.py',
        'commands.py',
        'project.py',
        'demo_scripts.py',
        'providers/elevenlabs.py'
    ]
    
    all_issues = []
    
    for file in python_files:
        filepath = beatbot_dir / file
        if filepath.exists():
            issues = check_file(filepath)
            all_issues.extend(issues)
    
    if all_issues:
        print(f"Found {len(all_issues)} code quality issues:\n")
        for issue in all_issues[:20]:  # Show first 20
            print(f"  ⚠️  {issue}")
        
        if len(all_issues) > 20:
            print(f"\n  ... and {len(all_issues) - 20} more issues")
        return 1
    else:
        print("✅ No major code quality issues found!")
        print("\nFiles checked:")
        for file in python_files:
            if (beatbot_dir / file).exists():
                print(f"  ✓ {file}")
        return 0

if __name__ == "__main__":
    sys.exit(main())