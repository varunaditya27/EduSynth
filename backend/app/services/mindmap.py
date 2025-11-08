"""
Mindmap Service - Gemini 2.5 Pro integration for generating mindmaps from lecture content.
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import google.generativeai as genai
from app.core.config import settings
from app.models.mindmap import (
    MindMapData,
    MindMapNode,
    MindMapBranch,
    MindMapChild,
    MindMapConnection
)

logger = logging.getLogger(__name__)


class MindMapService:
    """Service for generating mindmaps using Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize Gemini API"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
        )
    
    async def generate_mindmap(
        self,
        lecture_topic: str,
        lecture_audience: str,
        lecture_duration: int,
        max_branches: int = 6,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a mindmap for a lecture using Gemini 2.5 Pro
        
        Args:
            lecture_topic: Main topic of the lecture
            lecture_audience: Target audience
            lecture_duration: Duration in minutes
            max_branches: Maximum number of main branches (3-10)
            max_depth: Maximum depth of hierarchy (2-5)
        
        Returns:
            Dictionary containing mindmap data and mermaid syntax
        """
        try:
            # Construct the prompt
            prompt = self._build_mindmap_prompt(
                lecture_topic,
                lecture_audience,
                lecture_duration,
                max_branches,
                max_depth
            )
            
            # Generate content
            logger.info(f"Generating mindmap for topic: {lecture_topic}")
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            logger.debug(f"Raw Gemini response (first 500 chars): {response_text[:500]}")
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                mindmap_json = json.loads(response_text)
                logger.info(f"Successfully parsed mindmap JSON with {len(mindmap_json.get('branches', []))} branches")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response. Response text: {response_text[:1000]}")
                raise ValueError(f"Invalid JSON from Gemini: {str(e)}")
            
            # Validate structure
            if not isinstance(mindmap_json, dict):
                raise ValueError("Mindmap JSON must be a dictionary")
            if "central" not in mindmap_json:
                raise ValueError("Missing 'central' node in mindmap")
            if "branches" not in mindmap_json or not mindmap_json["branches"]:
                raise ValueError("Missing or empty 'branches' in mindmap")
            
            # Validate and structure the data
            mindmap_data = self._validate_mindmap_structure(mindmap_json)
            logger.info(f"Validated mindmap structure successfully")
            
            # Generate Mermaid syntax
            mermaid_syntax = self._generate_mermaid_syntax(mindmap_data)
            
            # Calculate metadata
            metadata = self._calculate_metadata(mindmap_data)
            
            return {
                "mindmap_data": mindmap_data,
                "mermaid_syntax": mermaid_syntax,
                "metadata": metadata
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating mindmap: {e}")
            raise
    
    def _build_mindmap_prompt(
        self,
        topic: str,
        audience: str,
        duration: int,
        max_branches: int,
        max_depth: int
    ) -> str:
        """Build the prompt for Gemini"""
        return f"""You are an educational mindmap generator. Generate a comprehensive, well-structured mindmap for a lecture.

LECTURE DETAILS:
- Topic: "{topic}"
- Target Audience: {audience}
- Duration: {duration} minutes
- Required Branches: {max_branches}
- Hierarchy Depth: {max_depth} levels

STRICT REQUIREMENTS:
1. **Central Node**: MUST have id="root", a clear label, and comprehensive description
2. **Main Branches**: Create EXACTLY {max_branches} main branches
3. **Branch Structure**: Each branch MUST have:
   - Unique id (lowercase, underscores, no spaces)
   - Clear label
   - parent="root"
   - Detailed description (2-3 sentences explaining the concept)
   - 2-4 children nodes
4. **Children**: Each child MUST have:
   - Unique id (format: parent_id + specific_name)
   - Clear label
   - Concise description (1-2 sentences)
5. **Connections**: Create 3-5 cross-connections between different branches using types: "enables", "requires", "relates", "builds-on"
6. **Node ID Rules**:
   - Only lowercase letters, numbers, and underscores
   - Examples: "quantum_basics", "gate_operations", "measurement_theory"
   - MUST be unique across entire mindmap
7. **Educational Quality**:
   - Descriptions must be factually accurate
   - Content appropriate for {audience}
   - Concepts logically organized
   - Progressive complexity from simple to advanced

CRITICAL OUTPUT FORMAT:
You MUST return ONLY a valid JSON object with this EXACT structure. NO markdown, NO code blocks, NO explanations:

{{
  "central": {{
    "id": "root",
    "label": "Main Topic Title",
    "description": "Comprehensive 2-3 sentence overview of the entire topic."
  }},
  "branches": [
    {{
      "id": "branch_1_id",
      "label": "First Main Concept",
      "parent": "root",
      "description": "Detailed 2-3 sentence explanation of this main concept and its importance.",
      "children": [
        {{
          "id": "branch_1_child_1",
          "label": "Sub-concept 1",
          "description": "Clear 1-2 sentence explanation of this sub-concept."
        }},
        {{
          "id": "branch_1_child_2",
          "label": "Sub-concept 2",
          "description": "Clear 1-2 sentence explanation of this sub-concept."
        }}
      ]
    }},
    {{
      "id": "branch_2_id",
      "label": "Second Main Concept",
      "parent": "root",
      "description": "Detailed 2-3 sentence explanation of this main concept.",
      "children": [
        {{
          "id": "branch_2_child_1",
          "label": "Sub-concept 1",
          "description": "Clear explanation."
        }}
      ]
    }}
  ],
  "connections": [
    {{
      "from": "branch_1_child_1",
      "to": "branch_2_child_1",
      "type": "enables"
    }},
    {{
      "from": "branch_2_id",
      "to": "branch_1_id",
      "type": "builds-on"
    }}
  ]
}}

VALIDATION CHECKLIST:
✓ Central node has all required fields
✓ Exactly {max_branches} branches present
✓ Each branch has 2-4 children
✓ All node IDs are unique and follow naming rules
✓ All descriptions are educational and complete
✓ 3-5 meaningful cross-connections exist
✓ Output is pure JSON (no markdown/code blocks)

Generate the mindmap JSON NOW (raw JSON only):"""
    
    def _validate_mindmap_structure(self, raw_data: Dict[str, Any]) -> MindMapData:
        """Validate and convert raw JSON to MindMapData model"""
        try:
            # Parse central node
            central = MindMapNode(**raw_data["central"])
            
            # Parse branches
            branches = []
            for branch_data in raw_data.get("branches", []):
                # Parse children
                children = [
                    MindMapChild(**child_data)
                    for child_data in branch_data.get("children", [])
                ]
                
                branch = MindMapBranch(
                    id=branch_data["id"],
                    label=branch_data["label"],
                    parent=branch_data.get("parent", "root"),
                    description=branch_data.get("description"),
                    children=children
                )
                branches.append(branch)
            
            # Parse connections
            connections = []
            for conn_data in raw_data.get("connections", []):
                connection = MindMapConnection(
                    **{"from": conn_data.get("from"), "to": conn_data.get("to"), "type": conn_data.get("type", "relates")}
                )
                connections.append(connection)
            
            return MindMapData(
                central=central,
                branches=branches,
                connections=connections
            )
        
        except Exception as e:
            logger.error(f"Error validating mindmap structure: {e}")
            raise ValueError(f"Invalid mindmap structure: {str(e)}")
    
    def _generate_mermaid_syntax(self, mindmap_data: MindMapData) -> str:
        """Generate Mermaid diagram syntax from mindmap data"""
        lines = ["graph TD"]
        
        # Central node
        central_id = mindmap_data.central.id
        central_label = mindmap_data.central.label.replace('"', "'")
        lines.append(f'  {central_id}["{central_label}"]')
        
        # Branches and children
        for branch in mindmap_data.branches:
            branch_id = branch.id
            branch_label = branch.label.replace('"', "'")
            lines.append(f'  {central_id} --> {branch_id}["{branch_label}"]')
            
            # Children
            for child in branch.children:
                child_id = child.id
                child_label = child.label.replace('"', "'")
                lines.append(f'  {branch_id} --> {child_id}["{child_label}"]')
        
        # Cross-connections
        for connection in mindmap_data.connections:
            conn_type = connection.connection_type
            lines.append(f'  {connection.from_node} -.{conn_type}.-> {connection.to_node}')
        
        # Styling
        lines.append(f'  classDef central fill:#6366f1,stroke:#4f46e5,stroke-width:3px,color:#fff')
        lines.append(f'  classDef branch fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff')
        lines.append(f'  classDef child fill:#ec4899,stroke:#db2777,stroke-width:1px,color:#fff')
        lines.append(f'  class {central_id} central')
        
        branch_ids = ','.join([b.id for b in mindmap_data.branches])
        if branch_ids:
            lines.append(f'  class {branch_ids} branch')
        
        child_ids = ','.join([
            child.id
            for branch in mindmap_data.branches
            for child in branch.children
        ])
        if child_ids:
            lines.append(f'  class {child_ids} child')
        
        return '\n'.join(lines)
    
    def _calculate_metadata(self, mindmap_data: MindMapData) -> Dict[str, int]:
        """Calculate mindmap metadata"""
        node_count = 1  # Central node
        node_count += len(mindmap_data.branches)  # Main branches
        
        for branch in mindmap_data.branches:
            node_count += len(branch.children)
        
        branch_count = len(mindmap_data.branches)
        
        # Calculate max depth (central -> branch -> child = 3)
        max_depth = 3 if any(branch.children for branch in mindmap_data.branches) else 2
        
        return {
            "node_count": node_count,
            "branch_count": branch_count,
            "max_depth": max_depth,
            "connection_count": len(mindmap_data.connections)
        }


# Singleton instance
mindmap_service = MindMapService()
