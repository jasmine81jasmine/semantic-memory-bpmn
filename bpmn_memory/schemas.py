"""BPMN Ontology Schema Management.

Convert BPMN domain schema to neo4j-agent-memory EntitySchemaConfig.
"""

from neo4j_agent_memory.schema.models import (
    EntitySchemaConfig,
    EntityTypeConfig,
    RelationTypeConfig,
)
from bpmn_memory.config import BPMNOntologySchema


def create_bpmn_schema(ontology: BPMNOntologySchema) -> EntitySchemaConfig:
    """
    Convert BPMN ontology schema to neo4j-agent-memory EntitySchemaConfig.
    
    This schema is **fully customizable**. Edit BPMNOntologySchema in config.py
    to add/remove entity types, relationships, or subtypes.
    
    Args:
        ontology: BPMN ontology configuration
    
    Returns:
        EntitySchemaConfig ready for memory client
    """
    
    # Create entity type configs
    entity_types = []
    for entity_name, description in ontology.entity_types.items():
        subtypes = ontology.subtypes.get(entity_name, [])
        entity_types.append(
            EntityTypeConfig(
                name=entity_name,
                description=description,
                subtypes=subtypes,
                attributes=["name", "description", "created_at", "updated_at"],
            )
        )
    
    # Create relationship type configs
    relation_types = []
    for rel_name, description in ontology.relationship_types.items():
        relation_types.append(
            RelationTypeConfig(
                name=rel_name,
                description=description,
                source_types=list(ontology.entity_types.keys()),
                target_types=list(ontology.entity_types.keys()),
                properties=["confidence", "source", "created_at"],
            )
        )
    
    # Create schema config
    return EntitySchemaConfig(
        name="bpmn",
        version="1.0",
        description="BPMN Process Ontology Schema",
        entity_types=entity_types,
        relation_types=relation_types,
        default_entity_type="PROCESS",
        enable_subtypes=True,
        strict_types=False,  # Allow custom types during extraction
    )


def get_bpmn_schema() -> EntitySchemaConfig:
    """Get default BPMN schema."""
    ontology = BPMNOntologySchema()
    return create_bpmn_schema(ontology)
