#!/usr/bin/env python3
"""
Export ZeroWasteAI Context to Other Projects
Copies complete ZeroWasteAI context to any other project
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, Any

def export_zerowaste_context(target_project_path: str) -> Dict[str, Any]:
    """
    Export complete ZeroWasteAI context to another project
    """
    
    # Current ZeroWasteAI project path
    zerowaste_path = Path(__file__).parent.resolve()
    target_path = Path(target_project_path).resolve()
    
    if not target_path.exists():
        return {"error": f"Target project path does not exist: {target_project_path}"}
    
    # Files to copy for complete ZeroWasteAI context
    context_files = [
        "mcp_server.py",        # Complete ZeroWasteAI MCP server
        "mcp.json",             # Cursor configuration
        "setup_mcp.py",         # Setup script
        "CURSOR_MCP_SETUP.md"   # Documentation
    ]
    
    results = {
        "target_project": str(target_path),
        "copied_files": [],
        "errors": [],
        "success": True
    }
    
    try:
        # Copy context files
        for file_name in context_files:
            source_file = zerowaste_path / file_name
            target_file = target_path / file_name
            
            if source_file.exists():
                shutil.copy2(source_file, target_file)
                results["copied_files"].append(file_name)
                print(f"✅ Copied {file_name}")
            else:
                results["errors"].append(f"Source file not found: {file_name}")
                print(f"❌ Missing {file_name}")
        
        # Create custom configuration for target project
        target_config = {
            "name": target_path.name,
            "zerowaste_context_source": str(zerowaste_path),
            "setup_date": "2024-06-21",
            "context_type": "complete_zerowaste_backend",
            "features": [
                "58 ZeroWasteAI API endpoints",
                "Clean Architecture patterns",
                "Firebase + JWT authentication",
                "AI food recognition context",
                "Complete database models",
                "Business logic use cases",
                "Swagger documentation"
            ]
        }
        
        config_file = target_path / "zerowaste_context.json"
        with open(config_file, 'w') as f:
            json.dump(target_config, f, indent=2)
        
        results["copied_files"].append("zerowaste_context.json")
        print(f"✅ Created configuration: zerowaste_context.json")
        
        # Create setup instructions
        instructions = f"""
# ZeroWasteAI Context Setup for {target_path.name}

## What was exported:
- Complete ZeroWasteAI MCP server with 58 endpoints
- Clean Architecture context and patterns
- Firebase + JWT authentication patterns
- AI integration context
- Database models and use cases
- Swagger documentation patterns

## Setup Instructions:

1. **Install MCP dependencies:**
   ```bash
   pip install mcp
   ```

2. **Run the setup:**
   ```bash
   python setup_mcp.py
   ```

3. **Verify in Cursor:**
   - Restart Cursor
   - Check MCP connection in status bar
   - Access ZeroWasteAI context via MCP

## Context Available:
- 🏗️ Complete Clean Architecture structure
- 🔐 Authentication & security patterns
- 🤖 AI integration examples
- 📊 Database design patterns
- 📚 API documentation standards
- 🧪 Testing approaches

Your project now has access to the complete ZeroWasteAI backend context!
"""
        
        readme_file = target_path / "ZEROWASTE_CONTEXT_README.md"
        with open(readme_file, 'w') as f:
            f.write(instructions)
        
        results["copied_files"].append("ZEROWASTE_CONTEXT_README.md")
        print(f"✅ Created setup instructions: ZEROWASTE_CONTEXT_README.md")
        
        print(f"\n🎉 Successfully exported ZeroWasteAI context to: {target_path}")
        print(f"📁 Files copied: {len(results['copied_files'])}")
        print(f"🚀 Run 'python setup_mcp.py' in the target project to complete setup")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(str(e))
        print(f"❌ Error during export: {e}")
    
    return results

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python export_zerowaste_context.py <target_project_path>")
        print("Example: python export_zerowaste_context.py /path/to/my/other/project")
        sys.exit(1)
    
    target_project = sys.argv[1]
    result = export_zerowaste_context(target_project)
    
    if result["success"]:
        print(f"\n✅ Export completed successfully!")
        print(f"📋 Summary: {json.dumps(result, indent=2)}")
    else:
        print(f"\n❌ Export failed!")
        print(f"🔍 Errors: {result['errors']}")
        sys.exit(1)

if __name__ == "__main__":
    main() 