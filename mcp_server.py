#!/usr/bin/env python3
"""
MCP Server for ZeroWasteAI Backend
Exposes complete backend context for AI assistants like Cursor
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Initialize the MCP server
server = Server("zerowaste-ai-backend")

class ZeroWasteBackendContext:
    """Manages the complete context of the ZeroWasteAI backend"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.src_path = self.base_path / "src"
        self.docs_path = self.base_path / "docs"
        self.test_path = self.base_path / "test"
        
    def get_project_structure(self) -> Dict[str, Any]:
        """Get the complete project structure"""
        def scan_directory(path: Path, max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {}
                
            structure = {}
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') or item.name in ['__pycache__', 'venv', '.git']:
                        continue
                        
                    if item.is_file():
                        structure[item.name] = {
                            "type": "file",
                            "size": item.stat().st_size,
                            "extension": item.suffix
                        }
                    elif item.is_dir():
                        structure[item.name] = {
                            "type": "directory",
                            "contents": scan_directory(item, max_depth, current_depth + 1)
                        }
            except PermissionError:
                pass
                
            return structure
            
        return scan_directory(self.base_path)
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """Extract all API endpoints from controllers"""
        endpoints = []
        controllers_path = self.src_path / "interface" / "controllers"
        
        if not controllers_path.exists():
            return endpoints
            
        for controller_file in controllers_path.glob("*.py"):
            if controller_file.name.startswith("__"):
                continue
                
            try:
                content = controller_file.read_text(encoding='utf-8')
                
                # Extract endpoints from route decorators
                import re
                route_pattern = r"@[a-zA-Z_]+\.route\(['\"]([^'\"]+)['\"](?:,\s*methods\s*=\s*\[([^\]]+)\])?"
                matches = re.findall(route_pattern, content)
                
                for match in matches:
                    endpoint = {
                        "path": match[0],
                        "methods": [m.strip().strip("'\"") for m in match[1].split(",")] if match[1] else ["GET"],
                        "controller": controller_file.stem,
                        "file": str(controller_file.relative_to(self.base_path))
                    }
                    endpoints.append(endpoint)
                    
            except Exception as e:
                print(f"Error reading {controller_file}: {e}")
                
        return endpoints
    
    def get_database_models(self) -> List[Dict[str, Any]]:
        """Extract database models information"""
        models = []
        models_path = self.src_path / "infrastructure" / "db" / "models"
        
        if not models_path.exists():
            return models
            
        for model_file in models_path.glob("*_orm.py"):
            try:
                content = model_file.read_text(encoding='utf-8')
                
                # Extract class definitions
                import re
                class_pattern = r"class\s+(\w+)\s*\([^)]*\):"
                classes = re.findall(class_pattern, content)
                
                for class_name in classes:
                    model = {
                        "name": class_name,
                        "file": str(model_file.relative_to(self.base_path)),
                        "table_name": model_file.stem.replace("_orm", "")
                    }
                    models.append(model)
                    
            except Exception as e:
                print(f"Error reading {model_file}: {e}")
                
        return models
    
    def get_use_cases(self) -> List[Dict[str, Any]]:
        """Extract use cases information"""
        use_cases = []
        use_cases_path = self.src_path / "application" / "use_cases"
        
        if not use_cases_path.exists():
            return use_cases
            
        for use_case_file in use_cases_path.rglob("*.py"):
            if use_case_file.name.startswith("__"):
                continue
                
            try:
                content = use_case_file.read_text(encoding='utf-8')
                
                # Extract class definitions
                import re
                class_pattern = r"class\s+(\w+)\s*:"
                classes = re.findall(class_pattern, content)
                
                for class_name in classes:
                    use_case = {
                        "name": class_name,
                        "file": str(use_case_file.relative_to(self.base_path)),
                        "category": use_case_file.parent.name,
                        "module": use_case_file.stem
                    }
                    use_cases.append(use_case)
                    
            except Exception as e:
                print(f"Error reading {use_case_file}: {e}")
                
        return use_cases
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get configuration information"""
        config = {}
        
        # Read main config
        config_file = self.src_path / "config" / "config.py"
        if config_file.exists():
            try:
                content = config_file.read_text(encoding='utf-8')
                config["main_config"] = {
                    "file": str(config_file.relative_to(self.base_path)),
                    "content_preview": content[:500] + "..." if len(content) > 500 else content
                }
            except Exception as e:
                print(f"Error reading config: {e}")
        
        # Read requirements
        req_file = self.base_path / "requirements.txt"
        if req_file.exists():
            try:
                requirements = req_file.read_text(encoding='utf-8').strip().split('\n')
                config["dependencies"] = [req.strip() for req in requirements if req.strip()]
            except Exception as e:
                print(f"Error reading requirements: {e}")
        
        # Read docker config
        docker_file = self.base_path / "Dockerfile"
        if docker_file.exists():
            try:
                content = docker_file.read_text(encoding='utf-8')
                config["docker"] = {
                    "file": "Dockerfile",
                    "content_preview": content[:300] + "..." if len(content) > 300 else content
                }
            except Exception as e:
                print(f"Error reading Dockerfile: {e}")
                
        return config

# Initialize context manager
context_manager = ZeroWasteBackendContext()

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List all available resources"""
    return [
        Resource(
            uri="zerowaste://project-structure",
            name="Project Structure",
            description="Complete file structure of the ZeroWasteAI backend",
            mimeType="application/json"
        ),
        Resource(
            uri="zerowaste://api-endpoints",
            name="API Endpoints",
            description="All REST API endpoints with their methods and controllers",
            mimeType="application/json"
        ),
        Resource(
            uri="zerowaste://database-models",
            name="Database Models",
            description="All ORM models and database schema information",
            mimeType="application/json"
        ),
        Resource(
            uri="zerowaste://use-cases",
            name="Use Cases",
            description="All business logic use cases organized by domain",
            mimeType="application/json"
        ),
        Resource(
            uri="zerowaste://configuration",
            name="Configuration",
            description="Project configuration, dependencies, and setup information",
            mimeType="application/json"
        ),
        Resource(
            uri="zerowaste://architecture",
            name="Architecture Overview",
            description="Clean Architecture implementation details and patterns",
            mimeType="application/json"
        ),
        Resource(
            uri="zerowaste://documentation",
            name="Documentation",
            description="All project documentation and API specs",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    
    if uri == "zerowaste://project-structure":
        structure = context_manager.get_project_structure()
        return json.dumps(structure, indent=2)
    
    elif uri == "zerowaste://api-endpoints":
        endpoints = context_manager.get_api_endpoints()
        return json.dumps({
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
            "controllers": list(set(ep["controller"] for ep in endpoints))
        }, indent=2)
    
    elif uri == "zerowaste://database-models":
        models = context_manager.get_database_models()
        return json.dumps({
            "total_models": len(models),
            "models": models
        }, indent=2)
    
    elif uri == "zerowaste://use-cases":
        use_cases = context_manager.get_use_cases()
        categories = {}
        for uc in use_cases:
            cat = uc["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(uc)
        
        return json.dumps({
            "total_use_cases": len(use_cases),
            "categories": categories
        }, indent=2)
    
    elif uri == "zerowaste://configuration":
        config = context_manager.get_configuration()
        return json.dumps(config, indent=2)
    
    elif uri == "zerowaste://architecture":
        architecture_info = {
            "pattern": "Clean Architecture",
            "layers": {
                "interface": {
                    "description": "Controllers, serializers, middlewares",
                    "path": "src/interface/",
                    "responsibilities": ["HTTP handling", "Input validation", "Response formatting"]
                },
                "application": {
                    "description": "Use cases, services, factories",
                    "path": "src/application/",
                    "responsibilities": ["Business logic orchestration", "Use case implementation", "Service coordination"]
                },
                "domain": {
                    "description": "Models, repositories, services",
                    "path": "src/domain/",
                    "responsibilities": ["Business entities", "Domain logic", "Repository contracts"]
                },
                "infrastructure": {
                    "description": "Database, external services, implementations",
                    "path": "src/infrastructure/",
                    "responsibilities": ["Data persistence", "External integrations", "Technical implementations"]
                }
            },
            "key_features": [
                "Firebase + JWT hybrid authentication",
                "AI-powered food recognition",
                "Smart inventory management",
                "Recipe generation with AI",
                "Environmental impact calculations",
                "Asynchronous image processing",
                "Clean separation of concerns"
            ]
        }
        return json.dumps(architecture_info, indent=2)
    
    elif uri == "zerowaste://documentation":
        docs_info = {
            "api_documentation": "Comprehensive Swagger/OpenAPI documentation",
            "swagger_endpoint": "/apidocs",
            "documentation_files": []
        }
        
        # List documentation files
        if context_manager.docs_path.exists():
            for doc_file in context_manager.docs_path.glob("*.md"):
                docs_info["documentation_files"].append({
                    "name": doc_file.name,
                    "path": str(doc_file.relative_to(context_manager.base_path))
                })
        
        return json.dumps(docs_info, indent=2)
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_code_file",
            description="Analyze a specific code file in the backend",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file from project root"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="search_code",
            description="Search for specific patterns or text in the codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (regex supported)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to search in (e.g., '*.py')",
                        "default": "*.py"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_api_documentation",
            description="Get detailed API documentation for specific endpoints",
            inputSchema={
                "type": "object",
                "properties": {
                    "controller": {
                        "type": "string",
                        "description": "Controller name (optional)"
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "Specific endpoint path (optional)"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    
    if name == "analyze_code_file":
        file_path = arguments.get("file_path")
        full_path = context_manager.base_path / file_path
        
        if not full_path.exists():
            return [types.TextContent(
                type="text",
                text=f"File not found: {file_path}"
            )]
        
        try:
            content = full_path.read_text(encoding='utf-8')
            
            # Basic analysis
            lines = content.split('\n')
            analysis = {
                "file": file_path,
                "lines": len(lines),
                "size": len(content),
                "extension": full_path.suffix,
                "imports": [],
                "classes": [],
                "functions": []
            }
            
            # Extract imports, classes, functions
            import re
            
            for line in lines:
                # Imports
                if line.strip().startswith(('import ', 'from ')):
                    analysis["imports"].append(line.strip())
                
                # Classes
                class_match = re.match(r'^\s*class\s+(\w+)', line)
                if class_match:
                    analysis["classes"].append(class_match.group(1))
                
                # Functions
                func_match = re.match(r'^\s*def\s+(\w+)', line)
                if func_match:
                    analysis["functions"].append(func_match.group(1))
            
            return [types.TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing file: {str(e)}"
            )]
    
    elif name == "search_code":
        query = arguments.get("query")
        file_pattern = arguments.get("file_pattern", "*.py")
        
        results = []
        search_path = context_manager.base_path / "src"
        
        import re
        pattern = re.compile(query, re.IGNORECASE)
        
        for file_path in search_path.rglob(file_pattern):
            if file_path.name.startswith('__'):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        results.append({
                            "file": str(file_path.relative_to(context_manager.base_path)),
                            "line": i,
                            "content": line.strip()
                        })
                        
            except Exception:
                continue
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "query": query,
                "total_matches": len(results),
                "results": results[:50]  # Limit results
            }, indent=2)
        )]
    
    elif name == "get_api_documentation":
        controller = arguments.get("controller")
        endpoint = arguments.get("endpoint")
        
        # This would integrate with your Swagger documentation
        doc_info = {
            "message": "API documentation is available via Swagger UI",
            "swagger_url": "http://localhost:5000/apidocs",
            "json_spec": "http://localhost:5000/apispec_1.json",
            "controllers": [
                "auth_controller", "inventory_controller", "recipe_controller",
                "recognition_controller", "planning_controller", "environmental_savings_controller",
                "generation_controller", "image_management_controller", "user_controller", "admin_controller"
            ]
        }
        
        if controller:
            doc_info["requested_controller"] = controller
        if endpoint:
            doc_info["requested_endpoint"] = endpoint
            
        return [types.TextContent(
            type="text",
            text=json.dumps(doc_info, indent=2)
        )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server"""
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="zerowaste-ai-backend",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 