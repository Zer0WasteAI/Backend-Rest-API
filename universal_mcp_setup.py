#!/usr/bin/env python3
"""
Universal MCP Setup Script
Configures MCP server for any Python project in Cursor
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import argparse

def install_mcp_dependencies():
    """Install MCP dependencies"""
    print("🔧 Installing MCP dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "mcp>=1.0.0", "typing-extensions>=4.0.0"
        ])
        print("✅ MCP dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing MCP dependencies: {e}")
        return False

def copy_mcp_files(target_project_path: Path, source_path: Path = None):
    """Copy MCP server files to target project"""
    print(f"📁 Copying MCP files to {target_project_path}...")
    
    if source_path is None:
        source_path = Path(__file__).parent
    
    # Files to copy
    files_to_copy = [
        "generic_mcp_server.py",
        "requirements-mcp.txt"
    ]
    
    for file_name in files_to_copy:
        source_file = source_path / file_name
        target_file = target_project_path / file_name
        
        if source_file.exists():
            try:
                shutil.copy2(source_file, target_file)
                print(f"✅ Copied {file_name}")
            except Exception as e:
                print(f"❌ Error copying {file_name}: {e}")
                return False
        else:
            print(f"⚠️  Source file not found: {file_name}")
    
    return True

def create_project_mcp_config(project_path: Path, project_name: str = None):
    """Create MCP configuration for specific project"""
    if project_name is None:
        project_name = project_path.name
    
    config = {
        "mcpServers": {
            f"{project_name}-mcp": {
                "command": "python",
                "args": ["generic_mcp_server.py"],
                "cwd": str(project_path.absolute()),
                "env": {
                    "PYTHONPATH": str(project_path.absolute())
                }
            }
        }
    }
    
    config_file = project_path / "mcp_config.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created MCP config: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating MCP config: {e}")
        return False

def update_cursor_global_config(project_configs: list):
    """Update Cursor's global configuration with multiple projects"""
    print("📝 Updating Cursor global configuration...")
    
    # Cursor config path (varies by OS)
    if sys.platform == "darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "Cursor" / "User"
    elif sys.platform == "win32":  # Windows
        config_dir = Path.home() / "AppData" / "Roaming" / "Cursor" / "User"
    else:  # Linux
        config_dir = Path.home() / ".config" / "Cursor" / "User"
    
    config_file = config_dir / "settings.json"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing settings or create new
    settings = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Existing settings.json is invalid, creating new one")
    
    # Add MCP configuration
    if "mcp.servers" not in settings:
        settings["mcp.servers"] = {}
    
    # Add all project configurations
    for project_config in project_configs:
        settings["mcp.servers"].update(project_config["mcpServers"])
    
    # Save updated settings
    try:
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✅ Cursor configuration updated: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Error updating Cursor config: {e}")
        return False

def setup_project(project_path: Path, project_name: str = None):
    """Setup MCP for a single project"""
    print(f"🚀 Setting up MCP for project: {project_path}")
    
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        return False
    
    if project_name is None:
        project_name = project_path.name
    
    success = True
    
    # Step 1: Copy MCP files
    if not copy_mcp_files(project_path):
        success = False
    
    # Step 2: Create project-specific config
    if not create_project_mcp_config(project_path, project_name):
        success = False
    
    return success

def discover_python_projects(search_path: Path, max_depth: int = 2) -> list:
    """Discover Python projects in a directory"""
    print(f"🔍 Discovering Python projects in: {search_path}")
    
    projects = []
    
    def scan_directory(path: Path, current_depth: int = 0):
        if current_depth >= max_depth:
            return
        
        # Check if current directory is a Python project
        python_indicators = [
            "requirements.txt", "setup.py", "pyproject.toml", 
            "main.py", "app.py", "manage.py"
        ]
        
        has_python_files = any((path / indicator).exists() for indicator in python_indicators)
        has_py_files = any(path.glob("*.py"))
        
        if has_python_files or has_py_files:
            projects.append({
                "path": path,
                "name": path.name,
                "indicators": [ind for ind in python_indicators if (path / ind).exists()]
            })
        
        # Recursively check subdirectories
        try:
            for subdir in path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.') and subdir.name not in ['venv', '__pycache__', 'node_modules']:
                    scan_directory(subdir, current_depth + 1)
        except PermissionError:
            pass
    
    scan_directory(search_path)
    return projects

def create_setup_guide(target_path: Path):
    """Create a setup guide for the project"""
    guide_content = f"""# MCP Setup Guide for {target_path.name}

## 🚀 MCP Server Configured!

Your project now has a generic MCP server that provides context to Cursor.

## Files Added:
- `generic_mcp_server.py` - Universal MCP server
- `requirements-mcp.txt` - MCP dependencies
- `mcp_config.json` - Project-specific configuration
- `MCP_SETUP_GUIDE.md` - This guide

## What the MCP Server Provides:
1. **Project Info** - Automatic detection of framework (Flask, Django, FastAPI)
2. **Project Structure** - Complete file tree analysis
3. **Python Analysis** - Classes, functions, imports in all .py files
4. **Dependencies** - Requirements and package analysis
5. **Entry Points** - Main files and executable scripts

## Tools Available:
- `analyze_file` - Analyze any file in the project
- `search_code` - Search patterns across the codebase
- `get_project_summary` - Comprehensive project overview

## Usage with Cursor:
1. **Restart Cursor** completely
2. The MCP server will activate automatically
3. Ask Cursor questions like:
   - "What type of project is this?"
   - "Show me the project structure"
   - "What are the main entry points?"
   - "Analyze the main.py file"
   - "Search for all Flask routes"

## Manual Testing:
```bash
# Test the MCP server
python generic_mcp_server.py

# Install dependencies if needed
pip install -r requirements-mcp.txt
```

## Configuration:
The MCP server is configured in Cursor's settings.json as:
```json
{{
  "mcp.servers": {{
    "{target_path.name}-mcp": {{
      "command": "python",
      "args": ["generic_mcp_server.py"],
      "cwd": "{target_path.absolute()}",
      "env": {{
        "PYTHONPATH": "{target_path.absolute()}"
      }}
    }}
  }}
}}
```

## Supported Project Types:
- ✅ Flask applications
- ✅ Django projects  
- ✅ FastAPI applications
- ✅ General Python projects
- ✅ Python packages
- ✅ Any project with .py files

Enjoy enhanced AI assistance with complete project context! 🎉
"""
    
    guide_file = target_path / "MCP_SETUP_GUIDE.md"
    try:
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        print(f"✅ Created setup guide: {guide_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating setup guide: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Universal MCP Setup for Python Projects")
    parser.add_argument("--project", "-p", type=str, help="Path to specific project")
    parser.add_argument("--discover", "-d", type=str, help="Discover projects in directory")
    parser.add_argument("--install-deps", "-i", action="store_true", help="Install MCP dependencies")
    parser.add_argument("--max-depth", type=int, default=2, help="Max depth for project discovery")
    
    args = parser.parse_args()
    
    print("🚀 Universal MCP Setup for Python Projects")
    print("=" * 50)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_mcp_dependencies():
            sys.exit(1)
    
    project_configs = []
    
    if args.project:
        # Setup specific project
        project_path = Path(args.project).resolve()
        if setup_project(project_path):
            # Load the created config
            config_file = project_path / "mcp_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    project_configs.append(json.load(f))
            
            create_setup_guide(project_path)
            print(f"✅ MCP setup completed for: {project_path}")
        else:
            print(f"❌ Failed to setup MCP for: {project_path}")
            sys.exit(1)
    
    elif args.discover:
        # Discover and setup multiple projects
        search_path = Path(args.discover).resolve()
        projects = discover_python_projects(search_path, args.max_depth)
        
        if not projects:
            print(f"❌ No Python projects found in: {search_path}")
            sys.exit(1)
        
        print(f"📋 Found {len(projects)} Python projects:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project['name']} ({project['path']})")
            print(f"     Indicators: {', '.join(project['indicators'])}")
        
        # Ask user which projects to setup
        response = input("\nSetup MCP for all projects? (y/n/select): ").lower()
        
        if response == 'y':
            selected_projects = projects
        elif response == 'select':
            selected_indices = input("Enter project numbers (comma-separated): ")
            try:
                indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
                selected_projects = [projects[i] for i in indices if 0 <= i < len(projects)]
            except (ValueError, IndexError):
                print("❌ Invalid selection")
                sys.exit(1)
        else:
            print("❌ Setup cancelled")
            sys.exit(0)
        
        # Setup selected projects
        for project in selected_projects:
            if setup_project(project['path'], project['name']):
                # Load the created config
                config_file = project['path'] / "mcp_config.json"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        project_configs.append(json.load(f))
                
                create_setup_guide(project['path'])
                print(f"✅ MCP setup completed for: {project['name']}")
            else:
                print(f"❌ Failed to setup MCP for: {project['name']}")
    
    else:
        # Setup current directory
        current_path = Path.cwd()
        if setup_project(current_path):
            # Load the created config
            config_file = current_path / "mcp_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    project_configs.append(json.load(f))
            
            create_setup_guide(current_path)
            print(f"✅ MCP setup completed for current directory: {current_path}")
        else:
            print(f"❌ Failed to setup MCP for current directory")
            sys.exit(1)
    
    # Update Cursor global configuration
    if project_configs:
        if update_cursor_global_config(project_configs):
            print("\n🎉 Universal MCP Setup completed successfully!")
            print(f"📊 Configured {len(project_configs)} project(s)")
            print("\n📋 Next steps:")
            print("1. Restart Cursor completely")
            print("2. MCP servers will activate automatically for each project")
            print("3. Check MCP_SETUP_GUIDE.md in each project for usage")
            print("\n🔍 Test by asking Cursor about your project structure!")
        else:
            print("❌ Failed to update Cursor configuration")
            sys.exit(1)
    else:
        print("❌ No projects were successfully configured")
        sys.exit(1)

if __name__ == "__main__":
    main() 