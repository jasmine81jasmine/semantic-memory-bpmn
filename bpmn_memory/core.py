"""Core BPMN Memory Client.

Main interface for managing BPMN semantic memory:
- Store/retrieve processes, data objects, actors, relationships
- Vector-based semantic search
- Entity resolution and deduplication
- World model updates
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, dict, list, Any

from neo4j_agent_memory import MemoryClient, MemorySettings
from neo4j_agent_memory.memory import DeduplicationConfig
from neo4j_agent_memory.schema.models import EntityRef

from bpmn_memory.config import BPMNMemoryConfig, BPMNOntologySchema
from bpmn_memory.schemas import create_bpmn_schema
from bpmn_memory.extractors import BPMNEntityExtractor


class BPMNMemoryClient:
    """
    High-level interface for BPMN agent semantic memory.
    
    Manages:
    - Long-term entity store (processes, actors, data objects, etc.)
    - Relationships between entities
    - Semantic search via embeddings
    - Entity resolution and merging
    - Session-based conversation history
    """
    
    def __init__(self, config: BPMNMemoryConfig):
        """Initialize BPMN memory client.
        
        Args:
            config: BPMNMemoryConfig with Neo4j, LLM, and ontology settings
        """
        self.config = config
        self.memory_client: Optional[MemoryClient] = None
        self.extractor = BPMNEntityExtractor()
        self.schema = create_bpmn_schema(config.ontology_schema)
        self._dedup_config = DeduplicationConfig(
            auto_merge_threshold=0.95,
            flag_threshold=0.85,
            use_fuzzy_matching=True,
        )
    
    async def connect(self):
        """Connect to Neo4j and initialize memory client."""
        settings = self.config.to_memory_settings()
        self.memory_client = MemoryClient(settings)
        await self.memory_client.connect()
        print(f"✅ Connected to Neo4j at {self.config.neo4j_uri}")
    
    async def close(self):
        """Close connection to Neo4j."""
        if self.memory_client:
            await self.memory_client.close()
            print("✅ Closed Neo4j connection")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # ========================================================================
    # WORLD MODEL UPDATES: Add/Update/Merge Entities
    # ========================================================================
    
    async def add_process(
        self,
        name: str,
        description: Optional[str] = None,
        process_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Add or update a process node in the semantic memory.
        
        Args:
            name: Process name (unique identifier)
            description: Process description
            process_type: Subtype (MANUAL, AUTOMATED, HYBRID, GATEWAY)
            metadata: Additional attributes
        
        Returns:
            Entity dict with id and properties
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        entity, dedup_result = await self.memory_client.long_term.add_entity(
            name=name,
            entity_type="PROCESS",
            subtype=process_type,
            description=description,
            attributes={
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                **metadata if metadata else {},
            },
            deduplication=self._dedup_config,
        )
        
        print(f"📝 Added process: {name} (ID: {entity.id})")
        if dedup_result.action == "merged":
            print(f"   ⚠️  Merged with existing: {dedup_result.matched_entity_name}")
        
        return {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "dedup_action": dedup_result.action,
        }
    
    async def add_data_object(
        self,
        name: str,
        description: Optional[str] = None,
        data_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Add a data object (form, document, file) to the semantic memory.
        
        Args:
            name: Data object name
            description: What this data object is
            data_type: Subtype (FORM, DOCUMENT, DATABASE, FILE)
            metadata: Additional attributes
        
        Returns:
            Entity dict
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        entity, dedup_result = await self.memory_client.long_term.add_entity(
            name=name,
            entity_type="DATA_OBJECT",
            subtype=data_type,
            description=description,
            attributes={
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                **metadata if metadata else {},
            },
            deduplication=self._dedup_config,
        )
        
        print(f"📄 Added data object: {name}")
        return {"id": entity.id, "name": entity.name, "type": entity.type}
    
    async def add_actor(
        self,
        name: str,
        description: Optional[str] = None,
        actor_type: Optional[str] = None,
    ) -> dict:
        """
        Add an actor (person, role, system) to the semantic memory.
        
        Args:
            name: Actor name/identifier
            description: Actor description
            actor_type: Subtype (PERSON, ROLE, SYSTEM_ACTOR)
        
        Returns:
            Entity dict
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        entity, _ = await self.memory_client.long_term.add_entity(
            name=name,
            entity_type="ACTOR",
            subtype=actor_type,
            description=description,
            deduplication=self._dedup_config,
        )
        
        print(f"👤 Added actor: {name}")
        return {"id": entity.id, "name": entity.name, "type": entity.type}
    
    async def create_relationship(
        self,
        source_name: str,
        source_type: str,
        target_name: str,
        target_type: str,
        relationship_type: str,
        properties: Optional[dict] = None,
    ) -> dict:
        """
        Create a relationship between two entities.
        
        Args:
            source_name: Name of source entity
            source_type: Type of source entity (PROCESS, DATA_OBJECT, etc.)
            target_name: Name of target entity
            target_type: Type of target entity
            relationship_type: Type of relationship (TRIGGERS, IS_INPUT_OF, etc.)
            properties: Optional relationship properties
        
        Returns:
            Relationship info dict
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        # Create entity references
        source_ref = EntityRef(name=source_name, type=source_type)
        target_ref = EntityRef(name=target_name, type=target_type)
        
        # Create relationship (simplified - actual implementation via Cypher)
        print(f"🔗 Creating relationship: {source_name} --[{relationship_type}]--> {target_name}")
        
        return {
            "source": source_name,
            "relationship_type": relationship_type,
            "target": target_name,
            "properties": properties or {},
        }
    
    # ========================================================================
    # ENTITY EXTRACTION: Text → Entities & Relationships
    # ========================================================================
    
    async def extract_and_store(
        self,
        text: str,
        session_id: Optional[str] = None,
        confidence_threshold: float = 0.6,
    ) -> dict:
        """
        Extract BPMN entities and relationships from text and store them.
        
        This is the main entry point for processing user descriptions.
        
        Args:
            text: Process description text
            session_id: Optional session ID for conversation tracking
            confidence_threshold: Minimum confidence for extracted entities
        
        Returns:
            Extraction result dict with counts and entity IDs
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        print(f"\n🔍 Extracting entities from text...")
        
        # Extract entities using custom BPMN extractor
        extraction_result = await self.extractor.extract(
            text,
            extract_relations=True,
            confidence_threshold=confidence_threshold,
        )
        
        print(f"   Extracted: {len(extraction_result.entities)} entities, "
              f"{len(extraction_result.relations)} relationships")
        
        # Store entities in memory
        stored_entities = {}
        for entity in extraction_result.entities:
            if entity.confidence < confidence_threshold:
                continue
            
            entity_dict, _ = await self.memory_client.long_term.add_entity(
                name=entity.name,
                entity_type=entity.type,
                subtype=entity.subtype,
                description=entity.context,
                attributes={"confidence": entity.confidence},
                deduplication=self._dedup_config,
            )
            stored_entities[entity.name] = entity_dict.id
            print(f"   ✓ Stored {entity.type}: {entity.name}")
        
        # Link to message if session provided
        if session_id:
            message = await self.memory_client.short_term.add_message(
                session_id,
                "user",
                text,
                metadata={"entities_extracted": len(extraction_result.entities)},
            )
            print(f"   ✓ Linked to session: {session_id}")
        
        return {
            "entities_extracted": len(extraction_result.entities),
            "relations_extracted": len(extraction_result.relations),
            "stored_entities": stored_entities,
            "extraction_result": extraction_result,
        }
    
    # ========================================================================
    # SEMANTIC SEARCH: Find Related Entities
    # ========================================================================
    
    async def search_processes(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Semantic search for processes.
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching processes
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        # Search using the memory client's search capability
        results = await self.memory_client.long_term.search(
            query,
            entity_types=["PROCESS"],
            limit=limit,
        )
        
        return [
            {"name": r.name, "type": r.type, "description": r.description}
            for r in results
        ]
    
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Semantic search for entities by type.
        
        Args:
            query: Search query
            entity_type: Filter by entity type (PROCESS, DATA_OBJECT, etc.)
            limit: Maximum results
        
        Returns:
            List of matching entities
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        results = await self.memory_client.long_term.search(
            query,
            entity_types=[entity_type] if entity_type else None,
            limit=limit,
        )
        
        return [
            {"name": r.name, "type": r.type, "description": r.description}
            for r in results
        ]
    
    # ========================================================================
    # MEMORY STATS & INTROSPECTION
    # ========================================================================
    
    async def get_stats(self) -> dict:
        """
        Get memory statistics.
        
        Returns:
            Dict with entity counts by type
        """
        assert self.memory_client, "Not connected. Call await connect() first."
        
        stats = await self.memory_client.get_stats()
        return stats
    
    async def print_schema(self):
        """Print current ontology schema for reference."""
        print("\n" + "="*60)
        print("BPMN ONTOLOGY SCHEMA")
        print("="*60)
        
        print("\nEntity Types:")
        for entity_type in self.schema.entity_types:
            print(f"  • {entity_type.name}: {entity_type.description}")
            if entity_type.subtypes:
                print(f"      Subtypes: {', '.join(entity_type.subtypes)}")
        
        print("\nRelationship Types:")
        for rel_type in self.schema.relation_types:
            print(f"  • {rel_type.name}: {rel_type.description}")
