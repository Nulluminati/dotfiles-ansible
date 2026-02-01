---
name: python-uv
description: Comprehensive guide for Python development with UV, the ultra-fast Python package installer and resolver. Use when working with Python projects, dependency management, virtual environments, or application development using UV.
license: MIT
metadata:
  version: "1.0"
  category: "python"
  tags: ["python", "uv", "package-management", "virtual-environments", "dependency-management", "development"]
---

# Python UV Development Skill

## Overview

This skill provides comprehensive guidance for Python development using UV, Astral's ultra-fast Python package installer and resolver. UV is written in Rust and offers 10-100x faster dependency management compared to traditional tools like pip and poetry. Use this skill when you need to create Python projects, manage dependencies, work with virtual environments, or optimize Python development workflows.

## When to Use This Skill

- **Starting new Python projects** - Creating project structure with pyproject.toml
- **Dependency management** - Adding, updating, and resolving Python packages
- **Virtual environment management** - Creating and managing Python environments
- **Script development** - Working with single-file Python scripts and PEP 723
- **CLI tool management** - Installing and managing Python command-line tools
- **Python version management** - Managing multiple Python versions
- **Development workflow optimization** - Fast, efficient Python development cycles
- **CI/CD pipeline setup** - Integrating UV into automated workflows

---

# 🚀 UV Python Workflow Guide

## Phase 1: Project Setup and Initialization

### 1.1 Create New Python Projects

**Standard Project Creation:**
```bash
# Create a new Python project with UV
uv init my-project
cd my-project

# Creates:
# - my-project/
#   ├── .venv/           # Virtual environment
#   ├── pyproject.toml   # Project configuration
#   └── uv.lock          # Dependency lockfile
```

**Project with Specific Structure:**
```bash
# Create project with custom structure
uv init my-project --app
# or
uv init my-project --lib

# Initialize with specific Python version
uv init my-project --python 3.11

# Initialize in existing directory
cd existing-project
uv init
```

### 1.2 Configure pyproject.toml

**Basic Configuration:**
```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "A sample Python project"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1.0",
    "black>=23.0",
    "mypy>=1.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/my-project"
Repository = "https://github.com/yourusername/my-project"
Issues = "https://github.com/yourusername/my-project/issues"

[project.scripts]
my-cli = "my_project.cli:main"

[tool.ruff]
line-length = 88
target-version = "py38"

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 1.3 Initialize Git Repository

```bash
# Initialize git after project creation
git init
echo "*.pyc\n__pycache__/\n.pytest_cache/\n.coverage\ndist/\nbuild/\n*.egg-info/" > .gitignore
git add .
git commit -m "Initial project setup"
```

---

## Phase 2: Dependency Management

### 2.1 Add Dependencies

**Add Production Dependencies:**
```bash
# Add single dependency
uv add requests

# Add specific version
uv add requests==2.31.0

# Add with version constraint
uv add "requests>=2.30.0,<3.0.0"

# Add multiple dependencies
uv add requests fastapi uvicorn

# Add from git repository
uv add "git+https://github.com/psf/requests.git"

# Add from local path
uv add ./local-package

# Add from URL
uv add https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz
```

**Add Development Dependencies:**
```bash
# Add to dev dependencies group
uv add --dev pytest
uv add --group dev ruff black mypy

# Create custom dependency groups
uv add --group test pytest pytest-cov
uv add --group lint ruff black isort
uv add --group docs sphinx mkdocs
```

**Optional Dependencies:**
```bash
# Add optional dependencies
uv add --optional redis celery
uv add --optional matplotlib seaborn --group plotting
```

### 2.2 Manage Dependencies

**Update Dependencies:**
```bash
# Update all dependencies
uv lock --upgrade

# Update specific dependency
uv add requests@latest

# Update dependency group
uv sync --group dev --upgrade

# Update lockfile only
uv lock
```

**Remove Dependencies:**
```bash
# Remove dependency
uv remove requests

# Remove from specific group
uv remove pytest --group dev

# Remove multiple dependencies
uv remove requests fastapi uvicorn
```

**View Dependencies:**
```bash
# Show installed packages
uv pip list

# Show dependency tree
uv pip show requests

# Show outdated packages
uv pip list --outdated

# Export requirements
uv pip freeze > requirements.txt
```

### 2.3 Dependency Resolution and Locking

**Lock Dependencies:**
```bash
# Generate/refresh lockfile
uv lock

# Lock with specific Python version
uv lock --python 3.11

# Lock for specific platform
uv lock --resolution=highest

# Check lockfile consistency
uv sync --locked
```

**Dependency Resolution Strategies:**
```bash
# Highest compatible versions (default)
uv add package-name

# Lowest compatible versions
uv add package-name --resolution=lowest-direct

# Re-resolve dependencies
uv sync --reinstall
```

---

## Phase 3: Virtual Environment Management

### 3.1 Create and Manage Virtual Environments

**Automatic Environment Creation:**
```bash
# UV automatically creates .venv when needed
uv run python script.py

# Create environment explicitly
uv venv

# Create with specific Python version
uv venv --python 3.11

# Create environment in custom location
uv venv /path/to/custom/venv
```

**Environment Configuration:**
```bash
# Set Python version for project
uv python pin 3.11

# Use specific Python version
uv run --python 3.10 script.py

# Check available Python versions
uv python list

# Install Python versions
uv python install 3.11 3.12
```

### 3.2 Activate and Use Environments

**Traditional Activation:**
```bash
# Activate environment (traditional)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

**UV-style Usage (Recommended):**
```bash
# Run commands in environment without explicit activation
uv run python script.py
uv run pytest
uv run ruff check .

# Run with temporary dependencies
uv run --with requests python script.py
uv run --with pytest --with pytest-cov pytest

# Run with specific Python version
uv run --python 3.11 script.py
```

### 3.3 Environment Management

**Environment Information:**
```bash
# Show current environment info
uv venv --help

# Check if in active environment
uv run python -c "import sys; print(sys.prefix)"

# Show environment packages
uv pip list
uv pip show package-name
```

**Environment Cleanup:**
```bash
# Remove virtual environment
rm -rf .venv

# Recreate clean environment
rm -rf .venv && uv venv && uv sync
```

---

## Phase 4: Script Development

### 4.1 Single File Scripts (PEP 723)

**Create Self-Contained Scripts:**
```python
# script.py - UV automatically handles dependencies
# /// pyproject
# [project]
# name = "my-script"
# version = "0.1.0"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///

import requests
from rich import print

def fetch_data(url: str) -> dict:
    """Fetch data from URL and return JSON response."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def main():
    """Main script function."""
    url = "https://api.github.com/repos/astral-sh/uv"
    data = fetch_data(url)

    print(f"[bold green]Repository:[/bold green] {data['name']}")
    print(f"[bold blue]Stars:[/bold blue] {data['stargazers_count']}")
    print(f"[bold yellow]Language:[/bold yellow] {data['language']}")

if __name__ == "__main__":
    main()
```

**Run Scripts:**
```bash
# Run script (UV automatically installs dependencies)
uv run script.py

# Run with additional dependencies
uv run --with beautifulsoup4 script.py

# Run script with specific Python version
uv run --python 3.11 script.py

# Install script dependencies globally
uv add --script script.py requests rich
uv run script.py
```

### 4.2 Advanced Script Features

**Script with CLI Arguments:**
```python
# cli_script.py
# /// pyproject
# [project]
# name = "cli-tool"
# version = "0.1.0"
# dependencies = [
#     "click",
#     "rich",
# ]
# scripts = {cli-tool = "cli_script:main"}
# ///

import click
from rich.console import Console
from rich.table import Table

@click.command()
@click.option('--format', default='table', help='Output format')
@click.argument('url')
def main(format, url):
    """Fetch and display data from URL."""
    import requests

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if format == 'table':
            console = Console()
            table = Table(title="API Response")

            for key, value in data.items():
                table.add_row(str(key), str(value))

            console.print(table)
        else:
            print(data)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    main()
```

### 4.3 Script Distribution

**Make Scripts Executable:**
```bash
# Make script executable
chmod +x script.py

# Add shebang for direct execution
echo '#!/usr/bin/env uv run' > script.py
echo '# Your script content' >> script.py

# Direct execution
./script.py
```

---

## Phase 5: Testing and Development

### 5.1 Development Workflow

**Run Tests:**
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_module.py

# Run with verbose output
uv run pytest -v

# Run tests with specific marker
uv run pytest -m "unit"
uv run pytest -m "integration"
```

**Code Quality:**
```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy src/

# Run all quality checks
uv run ruff check . && uv run mypy src/ && uv run pytest
```

### 5.2 Test Configuration

**pytest.ini Configuration:**
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --verbose
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    network: Tests that require network access
```

**Test Structure:**
```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/
│   ├── test_module1.py
│   └── test_module2.py
├── integration/
│   ├── test_api.py
│   └── test_database.py
└── fixtures/
    ├── data.json
    └── sample.txt
```

### 5.3 Pre-commit Hooks

**Setup Pre-commit:**
```bash
# Add pre-commit to development dependencies
uv add --dev pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
EOF

# Install pre-commit hooks
uv run pre-commit install
```

---

## Phase 6: CLI Tool Management

### 6.1 Install and Use CLI Tools

**Ephemeral Tool Usage:**
```bash
# Use tools without installation
uvx ruff check .
uvx black src/
uvx mypy src/
uvx pytest

# Use with specific versions
uvx ruff==0.1.0 check .
uvx black==23.0.0 src/

# Use with additional dependencies
uvx --with jupyter jupyter notebook
```

**Persistent Tool Installation:**
```bash
# Install tools globally
uv tool install ruff
uv tool install black
uv tool install mypy
uv tool install pytest

# List installed tools
uv tool list

# Update tools
uv tool update --all
uv tool update ruff

# Uninstall tools
uv tool uninstall ruff

# Run installed tools
ruff check .
black src/
```

### 6.2 Tool Management

**Tool Version Management:**
```bash
# Install specific version
uv tool install ruff==0.1.0

# Install from git
uv tool install "git+https://github.com/psf/black.git"

# Install from local path
uv tool install ./my-tool

# Tool with dependencies
uv tool install --with requests httpie
```

---

## Phase 7: Advanced Usage

### 7.1 Performance Optimization

**UV Performance Settings:**
```bash
# Increase concurrent downloads
export UV_CONCURRENT_DOWNLOADS=16

# Increase concurrent installs
export UV_CONCURRENT_INSTALLS=8

# Use offline mode
export UV_OFFLINE=1

# Use custom index
export UV_INDEX_URL=https://pypi.example.com/simple/

# Disable colors
export UV_NO_COLOR=1

# Set cache directory
export UV_CACHE_DIR=/path/to/cache
```

**Cache Management:**
```bash
# Show cache information
uv cache info

# Show cache directory
uv cache dir

# Clean cache
uv cache clean

# Clean specific package from cache
uv cache clean --package requests
```

### 7.2 Offline and Air-gapped Usage

**Offline Package Installation:**
```bash
# Download packages for offline use
uv pip download -r requirements.txt -d ./wheels/

# Install from local wheels
uv pip install --no-index --find-links=./wheels/ -r requirements.txt

# Sync from lockfile offline
uv sync --offline
```

### 7.3 Cross-platform Development

**Platform-specific Dependencies:**
```bash
# Add platform-specific dependencies
uv add "pywin32; sys_platform == 'win32'"
uv add "uvloop; sys_platform != 'win32'"

# Sync for specific platform
uv sync --resolution=highest
```

---

## Phase 8: CI/CD Integration

### 8.1 GitHub Actions

**Complete CI Workflow:**
```yaml
# .github/workflows/python.yml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up UV
      uses: astral-sh/setup-uv@v5
      with:
        enable-cache: true
        cache-dependency-glob: "uv.lock"

    - name: Install Python
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: uv sync --locked

    - name: Run linting
      run: uv run ruff check .

    - name: Run type checking
      run: uv run mypy src/

    - name: Run tests
      run: uv run pytest --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Set up UV
      uses: astral-sh/setup-uv@v5
      with:
        enable-cache: true
        cache-dependency-glob: "uv.lock"

    - name: Build package
      run: uv build

    - name: Publish to PyPI
      if: startsWith(github.ref, 'refs/tags/')
      run: uv publish --token ${{ secrets.PYPI_TOKEN }}
```

### 8.2 Docker Integration

**Multi-stage Dockerfile:**
```dockerfile
# Dockerfile
FROM ghcr.io/astral-sh/uv:0.7.4 AS uv

# Build stage
FROM python:3.11-slim AS builder
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Application stage
FROM python:3.11-slim AS runtime
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

WORKDIR /app
COPY . .

# Run application
CMD ["uv", "run", "python", "-m", "myapp"]
```

### 8.3 Development Container

**devcontainer.json:**
```json
{
  "name": "Python UV",
  "image": "ghcr.io/astral-sh/uv:latest",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff",
        "ms-python.mypy-type-checker"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/opt/uv/.venv/bin/python",
        "python.linting.enabled": true,
        "python.linting.ruffEnabled": true
      }
    }
  },
  "postCreateCommand": "uv sync"
}
```

---

## Phase 9: Troubleshooting and Debugging

### 9.1 Common Issues

**Dependency Resolution Failures:**
```bash
# Clear cache and retry
uv cache clean
uv sync

# Check conflicting dependencies
uv add package-name --verbose

# Force re-resolution
uv sync --reinstall

# Check dependency graph
uv pip show package-name
```

**Environment Issues:**
```bash
# Recreate environment
rm -rf .venv
uv venv
uv sync

# Check Python version compatibility
uv python list
uv python pin 3.11

# Check platform compatibility
uv sync --resolution=highest
```

**Network Issues:**
```bash
# Use different index
uv sync --index-url https://pypi.org/simple/

# Increase timeout
export UV_HTTP_TIMEOUT=120
uv sync

# Use offline mode if cache is available
uv sync --offline
```

### 9.2 Debugging Commands

**Verbose Output:**
```bash
# Run with verbose output
uv sync --verbose
uv add requests --verbose

# Show resolution details
uv lock --resolution=highest --verbose

# Debug environment issues
uv run python -c "import sys; print(sys.path)"
uv run python -c "import sys; print(sys.executable)"
```

### 9.3 Performance Monitoring

**Monitor UV Performance:**
```bash
# Time UV operations
time uv sync
time uv add requests

# Check cache usage
uv cache info
du -sh $(uv cache dir)

# Monitor concurrent operations
export UV_CONCURRENT_DOWNLOADS=32
export UV_CONCURRENT_INSTALLS=16
```

---

# 📚 Reference Materials

## Essential UV Commands

**Project Management:**
- `uv init <name>` - Create new Python project
- `uv add <package>` - Add dependency
- `uv remove <package>` - Remove dependency
- `uv sync` - Install dependencies from lockfile
- `uv lock` - Generate/update lockfile

**Virtual Environments:**
- `uv venv` - Create virtual environment
- `uv run <command>` - Run command in environment
- `uv run --with <dep> <command>` - Run with temporary dependency

**Script Development:**
- `uv run script.py` - Run Python script
- `uv add --script script.py <deps>` - Add script dependencies
- `uvx <tool>` - Run tool without installation

**CLI Tools:**
- `uv tool install <package>` - Install CLI tool
- `uv tool list` - List installed tools
- `uv tool uninstall <package>` - Uninstall tool

**Python Management:**
- `uv python list` - List available Python versions
- `uv python install <version>` - Install Python version
- `uv python pin <version>` - Pin Python version for project

**Cache Management:**
- `uv cache info` - Show cache information
- `uv cache clean` - Clear cache
- `uv cache dir` - Show cache directory

## Performance Optimization Checklist

- [ ] Enable concurrent downloads and installs
- [ ] Use offline mode when possible
- [ ] Configure appropriate cache directory
- [ ] Use lockfile for reproducible builds
- [ ] Pin Python versions for consistency
- [ ] Use `uv sync --locked` in CI/CD
- [ ] Clean cache periodically to free space

## Best Practices

- [ ] Always commit `uv.lock` to version control
- [ ] Use dependency groups for development dependencies
- [ ] Prefer `uv run` over manual environment activation
- [ ] Use PEP 723 for self-contained scripts
- [ ] Configure pre-commit hooks for code quality
- [ ] Use semantic versioning for dependencies
- [ ] Regularly update dependencies for security
- [ ] Use `uvx` for one-off tool usage

## Migration from Other Tools

**From pip:**
```bash
# Old: pip install -r requirements.txt
# New: uv sync

# Old: pip install package
# New: uv add package

# Old: pip freeze > requirements.txt
# New: uv pip freeze > requirements.txt
```

**From poetry:**
```bash
# Old: poetry new project
# New: uv init project

# Old: poetry add package
# New: uv add package

# Old: poetry install
# New: uv sync

# Old: poetry run command
# New: uv run command
```

**From pipenv:**
```bash
# Old: pipenv install package
# New: uv add package

# Old: pipenv sync
# New: uv sync

# Old: pipenv run command
# New: uv run command
```

This comprehensive UV Python skill provides everything needed for modern Python development, from project setup to advanced CI/CD integration and troubleshooting. The ultra-fast performance of UV combined with these workflows will significantly accelerate your Python development process.