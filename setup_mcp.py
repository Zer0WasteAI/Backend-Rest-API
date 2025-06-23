#!/usr/bin/env python3
"""
Setup script for ZeroWasteAI MCP Server
Configures the MCP server for use with Cursor and other AI assistants
"""

import json
import os
import subprocess
import sys
from pathlib import Path

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

def create_cursor_config():
    """Create or update Cursor configuration"""
    print("📝 Creating Cursor MCP configuration...")
    
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
    
    project_path = str(Path(__file__).parent.absolute())
    
    settings["mcp.servers"]["zerowaste-ai-backend"] = {
        "command": "python",
        "args": ["mcp_server.py"],
        "cwd": project_path,
        "env": {
            "PYTHONPATH": f"{project_path}/src"
        }
    }
    
    # Save updated settings
    try:
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✅ Cursor configuration updated: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Error updating Cursor config: {e}")
        return False

def test_mcp_server():
    """Test the MCP server"""
    print("🧪 Testing MCP server...")
    try:
        # Import and basic validation
        import mcp_server
        print("✅ MCP server module loads correctly")
        
        # Test context manager
        context = mcp_server.ZeroWasteBackendContext()
        structure = context.get_project_structure()
        
        if structure:
            print(f"✅ Project structure loaded: {len(structure)} items")
        else:
            print("⚠️  Project structure is empty")
            
        endpoints = context.get_api_endpoints()
        print(f"✅ Found {len(endpoints)} API endpoints")
        
        models = context.get_database_models()
        print(f"✅ Found {len(models)} database models")
        
        use_cases = context.get_use_cases()
        print(f"✅ Found {len(use_cases)} use cases")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing MCP server: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

def create_documentation():
    """Create MCP documentation"""
    print("📚 Creating MCP documentation...")
    
    doc_content = """# ZeroWasteAI MCP Server

## Overview
This MCP (Model Context Protocol) server provides complete context about the ZeroWasteAI backend to AI assistants like Cursor.

## Features
- **Project Structure**: Complete file tree and organization
- **API Endpoints**: All REST endpoints with methods and controllers
- **Database Models**: ORM models and schema information
- **Use Cases**: Business logic organized by domain
- **Configuration**: Project setup and dependencies
- **Architecture**: Clean Architecture pattern details
- **Documentation**: API specs and project docs

## Resources Available
1. `zerowaste://project-structure` - Complete file structure
2. `zerowaste://api-endpoints` - All API endpoints
3. `zerowaste://database-models` - Database schema
4. `zerowaste://use-cases` - Business logic use cases
5. `zerowaste://configuration` - Project configuration
6. `zerowaste://architecture` - Architecture overview
7. `zerowaste://documentation` - Project documentation

## Tools Available
1. `analyze_code_file` - Analyze specific code files
2. `search_code` - Search patterns in codebase
3. `get_api_documentation` - Get API documentation

## Usage with Cursor
Once configured, Cursor will automatically have access to your backend context through MCP.

## Manual Testing
To test the MCP server manually:

```bash
python mcp_server.py
```

## Configuration
The server is configured in Cursor's settings.json:

```json
{
  "mcp.servers": {
    "zerowaste-ai-backend": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/your/project",
      "env": {
        "PYTHONPATH": "/path/to/your/project/src"
      }
    }
  }
}
```

## Architecture Integration
This MCP server understands your Clean Architecture implementation:

- **Interface Layer**: Controllers, serializers, middlewares
- **Application Layer**: Use cases, services, factories  
- **Domain Layer**: Models, repositories, domain services
- **Infrastructure Layer**: Database, external services

## AI Features Exposed
- Firebase + JWT authentication system
- AI-powered food recognition
- Smart inventory management
- Recipe generation with AI
- Environmental impact calculations
- Asynchronous image processing
"""
    
    try:
        with open("MCP_README.md", "w") as f:
            f.write(doc_content)
        print("✅ MCP documentation created: MCP_README.md")
        return True
    except Exception as e:
        print(f"❌ Error creating documentation: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up ZeroWasteAI MCP Server for Cursor")
    print("=" * 50)
    
    success = True
    
    # Step 1: Install dependencies
    if not install_mcp_dependencies():
        success = False
    
    # Step 2: Create Cursor configuration
    if not create_cursor_config():
        success = False
    
    # Step 3: Test MCP server
    if not test_mcp_server():
        success = False
    
    # Step 4: Create documentation
    if not create_documentation():
        success = False
    
    print("=" * 50)
    if success:
        print("🎉 MCP Server setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Restart Cursor")
        print("2. The MCP server will provide context automatically")
        print("3. Check MCP_README.md for detailed usage")
        print("\n🔍 Test by asking Cursor about your backend architecture!")
    else:
        print("❌ Setup completed with errors. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 