#!/usr/bin/env python3
"""
Project Structure Validator

Validates that the project structure is consistent and all 
required files are present for proper operation.
"""

import os
import sys
from pathlib import Path

def validate_project_structure(project_root: str) -> bool:
    """Validate the project structure and return True if valid."""
    root = Path(project_root)
    issues = []
    
    # Check for main project files
    required_files = [
        'README.md',
        'LICENSE',
        'PROJECT_INDEX.md',
        'Makefile'
    ]
    
    for file_name in required_files:
        if not (root / file_name).exists():
            issues.append(f"❌ Missing required file: {file_name}")
        else:
            print(f"✅ Found: {file_name}")
    
    # Check component directories
    components = ['monolith', 'planner', 'research', 'lddemo']
    
    for component in components:
        comp_path = root / component
        if not comp_path.exists():
            issues.append(f"❌ Missing component directory: {component}")
            continue
            
        print(f"✅ Component directory: {component}")
        
        # Check for component README
        if not (comp_path / 'README.md').exists():
            issues.append(f"⚠️  Missing README in {component}")
        
        # Check for main files
        main_files = ['main.py', 'plannerChat.py']
        has_main = any((comp_path / main_file).exists() for main_file in main_files)
        
        if not has_main and component != 'lddemo':  # lddemo uses different structure
            issues.append(f"⚠️  No main application file found in {component}")
    
    # Check scripts directory
    scripts_path = root / 'scripts'
    if scripts_path.exists():
        print("✅ Scripts directory found")
        if not (scripts_path / 'generate_project_index.py').exists():
            issues.append("❌ Missing project index generator script")
        else:
            print("✅ Project index generator found")
    else:
        issues.append("❌ Missing scripts directory")
    
    # Report results
    if issues:
        print(f"\n🔍 Validation completed with {len(issues)} issues:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n🎉 Project structure validation passed!")
        return True

def main():
    """Main entry point."""
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"🔍 Validating project structure in: {project_root}")
    print("=" * 50)
    
    is_valid = validate_project_structure(project_root)
    
    if not is_valid:
        print("\n💡 Run 'make index' to regenerate the project index")
        print("💡 Check component README files for setup instructions")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()