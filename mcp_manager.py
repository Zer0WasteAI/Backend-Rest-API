#!/usr/bin/env python3
"""
MCP Configuration Manager
Manage multiple MCP server configurations for ZeroWasteAI
"""

import json
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

class MCPManager:
    """Manage MCP server configurations"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.config_file = self.base_path / "mcp.json"
        self.cursor_settings = self._get_cursor_settings_path()
        
    def _get_cursor_settings_path(self) -> Path:
        """Get Cursor settings.json path"""
        home = Path.home()
        
        # macOS
        if sys.platform == "darwin":
            return home / "Library/Application Support/Cursor/User/settings.json"
        # Windows
        elif sys.platform == "win32":
            return home / "AppData/Roaming/Cursor/User/settings.json"
        # Linux
        else:
            return home / ".config/Cursor/User/settings.json"
    
    def list_available_servers(self) -> Dict[str, Any]:
        """List all available MCP servers"""
        servers = {}
        
        # Check for existing MCP server files
        mcp_files = [
            ("mcp_server.py", "Complete ZeroWasteAI context"),
            ("hybrid_mcp_server.py", "Hybrid ZeroWasteAI + generic analysis"),
            ("generic_mcp_server.py", "Universal Python project analyzer")
        ]
        
        for file_name, description in mcp_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                servers[file_name.replace('.py', '')] = {
                    "file": file_name,
                    "description": description,
                    "exists": True,
                    "size": file_path.stat().st_size
                }
            else:
                servers[file_name.replace('.py', '')] = {
                    "file": file_name,
                    "description": description,
                    "exists": False
                }
        
        return servers
    
    def create_configuration(self, config_type: str = "complete") -> Dict[str, Any]:
        """Create MCP configuration based on type"""
        
        configurations = {
            "simple": {
                "mcpServers": {
                    "zerowaste-ai": {
                        "command": "python",
                        "args": ["mcp_server.py"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src"}
                    }
                }
            },
            "complete": {
                "mcpServers": {
                    "zerowaste-complete": {
                        "command": "python",
                        "args": ["mcp_server.py"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src"},
                        "description": "Complete ZeroWasteAI backend context"
                    },
                    "zerowaste-hybrid": {
                        "command": "python",
                        "args": ["hybrid_mcp_server.py"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src"},
                        "description": "Hybrid context server"
                    }
                }
            },
            "advanced": {
                "mcpServers": {
                    "zerowaste-complete": {
                        "command": "python",
                        "args": ["mcp_server.py"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src", "MCP_MODE": "complete"}
                    },
                    "zerowaste-api": {
                        "command": "python", 
                        "args": ["mcp_server.py", "--focus", "api"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src", "MCP_FOCUS": "endpoints"}
                    },
                    "zerowaste-architecture": {
                        "command": "python",
                        "args": ["mcp_server.py", "--focus", "architecture"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src", "MCP_FOCUS": "clean_arch"}
                    },
                    "python-universal": {
                        "command": "python",
                        "args": ["generic_mcp_server.py"],
                        "cwd": ".",
                        "env": {"PYTHONPATH": "./src"}
                    }
                },
                "defaultServer": "zerowaste-complete"
            }
        }
        
        return configurations.get(config_type, configurations["simple"])
    
    def save_configuration(self, config: Dict[str, Any], file_name: str = "mcp.json") -> bool:
        """Save MCP configuration to file"""
        try:
            config_path = self.base_path / file_name
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Configuration saved to: {config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return False
    
    def update_cursor_settings(self, mcp_config: Dict[str, Any]) -> bool:
        """Update Cursor settings.json with MCP configuration"""
        try:
            settings = {}
            
            # Read existing settings
            if self.cursor_settings.exists():
                with open(self.cursor_settings, 'r') as f:
                    settings = json.load(f)
            
            # Update MCP servers
            if "mcp" not in settings:
                settings["mcp"] = {}
            
            settings["mcp"]["servers"] = mcp_config["mcpServers"]
            
            # Backup existing settings
            if self.cursor_settings.exists():
                backup_path = self.cursor_settings.with_suffix('.json.backup')
                shutil.copy2(self.cursor_settings, backup_path)
                print(f"📋 Backup created: {backup_path}")
            
            # Save updated settings
            with open(self.cursor_settings, 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"✅ Cursor settings updated: {self.cursor_settings}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating Cursor settings: {e}")
            return False
    
    def test_servers(self, server_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """Test MCP servers"""
        results = {}
        
        # Load configuration
        if not self.config_file.exists():
            print("❌ No mcp.json configuration found")
            return results
        
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        servers = config.get("mcpServers", {})
        if server_names:
            servers = {k: v for k, v in servers.items() if k in server_names}
        
        for server_name, server_config in servers.items():
            print(f"🧪 Testing server: {server_name}")
            
            # Check if server file exists
            server_file = server_config["args"][0] if server_config["args"] else None
            if server_file:
                file_path = self.base_path / server_file
                if file_path.exists():
                    results[server_name] = True
                    print(f"  ✅ Server file exists: {server_file}")
                else:
                    results[server_name] = False
                    print(f"  ❌ Server file missing: {server_file}")
            else:
                results[server_name] = False
                print(f"  ❌ No server file specified")
        
        return results
    
    def show_status(self) -> Dict[str, Any]:
        """Show current MCP status"""
        status = {
            "config_file": str(self.config_file),
            "config_exists": self.config_file.exists(),
            "cursor_settings": str(self.cursor_settings),
            "cursor_settings_exists": self.cursor_settings.exists(),
            "available_servers": self.list_available_servers(),
            "active_servers": {}
        }
        
        # Check active configuration
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    status["active_servers"] = list(config.get("mcpServers", {}).keys())
            except:
                pass
        
        return status

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("""
MCP Manager - ZeroWasteAI MCP Configuration Tool

Usage:
  python mcp_manager.py <command> [options]

Commands:
  status                    - Show current MCP status
  list                     - List available MCP servers
  create <type>            - Create configuration (simple|complete|advanced)
  test [server_name]       - Test MCP servers
  update-cursor            - Update Cursor settings with current MCP config

Examples:
  python mcp_manager.py status
  python mcp_manager.py create complete
  python mcp_manager.py test zerowaste-complete
  python mcp_manager.py update-cursor
        """)
        sys.exit(1)
    
    manager = MCPManager()
    command = sys.argv[1].lower()
    
    if command == "status":
        status = manager.show_status()
        print("\n📊 MCP Status:")
        print(json.dumps(status, indent=2))
        
    elif command == "list":
        servers = manager.list_available_servers()
        print("\n📋 Available MCP Servers:")
        for name, info in servers.items():
            status = "✅" if info["exists"] else "❌"
            print(f"  {status} {name}: {info['description']}")
            
    elif command == "create":
        config_type = sys.argv[2] if len(sys.argv) > 2 else "complete"
        config = manager.create_configuration(config_type)
        
        if manager.save_configuration(config):
            print(f"✅ Created {config_type} configuration")
            print(f"📁 Servers configured: {list(config['mcpServers'].keys())}")
        
    elif command == "test":
        server_name = sys.argv[2] if len(sys.argv) > 2 else None
        server_names = [server_name] if server_name else None
        
        results = manager.test_servers(server_names)
        print(f"\n🧪 Test Results:")
        for server, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {server}: {status}")
            
    elif command == "update-cursor":
        if not manager.config_file.exists():
            print("❌ No mcp.json found. Run 'create' first.")
            sys.exit(1)
            
        with open(manager.config_file, 'r') as f:
            config = json.load(f)
            
        if manager.update_cursor_settings(config):
            print("✅ Cursor settings updated successfully")
            print("🔄 Restart Cursor to apply changes")
        
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 