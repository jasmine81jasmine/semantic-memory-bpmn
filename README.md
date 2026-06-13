# BPMN Agent Semantic Memory System

A modular, extensible semantic memory system for BPMN process agents built on `neo4j-agent-memory`.

## Features

✅ **Custom Ontology Schema** - Define your own entity and relationship types  
✅ **Automatic Entity Extraction** - Extract processes, data objects, actors, etc. from text  
✅ **Semantic Search** - Vector-based search on your knowledge graph  
✅ **Entity Resolution** - Automatic deduplication and merging of entities  
✅ **World Model Updates** - Add/update/delete entities and relationships  
✅ **Conversation Memory** - Track extraction history with messages  
✅ **Neo4j Backend** - All data persisted in Neo4j knowledge graph  

## Quick Start

### 1. Installation

```bash
pip install -e .
```

### 2. Configure

Create `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

Start Neo4j:
```bash
docker run --rm -p 7687:7687 -p 7474:7474 neo4j
```

### 3. Run Example

```bash
python examples/bpmn_example.py
```

## Architecture

### Module Structure

```
bpmn_memory/
├── __init__.py           # Public API
├── config.py             # Configuration & ontology schema ⭐ EDIT THIS
├── schemas.py            # Schema conversion to neo4j-agent-memory format
├── extractors.py         # Custom BPMN entity extraction logic
└── core.py               # Main MemoryClient interface

examples/
└── bpmn_example.py       # Complete working example
```

### Data Flow

```
┌─────────────────────────────────────────────┐
│   User/Agent Conversation                   │
│  (Process description text)                 │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│   BPMNEntityExtractor                       │
│  (Extract entities & relations)             │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│   BPMNMemoryClient                          │
│  (Store in Neo4j + embeddings)              │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌───────────────���─────────────────────────────┐
│   Neo4j Database                            │
│  (Knowledge Graph + Vectors)                │
└─────────────────────────────────────────────┘
```

## Customization

### Extend Ontology Schema

Edit `bpmn_memory/config.py` in the `BPMNOntologySchema` class:

```python
class BPMNOntologySchema:
    entity_types: dict = field(default_factory=lambda: {
        "PROCESS": "A business process node",
        "DATA_OBJECT": "Data/form used in processes",
        # ADD YOUR CUSTOM TYPES HERE
        "CUSTOM_TYPE": "Your custom entity type",
    })
    
    relationship_types: dict = field(default_factory=lambda: {
        "SUBPROCESS_OF": "Process A is a subprocess of Process B",
        # ADD YOUR CUSTOM RELATIONSHIPS HERE
        "CUSTOM_RELATION": "Your custom relationship",
    })
```

Then update the entity extraction logic in `bpmn_memory/extractors.py` to recognize your new types.

### Use Your LLM Provider

The system uses `sentence-transformers` for embeddings (local, no API key needed).

To use your custom LLM endpoint instead:

1. Update `bpmn_memory/config.py`:
   ```python
   llm_provider: str = "custom"
   llm_endpoint: str = "http://localhost:8000/ai-llm/llm/query"
   ```

2. Create a custom LLM wrapper in `bpmn_memory/extractors.py` to call your endpoint

## How Neo4j Stores Your Data

### Nodes (Entities)

```cypher
# BPMN Processes
(:Entity:Process {name: "Order Processing", type: "PROCESS", subtype: "AUTOMATED"})

# Data Objects
(:Entity:DataObject {name: "Order Details", type: "DATA_OBJECT", subtype: "FORM"})

# Actors
(:Entity:Actor {name: "Sales Department", type: "ACTOR", subtype: "ROLE"})

# Stored with embeddings for semantic search
# Embedding: vector<float>[384]
```

### Relationships (Edges)

```cypher
# Process triggers another
(p1:Entity:Process)-[:TRIGGERS]->(p2:Entity:Process)

# Data object flows into process
(d:Entity:DataObject)-[:IS_INPUT_OF]->(p:Entity:Process)
(p:Entity:Process)-[:HAS_OUTPUT]->(d:Entity:DataObject)

# Actor performs process
(a:Entity:Actor)-[:DOING]->(p:Entity:Process)

# Process hierarchies
(p1:Entity:Process)-[:SUBPROCESS_OF]->(p2:Entity:Process)
```

## Querying Your Knowledge Graph

```cypher
# Find all processes
MATCH (p:Entity:Process) RETURN p.name, p.subtype

# Find process triggers
MATCH (p1:Entity:Process)-[:TRIGGERS]->(p2:Entity:Process)
RETURN p1.name, p2.name

# Find data flow
MATCH (d:Entity:DataObject)-[:IS_INPUT_OF]->(p:Entity:Process)-[:HAS_OUTPUT]->(d2:Entity:DataObject)
RETURN d.name, p.name, d2.name

# Find who does what
MATCH (a:Entity:Actor)-[:DOING]->(p:Entity:Process)
RETURN a.name, p.name

# Semantic similarity (vector search)
CALL db.index.vector.queryNodes('entity_embeddings', 10, $embedding)
YIELD node, score
RETURN node.name, node.type, score
```

## API Reference

### `BPMNMemoryClient`

#### World Model Updates

```python
# Add a process
await memory.add_process(
    name="Order Processing",
    description="...",
    process_type="AUTOMATED",  # MANUAL, AUTOMATED, HYBRID, GATEWAY
    metadata={...},
)

# Add data object
await memory.add_data_object(
    name="Order Form",
    data_type="FORM",  # FORM, DOCUMENT, DATABASE, FILE
)

# Add actor
await memory.add_actor(
    name="Sales Team",
    actor_type="ROLE",  # PERSON, ROLE, SYSTEM_ACTOR
)

# Create relationship
await memory.create_relationship(
    source_name="Order Details",
    source_type="DATA_OBJECT",
    target_name="Order Processing",
    target_type="PROCESS",
    relationship_type="IS_INPUT_OF",
)
```

#### Entity Extraction

```python
# Extract entities from text and store them
result = await memory.extract_and_store(
    text="Customer places order through Portal...",
    session_id="session-001",  # Optional: link to conversation
    confidence_threshold=0.6,
)

print(result)
# {
#   "entities_extracted": 5,
#   "relations_extracted": 3,
#   "stored_entities": {"Order Details": "entity-id-1", ...},
# }
```

#### Semantic Search

```python
# Search for processes
results = await memory.search_processes(
    query="order processing",
    limit=10
)

# Search all entities
results = await memory.search_entities(
    query="inventory",
    entity_type="PROCESS",  # Optional filter
    limit=10
)
```

#### Statistics

```python
stats = await memory.get_stats()
# {
#   "entities": 15,
#   "conversations": 2,
#   "messages": 10,
#   "traces": 0,
# }
```

## File Guide

| File | Purpose | When to Edit |
|------|---------|-------------|
| `config.py` | Ontology schema + settings | Add custom entity types |
| `extractors.py` | Entity extraction logic | Add custom extraction patterns |
| `core.py` | Main MemoryClient API | Add new query/update methods |
| `schemas.py` | Schema conversion | Usually not needed |
| `examples/bpmn_example.py` | Working example | Reference implementation |

## Embedding & Vector Storage

The system uses **sentence-transformers** for local embeddings:

- **Model**: `all-MiniLM-L6-v2` (384-dimensional)
- **Speed**: ~200ms per 1000 tokens on CPU
- **Storage**: Vectors stored as Neo4j node properties
- **Search**: Semantic similarity via vector distance

To use OpenAI embeddings instead:

```python
config = BPMNMemoryConfig(
    embedding_model="openai/text-embedding-3-small",
    # Requires OPENAI_API_KEY environment variable
)
```

## Troubleshooting

### Neo4j Connection Error

Make sure Neo4j is running:
```bash
docker ps | grep neo4j
docker logs <container_id>
```

### Entity Extraction Not Working

1. Check text includes keywords from `BPMNEntityExtractor`
2. Lower `confidence_threshold` if needed
3. Add custom keyword patterns to extractor

### Vector Search Not Finding Results

1. Make sure embeddings were generated (check Neo4j property)
2. Verify similarity threshold is not too high
3. Try more general search queries

## License

Apache 2.0

## See Also

- [neo4j-agent-memory Documentation](https://neo4j.com/labs/agent-memory/)
- [Neo4j Graph Database](https://neo4j.com/)
- [Sentence Transformers](https://www.sbert.net/)
