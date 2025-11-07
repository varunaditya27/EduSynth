"""
Mindmap data models for request/response validation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ===========================
# MINDMAP NODE STRUCTURES
# ===========================

class MindMapNode(BaseModel):
    """Individual node in the mindmap"""
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., min_length=1, max_length=200, description="Display label for the node")
    description: Optional[str] = Field(None, max_length=500, description="Optional detailed description")


class MindMapChild(BaseModel):
    """Child node (without nested children)"""
    id: str = Field(..., description="Unique identifier for the child node")
    label: str = Field(..., min_length=1, max_length=200, description="Display label")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")


class MindMapBranch(BaseModel):
    """Main branch with children"""
    id: str = Field(..., description="Unique identifier for the branch")
    label: str = Field(..., min_length=1, max_length=200, description="Branch label")
    parent: str = Field(..., description="Parent node ID (usually 'root')")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    children: List[MindMapChild] = Field(default_factory=list, description="Child nodes of this branch")


class MindMapConnection(BaseModel):
    """Cross-connection between nodes"""
    from_node: str = Field(..., alias="from", description="Source node ID")
    to_node: str = Field(..., alias="to", description="Target node ID")
    connection_type: str = Field(..., alias="type", description="Connection type (e.g., 'enables', 'requires', 'relates')")
    
    class Config:
        populate_by_name = True


class MindMapData(BaseModel):
    """Complete mindmap structure"""
    central: MindMapNode = Field(..., description="Central/root node of the mindmap")
    branches: List[MindMapBranch] = Field(..., description="Main branches from the central node")
    connections: List[MindMapConnection] = Field(default_factory=list, description="Cross-connections between nodes")


# ===========================
# REQUEST/RESPONSE MODELS
# ===========================

class MindMapGenerateRequest(BaseModel):
    """Request to generate a mindmap for a lecture"""
    lecture_id: str = Field(..., description="ID of the lecture to generate mindmap for")
    regenerate: bool = Field(False, description="Force regeneration if mindmap already exists")
    max_branches: int = Field(6, ge=3, le=10, description="Maximum number of main branches")
    max_depth: int = Field(3, ge=2, le=5, description="Maximum depth of hierarchy")


class MindMapResponse(BaseModel):
    """Response containing generated mindmap"""
    lecture_id: str = Field(..., description="Lecture ID")
    mindmap_id: str = Field(..., description="Generated mindmap ID")
    mind_map: MindMapData = Field(..., description="Mindmap hierarchical structure")
    mermaid_syntax: str = Field(..., description="Mermaid diagram syntax")
    metadata: Dict[str, Any] = Field(..., description="Mindmap metadata (node count, branches, depth)")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lecture_id": "550e8400-e29b-41d4-a716-446655440000",
                "mindmap_id": "660e8400-e29b-41d4-a716-446655440001",
                "mind_map": {
                    "central": {
                        "id": "root",
                        "label": "Introduction to Quantum Computing",
                        "description": "Core concepts and principles"
                    },
                    "branches": [
                        {
                            "id": "qubits",
                            "label": "Qubits & Superposition",
                            "parent": "root",
                            "description": "Fundamental quantum information units",
                            "children": [
                                {"id": "superposition", "label": "Superposition Principle", "description": "Quantum state combinations"},
                                {"id": "measurement", "label": "Quantum Measurement", "description": "Collapse to classical state"}
                            ]
                        },
                        {
                            "id": "gates",
                            "label": "Quantum Gates",
                            "parent": "root",
                            "description": "Operations on qubits",
                            "children": [
                                {"id": "hadamard", "label": "Hadamard Gate"},
                                {"id": "cnot", "label": "CNOT Gate"}
                            ]
                        }
                    ],
                    "connections": [
                        {"from": "superposition", "to": "measurement", "type": "enables"}
                    ]
                },
                "mermaid_syntax": "graph TD\n  root[Introduction to Quantum Computing]\n  root --> qubits[Qubits & Superposition]",
                "metadata": {
                    "node_count": 8,
                    "branch_count": 2,
                    "max_depth": 3
                },
                "created_at": "2025-11-07T10:00:00Z"
            }
        }


class MindMapRetrieveResponse(BaseModel):
    """Response for retrieving existing mindmap"""
    lecture_id: str
    mindmap_id: str
    mind_map: MindMapData
    mermaid_syntax: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MindMapDeleteResponse(BaseModel):
    """Response after deleting mindmap"""
    message: str = Field(..., description="Success message")
    lecture_id: str = Field(..., description="Lecture ID of deleted mindmap")
    deleted_at: datetime = Field(..., description="Deletion timestamp")


class MindMapHealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field("mindmap", description="Service name")
    gemini_available: bool = Field(..., description="Whether Gemini API is configured")
    database_connected: bool = Field(..., description="Whether database is accessible")


class MindMapError(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    lecture_id: Optional[str] = Field(None, description="Related lecture ID")
