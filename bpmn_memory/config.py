"""Configuration for BPMN semantic memory system."""

from dataclasses import dataclass, field
from typing import Optional
from pydantic import SecretStr
from neo4j_agent_memory import (
    MemorySettings,
    Neo4jConfig,
    ExtractionConfig,
    ExtractorType,
)


@dataclass
class BPMNOntologySchema:
    """BPMN ontology schema configuration.
    
    Defines the entity types and relationships specific to your BPMN domain.
    This is **fully editable** - you can extend it to support your custom
    process types, data objects, and relationships.
    """
    
    # Entity types (nodes in your ontology)
    entity_types: dict = field(default_factory=lambda: {
        "PROCESS": "A business process node",
        "DATA_OBJECT": "Data/form used in processes (input or output)",
        "ACTOR": "Person, role, or system performing a process",
        "SYSTEM": "Software or IT system covering processes",
        "RULE": "Business rule or regulation used in a process",
        "DEPARTMENT": "Organizational unit/department handling processes",
        "DICTIONARY": "Dictionary entry or concept definition",
    })
    
    # Relationship types (edges in your ontology)
    relationship_types: dict = field(default_factory=lambda: {
        "SUBPROCESS_OF": "Process A is a subprocess of Process B",
        "IS_INPUT_OF": "Data object is input to a process",
        "HAS_OUTPUT": "Process produces an output data object",
        "DOING": "Actor/department performs a process",
        "TRIGGERS": "Process A triggers Process B",
        "COVERS": "System covers/manages a process",
        "SYSTEM_INPUT": "System receives input data object",
        "SYSTEM_OUTPUT": "System produces output data object",
        "USED_IN": "Rule/regulation is used in a process",
        "DEFINES_CONCEPT": "Dictionary entry defines concept used in process",
    })
    
    # Optional subtypes for finer classification
    subtypes: dict = field(default_factory=lambda: {
        "PROCESS": ["MANUAL", "AUTOMATED", "HYBRID", "GATEWAY"],
        "DATA_OBJECT": ["FORM", "DOCUMENT", "DATABASE", "FILE"],
        "ACTOR": ["PERSON", "ROLE", "SYSTEM_ACTOR"],
        "SYSTEM": ["WEB_APP", "API", "LEGACY_SYSTEM", "DATABASE"],
        "RULE": ["COMPLIANCE", "BUSINESS_RULE", "SLA"],
        "DEPARTMENT": ["OPERATIONS", "FINANCE", "HR", "IT"],
    })
    
    def add_entity_type(self, entity_type: str, description: str, subtypes: Optional[list] = None):
        """Add a custom entity type to the schema."""
        self.entity_types[entity_type] = description
        if subtypes:
            self.subtypes[entity_type] = subtypes
    
    def add_relationship_type(self, rel_type: str, description: str):
        """Add a custom relationship type to the schema."""
        self.relationship_types[rel_type] = description


@dataclass
class BPMNMemoryConfig:
    """Configuration for BPMN Memory Client.
    
    Combines Neo4j connection settings, LLM/embedding provider settings,
    and extraction pipeline configuration.
    """
    
    # Neo4j Connection
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    
    # LLM Provider (for entity extraction and enrichment)
    # Use your custom LLM provider instead of OpenAI
    llm_provider: str = "custom"  # Change this to your LLM provider
    llm_endpoint: str = "http://localhost:8000/ai-llm/llm/query"  # Your LLM endpoint
    
    # Embedding Model (for semantic search)
    # Options: 
    #   - "openai/text-embedding-3-small" (requires OPENAI_API_KEY)
    #   - "sentence-transformers/all-MiniLM-L6-v2" (local, no API key)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Entity Extraction
    # Options: SPACY, GLINER, LLM, NONE
    extractor_type: str = ExtractorType.GLINER
    
    # BPMN Ontology Schema
    ontology_schema: BPMNOntologySchema = field(default_factory=BPMNOntologySchema)
    
    # Vector search configuration
    vector_search_enabled: bool = True
    vector_dimension: int = 384  # For sentence-transformers/all-MiniLM-L6-v2
    similarity_threshold: float = 0.75
    
    def to_memory_settings(self) -> MemorySettings:
        """Convert to MemorySettings for neo4j-agent-memory client."""
        return MemorySettings(
            neo4j=Neo4jConfig(
                uri=self.neo4j_uri,
                username=self.neo4j_username,
                password=SecretStr(self.neo4j_password),
            ),
            embedding=self.embedding_model,
            extraction=ExtractionConfig(
                extractor_type=ExtractorType[self.extractor_type],
            ),
        )
