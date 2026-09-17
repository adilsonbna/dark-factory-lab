from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = False


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: List[MCPToolParameter]


class MCPToolExecutionRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class MCPToolExecutionResponse(BaseModel):
    tool_name: str
    status: str
    result: Any
    error: Optional[str] = None
