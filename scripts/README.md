# Scripts Directory

This directory contains utility scripts for project maintenance and automation.

## Available Scripts

### `generate_project_index.py`

**Purpose**: Automatically generates and updates the `PROJECT_INDEX.md` file by analyzing the codebase structure.

**Usage**:
```bash
# Generate index for current directory
python3 scripts/generate_project_index.py

# Generate index for specific directory
python3 scripts/generate_project_index.py /path/to/project

# Or use the Makefile target
make index
```

**Features**:
- Counts files by type (Python, Markdown, YAML, JSON, Docker)
- Analyzes component structure and dependencies
- Extracts git repository information
- Generates directory tree visualization
- Creates detailed component analysis

**Output**: Updates `PROJECT_INDEX.md` with current project structure and statistics.

## Integration with CI/CD

The project index generator can be integrated into your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Update Project Index
  run: |
    python3 scripts/generate_project_index.py
    git add PROJECT_INDEX.md
    git commit -m "Auto-update project index" || exit 0
```

## Dependencies

The script uses only Python standard library modules:
- `os`, `sys` - System operations
- `pathlib` - Path handling
- `subprocess` - External command execution
- `datetime` - Timestamp generation
- `json` - JSON processing
- `typing` - Type hints

No additional packages required!

## Maintenance

This script is designed to be self-contained and maintainable. When adding new file types or analysis features:

1. Update the `count_files()` method for new file type counting
2. Extend `analyze_components()` for new component analysis
3. Modify `generate_index()` for new output sections
4. Test with `make index` or direct execution

## Error Handling

The script includes error handling for:
- Missing git repository
- File system access issues
- Command execution failures
- Missing directories or files

Errors are reported to stderr and the script exits with code 1.