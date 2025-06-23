#!/usr/bin/env python3
"""
Hybrid MCP Server
Combines ZeroWasteAI specific context with generic Python project analysis
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re
import ast

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
server = Server("hybrid-context-server")

class HybridProjectContext:
    """Manages context for any project with ZeroWasteAI knowledge"""
    
    def __init__(self, project_path: str = "."):
        self.base_path = Path(project_path).resolve()
        self.project_name = self.base_path.name
        self.is_zerowaste_project = self._detect_zerowaste_project()
        
    def _detect_zerowaste_project(self) -> bool:
        """Detect if this is a ZeroWasteAI-like project"""
        indicators = [
            "src/interface/controllers",
            "src/application/use_cases", 
            "src/domain/models",
            "src/infrastructure/db",
            "inventory_controller.py",
            "recognition_controller.py"
        ]
        
        return any((self.base_path / indicator).exists() for indicator in indicators)
    
    def get_zerowaste_context(self) -> Dict[str, Any]:
        """Get ZeroWasteAI specific context if applicable"""
        if not self.is_zerowaste_project:
            return {"is_zerowaste_project": False}
        
        context = {
            "is_zerowaste_project": True,
            "architecture": "Clean Architecture",
            "features": [
                "Firebase + JWT Authentication",
                "AI-powered food recognition", 
                "Smart inventory management",
                "Recipe generation with AI",
                "Environmental impact calculations",
                "Asynchronous image processing"
            ],
            "layers": {
                "interface": {
                    "path": "src/interface/",
                    "description": "Controllers, serializers, middlewares",
                    "responsibilities": ["HTTP handling", "Input validation", "Response formatting"]
                },
                "application": {
                    "path": "src/application/",
                    "description": "Use cases, services, factories", 
                    "responsibilities": ["Business logic orchestration", "Use case implementation"]
                },
                "domain": {
                    "path": "src/domain/",
                    "description": "Models, repositories, services",
                    "responsibilities": ["Business entities", "Domain logic", "Repository contracts"]
                },
                "infrastructure": {
                    "path": "src/infrastructure/",
                    "description": "Database, external services, implementations",
                    "responsibilities": ["Data persistence", "External integrations"]
                }
            }
        }
        
        # Add specific ZeroWasteAI endpoints if they exist
        context["api_categories"] = self._get_zerowaste_api_categories()
        
        return context
    
    def _get_zerowaste_api_categories(self) -> Dict[str, List[str]]:
        """Get ZeroWasteAI API categories"""
        return {
            "auth": ["Firebase authentication", "JWT token management", "User sessions"],
            "inventory": ["Ingredient management", "Food tracking", "Expiration alerts", "Stack system"],
            "recognition": ["AI food recognition", "Image processing", "Batch recognition"],
            "recipes": ["AI recipe generation", "Recipe management", "Personalization"],
            "planning": ["Meal planning", "Calendar integration", "Nutritional analysis"],
            "environmental": ["Carbon footprint", "Waste reduction", "Sustainability metrics"],
            "image_management": ["Firebase storage", "Image optimization", "Reference management"],
            "admin": ["System monitoring", "User management", "Analytics"]
        }
    
    def get_project_structure(self) -> Dict[str, Any]:
        """Get complete project structure with ZeroWasteAI insights"""
        def scan_directory(path: Path, max_depth: int = 8, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {}
                
            structure = {}
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') or item.name in ['__pycache__', 'venv', '.git', 'node_modules']:
                        continue
                        
                    if item.is_file():
                        file_info = {
                            "type": "file",
                            "size": item.stat().st_size,
                            "extension": item.suffix
                        }
                        
                        # Add ZeroWasteAI specific insights
                        if item.suffix == '.py':
                            file_info["lines"] = self._count_lines(item)
                            file_info["zerowaste_type"] = self._classify_zerowaste_file(item)
                            
                        structure[item.name] = file_info
                        
                    elif item.is_dir():
                        dir_info = {
                            "type": "directory",
                            "contents": scan_directory(item, max_depth, current_depth + 1)
                        }
                        
                        # Add ZeroWasteAI layer classification
                        if self.is_zerowaste_project:
                            dir_info["zerowaste_layer"] = self._classify_zerowaste_directory(item)
                            
                        structure[item.name] = dir_info
            except PermissionError:
                pass
                
            return structure
            
        return scan_directory(self.base_path)
    
    def _classify_zerowaste_file(self, file_path: Path) -> Optional[str]:
        """Classify file according to ZeroWasteAI patterns"""
        relative_path = str(file_path.relative_to(self.base_path))
        
        if "controller" in file_path.name:
            return "api_controller"
        elif "use_case" in file_path.name:
            return "business_logic"
        elif "_orm.py" in file_path.name:
            return "database_model"
        elif "repository" in file_path.name:
            return "data_access"
        elif "service" in file_path.name:
            return "service_layer"
        elif "factory" in file_path.name:
            return "dependency_factory"
        elif "serializer" in file_path.name:
            return "data_validation"
        elif file_path.name == "config.py":
            return "configuration"
        elif "test" in relative_path:
            return "test_file"
        
        return None
    
    def _classify_zerowaste_directory(self, dir_path: Path) -> Optional[str]:
        """Classify directory according to Clean Architecture"""
        relative_path = str(dir_path.relative_to(self.base_path))
        
        if "src/interface" in relative_path:
            return "interface_layer"
        elif "src/application" in relative_path:
            return "application_layer"
        elif "src/domain" in relative_path:
            return "domain_layer"
        elif "src/infrastructure" in relative_path:
            return "infrastructure_layer"
        elif "test" in relative_path:
            return "testing"
        elif "docs" in relative_path:
            return "documentation"
        
        return None
    
    def _count_lines(self, file_path: Path) -> Optional[int]:
        """Count lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return None
    
    def analyze_python_files(self) -> List[Dict[str, Any]]:
        """Analyze Python files with ZeroWasteAI context"""
        python_files = []
        
        for py_file in self.base_path.rglob("*.py"):
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                analysis = self._analyze_python_file(py_file, content)
                python_files.append(analysis)
            except Exception as e:
                python_files.append({
                    "file": str(py_file.relative_to(self.base_path)),
                    "error": str(e)
                })
                
        return python_files
    
    def _analyze_python_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Python file with ZeroWasteAI insights"""
        analysis = {
            "file": str(file_path.relative_to(self.base_path)),
            "lines": len(content.split('\n')),
            "size": len(content),
            "imports": [],
            "classes": [],
            "functions": [],
            "zerowaste_patterns": []
        }
        
        # Add ZeroWasteAI specific analysis
        if self.is_zerowaste_project:
            analysis["zerowaste_type"] = self._classify_zerowaste_file(file_path)
            analysis["zerowaste_patterns"] = self._detect_zerowaste_patterns(content)
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                    })
                    
        except SyntaxError:
            # Fallback to regex analysis
            analysis.update(self._regex_analysis(content))
            
        return analysis
    
    def _detect_zerowaste_patterns(self, content: str) -> List[str]:
        """Detect ZeroWasteAI specific patterns in code"""
        patterns = []
        
        # Flask/API patterns
        if "@swag_from" in content:
            patterns.append("swagger_documentation")
        if "@jwt_required" in content:
            patterns.append("jwt_authentication")
        if "firebase" in content.lower():
            patterns.append("firebase_integration")
        if "gemini" in content.lower():
            patterns.append("ai_integration")
        if "recognition" in content.lower():
            patterns.append("food_recognition")
        if "inventory" in content.lower():
            patterns.append("inventory_management")
        if "recipe" in content.lower():
            patterns.append("recipe_functionality")
        if "environmental" in content.lower():
            patterns.append("sustainability_features")
        if "async" in content:
            patterns.append("asynchronous_processing")
        if "ORM" in content or "db.Model" in content:
            patterns.append("database_model")
        if "UseCase" in content:
            patterns.append("clean_architecture_use_case")
        
        return patterns
    
    def _regex_analysis(self, content: str) -> Dict[str, List[str]]:
        """Fallback regex analysis"""
        imports = []
        classes = []
        functions = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith(('import ', 'from ')):
                imports.append(line)
            
            class_match = re.match(r'^class\s+(\w+)', line)
            if class_match:
                classes.append(class_match.group(1))
            
            func_match = re.match(r'^def\s+(\w+)', line)
            if func_match:
                functions.append(func_match.group(1))
        
        return {
            "imports": imports,
            "classes": classes,
            "functions": functions
        }
    
    def get_dependencies(self) -> Dict[str, Any]:
        """Get dependencies with ZeroWasteAI context"""
        deps = {
            "requirements_txt": [],
            "zerowaste_dependencies": []
        }
        
        req_file = self.base_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text()
                all_deps = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                deps["requirements_txt"] = all_deps
                
                # Identify ZeroWasteAI specific dependencies
                zerowaste_deps = []
                for dep in all_deps:
                    dep_lower = dep.lower()
                    if any(keyword in dep_lower for keyword in ['flask', 'jwt', 'firebase', 'sqlalchemy', 'marshmallow', 'flasgger']):
                        zerowaste_deps.append(dep)
                
                deps["zerowaste_dependencies"] = zerowaste_deps
                
            except:
                pass
        
        return deps

# Initialize context manager
context_manager = HybridProjectContext()

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List all available resources"""
    resources = [
        Resource(
            uri="hybrid://project-info",
            name=f"Project Info - {context_manager.project_name}",
            description="Project information with ZeroWasteAI context awareness",
            mimeType="application/json"
        ),
        Resource(
            uri="hybrid://structure",
            name="Enhanced Project Structure",
            description="Project structure with Clean Architecture insights",
            mimeType="application/json"
        ),
        Resource(
            uri="hybrid://python-analysis",
            name="Python Analysis with ZeroWasteAI Patterns",
            description="Code analysis detecting ZeroWasteAI specific patterns",
            mimeType="application/json"
        ),
        Resource(
            uri="hybrid://dependencies",
            name="Dependencies Analysis",
            description="Dependencies with ZeroWasteAI framework identification",
            mimeType="application/json"
        )
    ]
    
    # Add ZeroWasteAI specific resources if detected
    if context_manager.is_zerowaste_project:
        resources.extend([
            Resource(
                uri="hybrid://zerowaste-context",
                name="ZeroWasteAI Context",
                description="Complete ZeroWasteAI architecture and feature context",
                mimeType="application/json"
            ),
            Resource(
                uri="hybrid://clean-architecture",
                name="Clean Architecture Analysis",
                description="Detailed Clean Architecture layer analysis",
                mimeType="application/json"
            )
        ])
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    
    if uri == "hybrid://project-info":
        info = {
            "name": context_manager.project_name,
            "is_zerowaste_project": context_manager.is_zerowaste_project,
            "path": str(context_manager.base_path)
        }
        
        if context_manager.is_zerowaste_project:
            info["type"] = "ZeroWasteAI Backend"
            info["architecture"] = "Clean Architecture"
            info["framework"] = "Flask with AI Integration"
        
        return json.dumps(info, indent=2)
    
    elif uri == "hybrid://structure":
        structure = context_manager.get_project_structure()
        return json.dumps(structure, indent=2)
    
    elif uri == "hybrid://python-analysis":
        analysis = context_manager.analyze_python_files()
        return json.dumps({
            "total_files": len(analysis),
            "zerowaste_project": context_manager.is_zerowaste_project,
            "files": analysis
        }, indent=2)
    
    elif uri == "hybrid://dependencies":
        deps = context_manager.get_dependencies()
        return json.dumps(deps, indent=2)
    
    elif uri == "hybrid://zerowaste-context":
        if not context_manager.is_zerowaste_project:
            return json.dumps({"error": "Not a ZeroWasteAI project"}, indent=2)
        
        context = context_manager.get_zerowaste_context()
        return json.dumps(context, indent=2)
    
    elif uri == "hybrid://clean-architecture":
        if not context_manager.is_zerowaste_project:
            return json.dumps({"error": "Not a ZeroWasteAI project"}, indent=2)
        
        context = context_manager.get_zerowaste_context()
        return json.dumps(context["layers"], indent=2)
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_file_with_context",
            description="Analyze file with ZeroWasteAI context awareness",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to the file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="search_zerowaste_patterns",
            description="Search for ZeroWasteAI specific patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_type": {
                        "type": "string",
                        "description": "Pattern type: controllers, use_cases, models, services, etc."
                    }
                },
                "required": ["pattern_type"]
            }
        ),
        Tool(
            name="get_architecture_summary",
            description="Get comprehensive architecture summary",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    
    if name == "analyze_file_with_context":
        file_path = arguments.get("file_path")
        full_path = context_manager.base_path / file_path
        
        if not full_path.exists():
            return [types.TextContent(
                type="text",
                text=f"File not found: {file_path}"
            )]
        
        try:
            content = full_path.read_text(encoding='utf-8')
            
            if full_path.suffix == '.py':
                analysis = context_manager._analyze_python_file(full_path, content)
            else:
                analysis = {
                    "file": file_path,
                    "lines": len(content.split('\n')),
                    "size": len(content),
                    "type": "non-python"
                }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing file: {str(e)}"
            )]
    
    elif name == "search_zerowaste_patterns":
        pattern_type = arguments.get("pattern_type")
        
        results = []
        for py_file in context_manager.base_path.rglob("*.py"):
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Search for specific patterns
                if pattern_type == "controllers" and "controller" in py_file.name.lower():
                    results.append({
                        "file": str(py_file.relative_to(context_manager.base_path)),
                        "type": "controller",
                        "patterns": context_manager._detect_zerowaste_patterns(content)
                    })
                elif pattern_type == "use_cases" and "use_case" in py_file.name.lower():
                    results.append({
                        "file": str(py_file.relative_to(context_manager.base_path)),
                        "type": "use_case",
                        "patterns": context_manager._detect_zerowaste_patterns(content)
                    })
                # Add more pattern searches as needed
                    
            except Exception:
                continue
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "pattern_type": pattern_type,
                "results": results
            }, indent=2)
        )]
    
    elif name == "get_architecture_summary":
        summary = {
            "project_name": context_manager.project_name,
            "is_zerowaste_project": context_manager.is_zerowaste_project
        }
        
        if context_manager.is_zerowaste_project:
            summary.update(context_manager.get_zerowaste_context())
        
        # Add general project stats
        python_files = context_manager.analyze_python_files()
        summary["statistics"] = {
            "total_python_files": len(python_files),
            "project_structure": len(context_manager.get_project_structure())
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hybrid-context-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 