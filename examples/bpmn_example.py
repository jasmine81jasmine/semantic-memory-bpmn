#!/usr/bin/env python3
"""Example: BPMN Agent Semantic Memory System.

Demonstrates:
1. Setting up the BPMN memory system with custom ontology
2. Extracting entities from process descriptions
3. Storing entities and relationships in Neo4j
4. Semantic search on the knowledge graph
5. Entity resolution and deduplication

Run with:
    python examples/bpmn_example.py

Prerequisites:
    - Neo4j running at localhost:7687
    - pip install -e .
"""

import asyncio
import os
from bpmn_memory import BPMNMemoryClient, BPMNMemoryConfig


async def main():
    """Main demonstration."""
    
    # ========================================================================
    # STEP 1: Configure BPMN Memory
    # ========================================================================
    print("\n" + "="*70)
    print("BPMN AGENT SEMANTIC MEMORY - DEMONSTRATION")
    print("="*70)
    
    config = BPMNMemoryConfig(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )
    
    print("\n📋 Configuration:")
    print(f"   Neo4j URI: {config.neo4j_uri}")
    print(f"   Embedding: {config.embedding_model}")
    print(f"   Vector search: {config.vector_search_enabled}")
    
    # ========================================================================
    # STEP 2: Connect and Initialize
    # ========================================================================
    async with BPMNMemoryClient(config) as memory:
        # Print schema
        await memory.print_schema()
        
        # ====================================================================
        # STEP 3: Sample Process Description (from user/agent conversation)
        # ====================================================================
        print("\n" + "="*70)
        print("PROCESSING USER INPUT - SAMPLE BPMN DESCRIPTION")
        print("="*70)
        
        process_text = """
        Customer Order Process:
        1. Customer places order through Customer Portal
        2. Order form (Order Details) is input to Order Processing process
        3. Order Processing process is performed by Sales Department
        4. System "SAP ERP" covers the Order Processing process
        5. Order data triggers Inventory Management process
        6. Inventory Management is a subprocess of Supply Chain process
        7. Warehouse Actor does the Inventory Management
        8. Inventory Check form is output from Inventory Management
        9. Compliance Rule "PCI DSS" is used in Payment Processing
        10. Payment Processing is automated
        """
        
        print("\n📝 User Input:")
        print(process_text)
        
        # ====================================================================
        # STEP 4: Extract Entities and Store
        # ====================================================================
        print("\n" + "-"*70)
        print("ENTITY EXTRACTION & STORAGE")
        print("-"*70)
        
        extraction_result = await memory.extract_and_store(
            process_text,
            session_id="demo-session-001",
            confidence_threshold=0.6,
        )
        
        print(f"\n✅ Extraction Complete:")
        print(f"   Total entities: {extraction_result['entities_extracted']}")
        print(f"   Relationships: {extraction_result['relations_extracted']}")
        
        # ====================================================================
        # STEP 5: Manual Entity Addition (for demonstration)
        # ====================================================================
        print("\n" + "-"*70)
        print("MANUAL ENTITY ADDITION (World Model Updates)")
        print("-"*70)
        
        # Add processes
        print("\n📝 Adding Processes...")
        order_process = await memory.add_process(
            name="Order Processing",
            description="Process to handle incoming customer orders",
            process_type="AUTOMATED",
            metadata={"version": "1.0", "owner": "Sales"},
        )
        
        inventory_process = await memory.add_process(
            name="Inventory Management",
            description="Process to manage inventory levels and updates",
            process_type="HYBRID",
            metadata={"version": "2.1"},
        )
        
        # Add data objects
        print("\n📝 Adding Data Objects...")
        order_form = await memory.add_data_object(
            name="Order Details",
            description="Form containing customer order information",
            data_type="FORM",
            metadata={"fields": ["order_id", "customer_id", "items", "total_price"]},
        )
        
        inventory_form = await memory.add_data_object(
            name="Inventory Check",
            description="Document showing current inventory status",
            data_type="DOCUMENT",
        )
        
        # Add actors
        print("\n📝 Adding Actors...")
        sales_dept = await memory.add_actor(
            name="Sales Department",
            description="Sales team responsible for order processing",
            actor_type="ROLE",
        )
        
        warehouse_actor = await memory.add_actor(
            name="Warehouse",
            description="Warehouse team managing inventory",
            actor_type="ROLE",
        )
        
        # ====================================================================
        # STEP 6: Create Relationships
        # ====================================================================
        print("\n" + "-"*70)
        print("CREATING RELATIONSHIPS")
        print("-"*70)
        
        # Order Details -> Order Processing
        await memory.create_relationship(
            source_name="Order Details",
            source_type="DATA_OBJECT",
            target_name="Order Processing",
            target_type="PROCESS",
            relationship_type="IS_INPUT_OF",
            properties={"required": True},
        )
        
        # Order Processing -> Inventory Management
        await memory.create_relationship(
            source_name="Order Processing",
            source_type="PROCESS",
            target_name="Inventory Management",
            target_type="PROCESS",
            relationship_type="TRIGGERS",
        )
        
        # Sales Department -> Order Processing
        await memory.create_relationship(
            source_name="Sales Department",
            source_type="ACTOR",
            target_name="Order Processing",
            target_type="PROCESS",
            relationship_type="DOING",
        )
        
        # Inventory Management -> Inventory Check
        await memory.create_relationship(
            source_name="Inventory Management",
            source_type="PROCESS",
            target_name="Inventory Check",
            target_type="DATA_OBJECT",
            relationship_type="HAS_OUTPUT",
        )
        
        # ====================================================================
        # STEP 7: Semantic Search
        # ====================================================================
        print("\n" + "-"*70)
        print("SEMANTIC SEARCH")
        print("-"*70)
        
        print("\n🔍 Searching for processes related to 'order'...")
        results = await memory.search_processes("order processing", limit=5)
        for result in results:
            print(f"   • {result['name']}: {result['description']}")
        
        print("\n🔍 Searching for all entities related to 'inventory'...")
        results = await memory.search_entities("inventory", limit=10)
        for result in results:
            print(f"   • [{result['type']}] {result['name']}")
        
        # ====================================================================
        # STEP 8: Memory Statistics
        # ====================================================================
        print("\n" + "-"*70)
        print("MEMORY STATISTICS")
        print("-"*70)
        
        stats = await memory.get_stats()
        print(f"\n📊 Graph Statistics:")
        print(f"   Entities: {stats.get('entities', 0)}")
        print(f"   Conversations: {stats.get('conversations', 0)}")
        print(f"   Messages: {stats.get('messages', 0)}")
        
        # ====================================================================
        # STEP 9: How the Data Looks in Neo4j
        # ====================================================================
        print("\n" + "="*70)
        print("NEO4J GRAPH STRUCTURE")
        print("="*70)
        
        print("""
Your Neo4j database now contains:

NODES:
├── (p:Entity:Process)
│   ├── "Order Processing" [AUTOMATED]
│   └── "Inventory Management" [HYBRID]
├── (d:Entity:DataObject)
│   ├── "Order Details" [FORM]
│   └── "Inventory Check" [DOCUMENT]
├── (a:Entity:Actor)
│   ├── "Sales Department" [ROLE]
│   └── "Warehouse" [ROLE]
└── (c:Conversation)
    └── (m:Message) [from user input]

RELATIONSHIPS:
├── (Order Details)-[:IS_INPUT_OF]->(Order Processing)
├── (Order Processing)-[:TRIGGERS]->(Inventory Management)
├── (Sales Department)-[:DOING]->(Order Processing)
├── (Inventory Management)-[:HAS_OUTPUT]->(Inventory Check)
└── (Conversation)-[:FIRST_MESSAGE]->(Message)
    └── (Message)-[:MENTIONS]->(Entity)

EMBEDDINGS:
├── Each entity has a vector embedding (384-dim for MiniLM)
├── Used for semantic search
└── Stored in Neo4j as node properties

VERIFY WITH CYPHER:

Cypher Queries you can run:

1. Find all processes:
   MATCH (p:Entity:Process) RETURN p.name, p.subtype

2. Find process relationships:
   MATCH (p1:Entity:Process)-[r]->(p2:Entity:Process)
   RETURN p1.name, type(r), p2.name

3. Find processes by actor:
   MATCH (a:Entity:Actor)-[:DOING]->(p:Entity:Process)
   RETURN a.name, p.name

4. Find data input/output:
   MATCH (d:Entity:DataObject)-[r:IS_INPUT_OF|HAS_OUTPUT]->(p:Entity:Process)
   RETURN d.name, type(r), p.name

5. Vector similarity search (semantic search):
   CALL db.index.vector.queryNodes('entity_embeddings', 10, $embedding)
   YIELD node, score
   RETURN node.name, node.type, score

6. Find related entities:
   MATCH (p:Entity:Process {name: 'Order Processing'})-[*1..2]-(related)
   RETURN related.name, related.type
        """)
        
        # ====================================================================
        # STEP 10: Extending the Schema
        # ====================================================================
        print("\n" + "="*70)
        print("EXTENDING THE ONTOLOGY SCHEMA")
        print("="*70)
        
        print("""
To add custom entity types or relationships:

1. Edit bpmn_memory/config.py:
   
   In BPMNOntologySchema.__init__():
   
   # Add new entity type
   self.entity_types["DECISION_GATE"] = "Decision point in process"
   self.subtypes["DECISION_GATE"] = ["PARALLEL", "EXCLUSIVE", "INCLUSIVE"]
   
   # Add new relationship type
   self.relationship_types["ROUTES_TO"] = "Conditional routing to process"

2. Re-initialize memory client:
   config = BPMNMemoryConfig(...)
   async with BPMNMemoryClient(config) as memory:
       # New types available immediately
       await memory.add_entity(..., entity_type="DECISION_GATE")

3. Schema is automatically converted to neo4j-agent-memory format
   with proper labels and constraints.

Full ontology schema is in: bpmn_memory/schemas.py
        """)


if __name__ == "__main__":
    asyncio.run(main())
