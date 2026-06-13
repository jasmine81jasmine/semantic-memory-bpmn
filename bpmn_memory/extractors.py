"""BPMN Entity Extraction Pipeline.

Extract BPMN entities (processes, data objects, actors, etc.) from text
using custom extraction logic optimized for process descriptions.
"""

import re
from typing import Optional
from neo4j_agent_memory.extraction.base import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)


class BPMNEntityExtractor:
    """
    Custom BPMN entity extractor.
    
    Extracts BPMN-specific entities and relationships from process descriptions.
    You can extend this with LLM-based extraction or domain-specific NER.
    """
    
    # Patterns for extracting BPMN entities from text
    PROCESS_KEYWORDS = ["process", "step", "task", "operation", "activity", "procedure"]
    ACTOR_KEYWORDS = ["actor", "role", "user", "department", "team", "person", "system"]
    DATA_KEYWORDS = ["data", "form", "document", "input", "output", "file", "field"]
    SYSTEM_KEYWORDS = ["system", "application", "api", "service", "tool", "software"]
    RULE_KEYWORDS = ["rule", "regulation", "policy", "constraint", "requirement", "sla"]
    
    RELATIONSHIP_PATTERNS = {
        "TRIGGERS": r"(\w+)\s+(?:triggers?|causes?|initiates?)\s+(\w+)",
        "SUBPROCESS_OF": r"(\w+)\s+is\s+a\s+subprocess\s+of\s+(\w+)",
        "IS_INPUT_OF": r"(\w+)\s+(?:is\s+)?input\s+(?:to|of|for)\s+(\w+)",
        "HAS_OUTPUT": r"(\w+)\s+(?:produces?|outputs?)\s+(\w+)",
        "DOING": r"(\w+)\s+(?:performs?|does|executes?)\s+(\w+)",
        "COVERS": r"(\w+)\s+(?:covers?|manages?)\s+(\w+)",
        "USED_IN": r"(\w+)\s+(?:is\s+)?used\s+in\s+(\w+)",
    }
    
    def __init__(self):
        """Initialize BPMN extractor."""
        self.entity_type_keywords = {
            "PROCESS": self.PROCESS_KEYWORDS,
            "ACTOR": self.ACTOR_KEYWORDS,
            "DATA_OBJECT": self.DATA_KEYWORDS,
            "SYSTEM": self.SYSTEM_KEYWORDS,
            "RULE": self.RULE_KEYWORDS,
        }
    
    async def extract(
        self,
        text: str,
        entity_types: Optional[list[str]] = None,
        extract_relations: bool = True,
        confidence_threshold: float = 0.6,
    ) -> ExtractionResult:
        """
        Extract BPMN entities and relationships from text.
        
        Args:
            text: Process description text
            entity_types: Types to extract (if None, extract all)
            extract_relations: Whether to extract relationships
            confidence_threshold: Minimum confidence score (0-1)
        
        Returns:
            ExtractionResult with entities and relationships
        """
        entities = []
        relations = []
        
        # Extract entities using keyword patterns
        for line in text.split("\n"):
            line_lower = line.lower()
            
            for entity_type, keywords in self.entity_type_keywords.items():
                if entity_types and entity_type not in entity_types:
                    continue
                
                for keyword in keywords:
                    if keyword in line_lower:
                        # Extract entity name (simple heuristic)
                        entity_name = self._extract_entity_name(line, keyword)
                        if entity_name:
                            entities.append(
                                ExtractedEntity(
                                    name=entity_name,
                                    type=entity_type,
                                    confidence=0.85,  # Good confidence for keyword match
                                    context=line.strip(),
                                    extractor="BPMNEntityExtractor",
                                )
                            )
        
        # Extract relationships
        if extract_relations:
            for rel_type, pattern in self.RELATIONSHIP_PATTERNS.items():
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    source = match.group(1).strip()
                    target = match.group(2).strip()
                    relations.append(
                        ExtractedRelation(
                            source=source,
                            target=target,
                            relation_type=rel_type,
                            confidence=0.8,
                        )
                    )
        
        # Remove duplicates
        entities = list({e.name.lower(): e for e in entities}.values())
        relations = list({(r.source, r.target, r.relation_type): r for r in relations}.values())
        
        return ExtractionResult(
            entities=entities,
            relations=relations,
            source_text=text,
        )
    
    def _extract_entity_name(self, text: str, keyword: str) -> Optional[str]:
        """
        Extract entity name from text containing a keyword.
        Simple heuristic: get the first capitalized word or word after keyword.
        """
        # Look for quoted strings first
        matches = re.findall(r'"([^"]+)"', text)
        if matches:
            return matches[0]
        
        # Find word after keyword
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        idx = text_lower.find(keyword_lower)
        
        if idx != -1:
            # Extract words after keyword
            after_keyword = text[idx + len(keyword):]
            words = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', after_keyword)
            if words:
                return words[0]
        
        return None
