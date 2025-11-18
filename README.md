# Graph RAG - Production-Grade AI Agent

This project is a state-of-the-art, production-grade Retrieval-Augmented Generation (RAG) application. It leverages a powerful combination of a Knowledge Graph (Neo4j) and a Vector Store (Milvus) to provide rich, context-aware responses to user queries. The entire pipeline is orchestrated as a stateful graph using **LangGraph**, and it is built to be deployed on **AWS**.

## Key Features

- **Hybrid Retrieval**: Combines semantic search over unstructured data (via Milvus) with structured, relational queries over a knowledge graph (via Neo4j) for superior context.
- **Stateful, Modular Pipeline**: Uses **LangGraph** to define the RAG process as a modular and extensible graph of operations.
- **Production-Ready**: Built with a production-first mindset, featuring:
    - **Centralized Configuration**: Secure and flexible settings management with Pydantic.
    - **Asynchronous API**: High-performance FastAPI server with `async` endpoints.
    - **Containerized**: Fully containerized with Docker and Docker Compose for easy local setup and scalable deployment.
    - **Cloud Native**: Designed for AWS, with configurable support for services like Amazon Bedrock.
- **Pluggable LLM Backend**: Easily switch between LLM providers like **Amazon Bedrock** and **OpenAI** through simple configuration changes.

## Tech Stack

- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Knowledge Graph**: [Neo4j](https://neo4j.com/)
- **Vector Store**: [Milvus](https://milvus.io/)
- **LLM & Embedding Provider**: [Amazon Bedrock](https://aws.amazon.com/bedrock/) (default), [OpenAI](https://openai.com/)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Deployment Target**: [AWS](https://aws.amazon.com/) (ECS, EKS)

## System Architecture

The application is designed around a central `StateGraph` defined with LangGraph. This graph orchestrates the flow of data from the user's query to the final generated response.

1.  **API Layer (`main.py`)**: A FastAPI server receives the user's query.
2.  **Graph Orchestrator (`graph_rag/graph/graph.py`)**: The request is passed to a `runnable_graph` instance.
3.  **Graph Execution**: The graph proceeds through a series of nodes:
    - **Query Rewriting**: The initial query is refined for better retrieval.
    - **Hybrid Retrieval**:
        - **Vector Store Retriever**: The query is embedded, and relevant document chunks are retrieved from Milvus.
        - **Graph Retriever**: Entities are extracted from the query, and related sub-graphs are fetched from Neo4j.
    - **Context Aggregation**: The retrieved data from both sources is combined to form a rich context.
    - **Response Generation**: The context and query are passed to the configured LLM (e.g., via Amazon Bedrock) to generate a response.
    - **Streaming**: The response is streamed back to the user in real-time.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- An AWS account with access to Amazon Bedrock (if using the default configuration).

### 1. Configuration

The entire application is configured via environment variables.

First, copy the example `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Now, edit the `.env` file with your specific settings.

```dotenv
# .env

# --- LLM and Embedding Model Configuration ---
# Options: 'aws_bedrock' or 'openai'
MODEL_PROVIDER="aws_bedrock"

# For AWS Bedrock
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_KEY"
LLM_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
EMBEDDING_MODEL_ID="amazon.titan-embed-text-v2:0"

# For OpenAI (if used)
# OPENAI_API_KEY="YOUR_OPENAI_KEY"
# LLM_MODEL_ID="gpt-4o"
# EMBEDDING_MODEL_ID="text-embedding-3-large"

# --- Database Configuration ---
# These are the defaults for the local docker-compose setup
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="password"
NEO4J_DATABASE="neo4j"

MILVUS_HOST="localhost"
MILVUS_PORT=19530
```

### 2. Running Locally with Docker Compose

This is the easiest way to get the entire stack (App, Neo4j, Milvus) running.

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### 3. Data Ingestion

After the services are running, you need to populate the databases. The project includes a sample CSV file at `data/seed_kg.csv`.

Run the ingestion script:

```bash
docker-compose exec app python scripts/ingest_data.py
```

This will:
- Create graph relationships in Neo4j.
- Generate embeddings for the data and store them in Milvus.

### 4. Using the API

You can interact with the API via the automatically generated docs at `http://localhost:8000/docs` or by sending a POST request to the `/chat` endpoint.

**Example using `curl`:**

```bash
curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-d '{"query": "Tell me about the relationships in the graph."}'
```

## Deployment on AWS

1.  **Build and Push Docker Image**: Build the Docker image and push it to a container registry like Amazon ECR.
2.  **Set up Databases**:
    - **Neo4j**: Deploy a Neo4j instance, either on EC2 or using a managed service.
    - **Milvus**: Deploy a Milvus cluster, typically on a Kubernetes cluster (EKS).
3.  **Deploy Application**: Deploy the application container to a service like Amazon ECS or EKS.
4.  **Configure Environment**: Ensure all the environment variables in the `.env` file are correctly set in the execution environment of your container (e.g., as ECS task definition environment variables or Kubernetes secrets).



## Architecture

```
User (Browser) → FastAPI Gateway → LangGraph Orchestrator → GPT-5 API
                                          ↓
                              Hybrid Retrieval (Milvus + Neo4j)
                                          ↓
                              Safety Filters (Pre + Post)
                                          ↓
                              Response Streaming (WebSocket)
```

**Key Components:**
- **FastAPI**: REST API + WebSocket server
- **LangGraph**: DAG-based pipeline orchestration
- **GPT-5**: Cloud LLM via OpenAI API
- **Milvus**: Vector embeddings storage
- **Neo4j**: Knowledge graph database
- **Redis**: Session caching
- **Prometheus**: Metrics export

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

### Installation

```bash
# Clone repository
cd sahyog

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your OpenAI API key and other credentials

# Start infrastructure (Milvus, Neo4j, Redis)
docker-compose up -d milvus neo4j redis

# Run application
python app.py
```

Application runs at: **http://localhost:8000**

Web UI available at: **http://localhost:8000/ui**

API docs at: **http://localhost:8000/docs**

## Environment Variables

Create `.env` file with:

```env
OPENAI_API_KEY=sk-your-openai-api-key
JWT_SECRET=your-secret-key
NEO4J_PASSWORD=password
```

See `.env.example` for full configuration options.

## API Endpoints

### Create Session
```bash
POST /v1/sessions
{
  "user_id": "child123",
  "consent_token": "signed_token",
  "language": "en",
  "age_range": "8-12"
}
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "jwt_token": "eyJ...",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

### Send Message
```bash
POST /v1/messages
Authorization: Bearer <jwt_token>
{
  "session_id": "sess_abc123",
  "content": "I feel anxious about exams"
}
```

**Response:**
```json
{
  "response": "It's normal to feel anxious...",
  "safety_level": "safe",
  "provenance": [...],
  "escalated": false
}
```

### WebSocket Streaming
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/sess_abc123');
ws.send(JSON.stringify({message: "I'm worried"}));
ws.onmessage = (e) => console.log(JSON.parse(e.data).token);
```

### Escalation
```bash
POST /v1/escalate
{
  "session_id": "sess_abc123",
  "reason": "Crisis detected",
  "severity": "critical"
}
```

### Feedback
```bash
POST /v1/feedback
{
  "session_id": "sess_abc123",
  "message_id": "msg_xyz",
  "rating": 5,
  "comment": "Very helpful"
}
```

## Pipeline Flow

1. **Preprocess**: Text normalization, embedding generation
2. **Safety Prefilter**: Fast keyword + pattern matching (< 50ms)
3. **Vector Retrieval**: Top-24 similar chunks from Milvus
4. **KG Mapping**: Find seed nodes + 2-hop graph expansion
5. **Hybrid Scoring**: Combine vector (60%) + graph (30%) + node similarity (10%)
6. **Context Assembly**: Build prompt with 6 snippets + 12 facts
7. **LLM Invocation**: GPT-5 streaming response
8. **Safety Postfilter**: Output validation (< 200ms)
9. **Provenance**: Extract source attribution
10. **Response Stream**: Deliver to client

## Safety System

**Prefilter (Tier 1):**
- Critical keywords: suicide, self-harm, abuse
- High-risk keywords: depression, hopeless, scared
- Response time: < 50ms

**Postfilter (Tier 2):**
- LLM output validation
- Response time: < 200ms

**Escalation:**
- Risk score > 0.9: Immediate escalation
- Critical keywords: Direct clinician notification
- Webhook + SMS alert via Twilio

## Project Structure

```

├── app.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Multi-service orchestration
├── README.md                   # This file
├── .env.example                # Environment template
│
├── core/                       # Business logic
│   ├── config.py               # Environment settings
│   ├── settings.py             # Constants
│   └── utils.py                # Helper functions
│
├── orchestrator/               # LangGraph pipeline
│   ├── graph_dag.py            # Main DAG definition
│   └── nodes/                  # Individual pipeline nodes
│       ├── preprocess.py
│       ├── vector_retriever.py
│       ├── kg_mapper.py
│       ├── hybrid_scorer.py
│       ├── context_builder.py
│       ├── safety_prefilter.py
│       ├── llm_invoker_gpt5.py
│       ├── safety_postfilter.py
│       ├── provenance_builder.py
│       └── response_streamer.py
│
├── api/                        # REST + WebSocket routes
│   ├── routes_sessions.py
│   ├── routes_messages.py
│   ├── routes_feedback.py
│   └── routes_escalation.py
│
├── services/                   # External integrations
│   ├── vector_store.py         # Milvus client
│   ├── graph_db.py             # Neo4j client
│   ├── embedding_service.py    # OpenAI embeddings
│   ├── safety_service.py       # Safety classification
│   ├── escalation_service.py   # Clinician alerts
│   ├── clinician_console.py    # Admin interface
│   └── provenance_service.py   # Source tracking
│
├── mlops/                      # MLOps + monitoring
│   ├── tracking.py             # MLflow integration
│   ├── monitoring.py           # Prometheus metrics
│   ├── logging.py              # Centralized logging
│   └── deployment.py           # Deployment helpers
│
├── tests/                      # Test suite
│   ├── test_api.py
│   ├── test_graph_dag.py
│   ├── test_safety.py
│   └── test_integration.py
│
├── web_client/                 # Browser UI
│   └── index.html              # Minimal chat interface
│
└── data/                       # Seed data
    └── seed_kg.csv             # Knowledge graph seeds
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests
pytest tests/test_integration.py
```

## Docker Deployment

### Build and Run
```bash
# Build image
docker build -t sahyog:latest .

# Run container
docker run -p 8000:8000 --env-file .env sahyog:latest

# Or use docker-compose for full stack
docker-compose up -d
```

### Docker Compose Services
- `MAIN APPLICATION`: Main FastAPI application
- `milvus`: Vector database
- `neo4j`: Knowledge graph
- `redis`: Cache layer
- `etcd`, `minio`: Milvus dependencies

## Development

### Adding a New Node

Create file in `orchestrator/nodes/`:

```python
from __future__ import annotations
import time
from orchestrator.graph_dag import PipelineState
from core.utils import get_logger

logger = get_logger(__name__)

async def my_new_node(state: PipelineState) -> PipelineState:
    start = time.time()
    # Your logic here
    state.node_timings["my_node"] = time.time() - start
    return state
```

Add to `orchestrator/graph_dag.py`:

```python
workflow.add_node("my_node", my_new_node)
workflow.add_edge("previous_node", "my_node")
```

### Adding a New API Endpoint

Create in `api/routes_*.py`:

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["feature"])

class MyRequest(BaseModel):
    field: str

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    return {"result": "success"}
```

Register in `app.py`:

```python
from api.routes_feature import router as feature_router
app.include_router(feature_router, prefix="/v1")
```

## Performance

**Target Metrics:**
- P50 latency: < 1.3s
- P95 latency: < 2.6s
- Safety check: < 50ms (prefilter), < 200ms (postfilter)
- Throughput: 100+ requests/sec

**Optimization:**
- Redis caching for embeddings (30min TTL)
- Parallel retrieval (vector + graph)
- Connection pooling for databases
- Async I/O throughout

## Security

**Authentication:**
- JWT tokens with HS256 signing
- Token expiration: 60 minutes
- Parental consent verification required

**Data Protection:**
- HTTPS required in production
- API keys in environment variables
- No credentials in logs
- Input sanitization

**Compliance:**
- COPPA compliance for children
- Data minimization
- Right to erasure support
- Audit logging

## Monitoring

**Prometheus Metrics:**
- `/metrics` endpoint exposes:
  - `sahyog_requests_total`: Total request count
  - `sahyog_request_duration_seconds`: Request latency histogram

**Logging:**
- Structured JSON logs
- Log levels: INFO, WARNING, ERROR
- Correlation IDs for tracing

**MLflow:**
- Experiment tracking
- Model versioning
- Metrics logging

## Troubleshooting

### Connection Errors

**Milvus not connecting:**
```bash
# Check if Milvus is running
docker ps | grep milvus

# Check logs
docker logs sahyog-milvus-1

# Restart
docker-compose restart milvus
```

**Neo4j authentication failed:**
```bash
# Reset password
docker exec -it sahyog-neo4j-1 neo4j-admin set-initial-password newpassword

# Update .env
NEO4J_PASSWORD=newpassword
```

### Performance Issues

**Slow responses:**
1. Check Redis cache hit rate
2. Reduce VECTOR_TOP_K in `core/settings.py`
3. Limit graph expansion hops
4. Enable response caching

**High memory usage:**
1. Reduce batch sizes
2. Limit concurrent connections
3. Enable connection pooling
4. Monitor with `docker stats`


## Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- LangGraph - DAG-based LLM orchestration
- OpenAI GPT-5 - Large language model
- Milvus - Vector database
- Neo4j - Graph database
- Prometheus - Monitoring

---
