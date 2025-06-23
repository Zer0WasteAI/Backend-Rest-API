#!/usr/bin/env python3
"""
Generic MCP Server for Python Projects
Automatically analyzes any Python project structure and exposes context
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
server = Server("generic-python-project")

class GenericProjectContext:
    """Manages context for any Python project"""
    
    def __init__(self, project_path: str = "."):
        self.base_path = Path(project_path).resolve()
        self.project_name = self.base_path.name
        
    def detect_project_type(self) -> Dict[str, Any]:
        """Detect what type of Python project this is"""
        project_info = {
            "name": self.project_name,
            "type": "unknown",
            "framework": None,
            "features": []
        }
        
        # Check for common files and frameworks
        files = list(self.base_path.glob("*"))
        file_names = [f.name for f in files if f.is_file()]
        
        # Framework detection
        if "manage.py" in file_names:
            project_info["framework"] = "Django"
            project_info["type"] = "web_framework"
        elif "app.py" in file_names or "main.py" in file_names:
            if self._check_flask_project():
                project_info["framework"] = "Flask"
                project_info["type"] = "web_framework"
            elif self._check_fastapi_project():
                project_info["framework"] = "FastAPI"
                project_info["type"] = "web_framework"
        
        # Package detection
        if "setup.py" in file_names or "pyproject.toml" in file_names:
            project_info["features"].append("package")
        
        if "requirements.txt" in file_names or "Pipfile" in file_names:
            project_info["features"].append("dependencies")
            
        if "Dockerfile" in file_names:
            project_info["features"].append("docker")
            
        if "docker-compose.yml" in file_names or "docker-compose.yaml" in file_names:
            project_info["features"].append("docker-compose")
            
        if any("test" in f for f in file_names):
            project_info["features"].append("tests")
            
        return project_info
    
    def _check_flask_project(self) -> bool:
        """Check if project uses Flask"""
        try:
            req_file = self.base_path / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text()
                return "flask" in content.lower()
        except:
            pass
        return False
    
    def _check_fastapi_project(self) -> bool:
        """Check if project uses FastAPI"""
        try:
            req_file = self.base_path / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text()
                return "fastapi" in content.lower()
        except:
            pass
        return False
    
    def get_project_structure(self) -> Dict[str, Any]:
        """Get complete project structure"""
        def scan_directory(path: Path, max_depth: int = 8, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {}
                
            structure = {}
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') or item.name in ['__pycache__', 'venv', '.git', 'node_modules']:
                        continue
                        
                    if item.is_file():
                        structure[item.name] = {
                            "type": "file",
                            "size": item.stat().st_size,
                            "extension": item.suffix,
                            "lines": self._count_lines(item) if item.suffix == '.py' else None
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
    
    def _count_lines(self, file_path: Path) -> Optional[int]:
        """Count lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return None
    
    def analyze_python_files(self) -> List[Dict[str, Any]]:
        """Analyze all Python files in the project"""
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
        """Analyze a single Python file"""
        analysis = {
            "file": str(file_path.relative_to(self.base_path)),
            "lines": len(content.split('\n')),
            "size": len(content),
            "imports": [],
            "classes": [],
            "functions": [],
            "decorators": [],
            "docstring": None
        }
        
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
            
            # Get module docstring
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
                analysis["docstring"] = tree.body[0].value.s
                
        except SyntaxError:
            # If AST parsing fails, use regex fallback
            analysis.update(self._regex_analysis(content))
            
        return analysis
    
    def _regex_analysis(self, content: str) -> Dict[str, List[str]]:
        """Fallback regex analysis for Python files"""
        imports = []
        classes = []
        functions = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Imports
            if line.startswith(('import ', 'from ')):
                imports.append(line)
            
            # Classes
            class_match = re.match(r'^class\s+(\w+)', line)
            if class_match:
                classes.append(class_match.group(1))
            
            # Functions
            func_match = re.match(r'^def\s+(\w+)', line)
            if func_match:
                functions.append(func_match.group(1))
        
        return {
            "imports": imports,
            "classes": classes,
            "functions": functions
        }
    
    def get_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        deps = {
            "requirements_txt": [],
            "pyproject_toml": {},
            "pipfile": {},
            "setup_py": []
        }
        
        # requirements.txt
        req_file = self.base_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text()
                deps["requirements_txt"] = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            except:
                pass
        
        # pyproject.toml
        pyproject_file = self.base_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    deps["pyproject_toml"] = tomllib.load(f)
            except:
                deps["pyproject_toml"] = {"note": "Could not parse pyproject.toml"}
        
        return deps
    
    def find_entry_points(self) -> List[Dict[str, Any]]:
        """Find potential entry points (main files, servers, etc.)"""
        entry_points = []
        
        # Common entry point files
        entry_files = ['main.py', 'app.py', 'server.py', 'run.py', 'manage.py', '__main__.py']
        
        for entry_file in entry_files:
            file_path = self.base_path / entry_file
            if file_path.exists():
                entry_points.append({
                    "file": entry_file,
                    "type": "main_file",
                    "path": str(file_path.relative_to(self.base_path))
                })
        
        # Look for if __name__ == "__main__" patterns
        for py_file in self.base_path.rglob("*.py"):
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue
                
            try:
                content = py_file.read_text()
                if 'if __name__ == "__main__"' in content:
                    entry_points.append({
                        "file": py_file.name,
                        "type": "executable_script",
                        "path": str(py_file.relative_to(self.base_path))
                    })
            except:
                pass
        
        return entry_points

# Initialize context manager
context_manager = GenericProjectContext()

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List all available resources"""
    project_info = context_manager.detect_project_type()
    
    return [
        Resource(
            uri="project://info",
            name=f"Project Info - {project_info['name']}",
            description=f"Basic information about this {project_info.get('framework', 'Python')} project",
            mimeType="application/json"
        ),
        Resource(
            uri="project://structure",
            name="Project Structure",
            description="Complete file and directory structure",
            mimeType="application/json"
        ),
        Resource(
            uri="project://python-analysis",
            name="Python Code Analysis",
            description="Analysis of all Python files (classes, functions, imports)",
            mimeType="application/json"
        ),
        Resource(
            uri="project://dependencies",
            name="Dependencies",
            description="Project dependencies and requirements",
            mimeType="application/json"
        ),
        Resource(
            uri="project://entry-points",
            name="Entry Points",
            description="Main files and executable scripts",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    
    if uri == "project://info":
        project_info = context_manager.detect_project_type()
        return json.dumps(project_info, indent=2)
    
    elif uri == "project://structure":
        structure = context_manager.get_project_structure()
        return json.dumps(structure, indent=2)
    
    elif uri == "project://python-analysis":
        analysis = context_manager.analyze_python_files()
        return json.dumps({
            "total_files": len(analysis),
            "files": analysis
        }, indent=2)
    
    elif uri == "project://dependencies":
        deps = context_manager.get_dependencies()
        return json.dumps(deps, indent=2)
    
    elif uri == "project://entry-points":
        entry_points = context_manager.find_entry_points()
        return json.dumps(entry_points, indent=2)
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_file",
            description="Analyze a specific file in the project",
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
            description="Search for patterns in the codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (supports regex)"
                    },
                    "file_extension": {
                        "type": "string",
                        "description": "File extension to search in (e.g., 'py', 'js')",
                        "default": "py"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_project_summary",
            description="Get a comprehensive summary of the project",
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
    
    if name == "analyze_file":
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
                    "type": "non-python",
                    "content_preview": content[:500] + "..." if len(content) > 500 else content
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
    
    elif name == "search_code":
        query = arguments.get("query")
        file_ext = arguments.get("file_extension", "py")
        
        results = []
        pattern = re.compile(query, re.IGNORECASE)
        
        for file_path in context_manager.base_path.rglob(f"*.{file_ext}"):
            if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
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
                "file_extension": file_ext,
                "total_matches": len(results),
                "results": results[:50]  # Limit results
            }, indent=2)
        )]
    
    elif name == "get_project_summary":
        project_info = context_manager.detect_project_type()
        structure = context_manager.get_project_structure()
        python_analysis = context_manager.analyze_python_files()
        dependencies = context_manager.get_dependencies()
        entry_points = context_manager.find_entry_points()
        
        summary = {
            "project_info": project_info,
            "statistics": {
                "total_python_files": len(python_analysis),
                "total_dependencies": len(dependencies.get("requirements_txt", [])),
                "entry_points": len(entry_points)
            },
            "structure_overview": {
                "directories": len([k for k, v in structure.items() if v.get("type") == "directory"]),
                "files": len([k for k, v in structure.items() if v.get("type") == "file"])
            }
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
                server_name="generic-python-project",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 