#!/usr/bin/env python3
"""
Project Index Generator for QE-AI-Agent-Swarm

This script automatically generates and updates the PROJECT_INDEX.md file
by analyzing the codebase structure, dependencies, and documentation.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import subprocess
import sys

class ProjectIndexer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.timestamp = datetime.now().strftime("%B %d, %Y")
        
    def count_files(self) -> Dict[str, int]:
        """Count various file types in the project."""
        stats = {}
        
        # Total files
        result = subprocess.run(['find', str(self.project_root), '-type', 'f'], 
                              capture_output=True, text=True)
        stats['total_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Files excluding virtual environments and caches
        result = subprocess.run([
            'find', str(self.project_root), '-type', 'f',
            '-not', '-path', '*/mcpagent/*',
            '-not', '-path', '*/__pycache__/*',
            '-not', '-path', '*/node_modules/*'
        ], capture_output=True, text=True)
        stats['relevant_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Python files
        result = subprocess.run([
            'find', str(self.project_root), '-type', 'f', '-name', '*.py',
            '-not', '-path', '*/mcpagent/*',
            '-not', '-path', '*/__pycache__/*'
        ], capture_output=True, text=True)
        stats['python_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Markdown files
        result = subprocess.run([
            'find', str(self.project_root), '-type', 'f', '-name', '*.md'
        ], capture_output=True, text=True)
        stats['markdown_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # YAML files
        result = subprocess.run([
            'find', str(self.project_root), '-type', 'f', '-name', '*.yaml', '-o', '-name', '*.yml'
        ], capture_output=True, text=True)
        stats['yaml_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # JSON files
        result = subprocess.run([
            'find', str(self.project_root), '-type', 'f', '-name', '*.json'
        ], capture_output=True, text=True)
        stats['json_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Docker files
        docker_files = 0
        for pattern in ['Dockerfile', 'dockerfile', 'docker-compose*.yml', 'docker-compose*.yaml']:
            result = subprocess.run([
                'find', str(self.project_root), '-type', 'f', '-name', pattern
            ], capture_output=True, text=True)
            if result.stdout.strip():
                docker_files += len(result.stdout.strip().split('\n'))
        stats['docker_files'] = docker_files
        
        return stats
    
    def get_git_info(self) -> Dict[str, str]:
        """Get git repository information."""
        git_info = {}
        
        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  cwd=self.project_root, capture_output=True, text=True)
            git_info['branch'] = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            # Get remote origin URL
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                url = result.stdout.strip()
                if url.startswith('git@github.com:'):
                    repo_path = url.replace('git@github.com:', '').replace('.git', '')
                elif url.startswith('https://github.com/'):
                    repo_path = url.replace('https://github.com/', '').replace('.git', '')
                else:
                    repo_path = 'unknown'
                git_info['repo'] = repo_path
            else:
                git_info['repo'] = 'unknown'
                
        except Exception:
            git_info['branch'] = 'unknown'
            git_info['repo'] = 'unknown'
            
        return git_info
    
    def analyze_components(self) -> Dict[str, Dict]:
        """Analyze each component directory."""
        components = {}
        
        component_dirs = ['monolith', 'planner', 'research', 'lddemo']
        
        for comp_dir in component_dirs:
            comp_path = self.project_root / comp_dir
            if comp_path.exists():
                components[comp_dir] = self._analyze_component(comp_path)
                
        return components
    
    def _analyze_component(self, comp_path: Path) -> Dict:
        """Analyze a single component directory."""
        analysis = {
            'path': str(comp_path),
            'exists': comp_path.exists(),
            'files': [],
            'dependencies': [],
            'config_files': [],
            'documentation': [],
            'docker_files': []
        }
        
        if not comp_path.exists():
            return analysis
            
        # List important files
        for file_pattern in ['*.py', '*.md', '*.yaml', '*.yml', '*.json', 'Dockerfile*', 'docker-compose*', 'requirements.txt', 'pyproject.toml']:
            for file_path in comp_path.rglob(file_pattern):
                # Skip virtual environments and caches
                if any(skip in str(file_path) for skip in ['mcpagent', '__pycache__', 'node_modules']):
                    continue
                    
                relative_path = file_path.relative_to(comp_path)
                
                if file_path.suffix == '.py':
                    analysis['files'].append(str(relative_path))
                elif file_path.suffix == '.md':
                    analysis['documentation'].append(str(relative_path))
                elif file_path.suffix in ['.yaml', '.yml', '.json']:
                    analysis['config_files'].append(str(relative_path))
                elif 'docker' in file_path.name.lower() or file_path.name == 'Dockerfile':
                    analysis['docker_files'].append(str(relative_path))
                elif file_path.name in ['requirements.txt', 'pyproject.toml']:
                    analysis['dependencies'].append(str(relative_path))
        
        return analysis
    
    def read_main_readme(self) -> str:
        """Read the main README file for project description."""
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            try:
                return readme_path.read_text(encoding='utf-8')
            except Exception:
                return ""
        return ""
    
    def generate_index(self) -> str:
        """Generate the complete project index."""
        stats = self.count_files()
        git_info = self.get_git_info()
        components = self.analyze_components()
        
        # Extract repository name and owner from git info
        repo_parts = git_info.get('repo', 'unknown/unknown').split('/')
        owner = repo_parts[0] if len(repo_parts) > 0 else 'unknown'
        repo_name = repo_parts[1] if len(repo_parts) > 1 else 'unknown'
        
        index_content = f"""# {repo_name.upper()} - Project Index

**Generated on**: {self.timestamp}  
**Repository**: {repo_name}  
**Owner**: {owner}  
**Branch**: {git_info.get('branch', 'unknown')}

## 📊 Project Statistics

- **Total Files**: {stats.get('total_files', 0):,} ({stats.get('relevant_files', 0):,} excluding virtual environments/caches)
- **Python Files**: {stats.get('python_files', 0)} main application files
- **Documentation Files**: {stats.get('markdown_files', 0)} Markdown files
- **Configuration Files**: {stats.get('yaml_files', 0)} YAML files, {stats.get('json_files', 0)} JSON files
- **Container Files**: {stats.get('docker_files', 0)} Docker-related files

## 🏗️ Project Structure

### Component Analysis

"""
        
        for comp_name, comp_data in components.items():
            if comp_data['exists']:
                index_content += f"""#### {comp_name.title()} Component
- **Location**: `/{comp_name}/`
- **Python Files**: {len(comp_data['files'])}
- **Documentation**: {len(comp_data['documentation'])}
- **Configuration**: {len(comp_data['config_files'])}
- **Dependencies**: {len(comp_data['dependencies'])}
- **Docker Files**: {len(comp_data['docker_files'])}

"""
        
        index_content += f"""
## 📁 Directory Listing

```
{repo_name}/
"""
        
        # Generate directory tree
        for item in sorted(self.project_root.iterdir()):
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['__pycache__', 'mcpagent']:
                index_content += f"├── {item.name}/\n"
                # Add some key files for each directory
                for subitem in sorted(item.iterdir())[:5]:  # Limit to first 5 items
                    if subitem.is_file() and not subitem.name.startswith('.'):
                        index_content += f"│   ├── {subitem.name}\n"
                    elif subitem.is_dir() and not subitem.name.startswith('.'):
                        index_content += f"│   ├── {subitem.name}/\n"
            elif item.is_file() and not item.name.startswith('.'):
                index_content += f"├── {item.name}\n"
        
        index_content += """```

## 🔧 Maintenance

This index was automatically generated. To update:

```bash
# Run the index generator
python scripts/generate_project_index.py

# Or add to your CI/CD pipeline
# The script analyzes the codebase and updates PROJECT_INDEX.md
```

## 📋 Component Details

For detailed information about each component, see their respective README files:

"""
        
        for comp_name, comp_data in components.items():
            if comp_data['exists'] and any('README.md' in doc for doc in comp_data['documentation']):
                index_content += f"- [`/{comp_name}/README.md`]({comp_name}/README.md) - {comp_name.title()} component documentation\n"
        
        index_content += f"""
---

*Auto-generated on {self.timestamp} by Project Index Generator*
*Last analysis: {stats.get('total_files', 0):,} total files, {stats.get('python_files', 0)} Python files*
"""
        
        return index_content

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    indexer = ProjectIndexer(project_root)
    
    try:
        index_content = indexer.generate_index()
        
        # Write to PROJECT_INDEX.md
        output_file = Path(project_root) / 'PROJECT_INDEX.md'
        output_file.write_text(index_content, encoding='utf-8')
        
        print(f"✅ Project index generated successfully: {output_file}")
        print(f"📊 Analysis complete - check {output_file.name} for details")
        
    except Exception as e:
        print(f"❌ Error generating project index: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()