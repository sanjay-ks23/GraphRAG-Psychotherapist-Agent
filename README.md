# Hybrid GraphRAG - Mental Wellness Support Agent

A production-grade Hybrid GraphRAG architecture for mental wellness support, engineered with real-time safety guardrails. Orchestrates a stateful LangGraph pipeline combining semantic search (Weaviate) with knowledge graph reasoning (Neo4j) for grounded, hallucination-resistant clinical alignment. Built on an async FastAPI backend with pluggable LLM support (AWS Bedrock/OpenAI) and comprehensive observability, fully containerized via Docker for scalable AWS deployment.

## Key Features

- **Hybrid Retrieval**: Combines semantic search over unstructured data (via Weaviate) with structured, relational queries over a knowledge graph (via Neo4j) for superior context.
- **Real-time Safety Guardrails**: Pre and post-filters for clinical alignment and safety monitoring.
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
- **Vector Store**: [Weaviate](https://weaviate.io/)
- **LLM & Embedding Provider**: [Amazon Bedrock](https://aws.amazon.com/bedrock/) (default), [OpenAI](https://openai.com/)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Deployment Target**: [AWS](https://aws.amazon.com/) (ECS, EKS)

## System Architecture

```
User (Browser) → FastAPI Gateway → LangGraph Orchestrator → LLM API
                                          ↓
                              Hybrid Retrieval (Weaviate + Neo4j)
                                          ↓
                              Safety Filters (Pre + Post)
                                          ↓
                              Response Streaming (WebSocket)
```

**Key Components:**
- **FastAPI**: REST API + WebSocket server
- **LangGraph**: DAG-based pipeline orchestration
- **LLM**: Cloud LLM via AWS Bedrock or OpenAI API
- **Weaviate**: Vector embeddings storage
- **Neo4j**: Knowledge graph database
- **Redis**: Session caching
- **Prometheus**: Metrics export

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
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="password"
NEO4J_DATABASE="neo4j"

# --- Weaviate Configuration ---
WEAVIATE_HOST="localhost"
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051
WEAVIATE_CLASS_NAME="GraphRAGDocument"
```

### 2. Running Locally with Docker Compose

This is the easiest way to get the entire stack (App, Neo4j, Weaviate) running.

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
- Generate embeddings for the data and store them in Weaviate.

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
    - **Weaviate**: Deploy a Weaviate cluster, either on Kubernetes (EKS) or using Weaviate Cloud Services.
3.  **Deploy Application**: Deploy the application container to a service like Amazon ECS or EKS.
4.  **Configure Environment**: Ensure all the environment variables in the `.env` file are correctly set in the execution environment of your container.

## Pipeline Flow

1. **Preprocess**: Text normalization, embedding generation
2. **Safety Prefilter**: Fast keyword + pattern matching (< 50ms)
3. **Vector Retrieval**: Top-K similar chunks from Weaviate
4. **KG Mapping**: Find seed nodes + 2-hop graph expansion
5. **Hybrid Scoring**: Combine vector + graph + node similarity
6. **Context Assembly**: Build prompt with snippets + facts
7. **LLM Invocation**: Streaming response
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
├── main.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Multi-service orchestration
├── README.md                   # This file
├── .env.example                # Environment template
│
├── graph_rag/                  # Core application package
│   ├── settings.py             # Environment settings
│   ├── schemas.py              # Pydantic schemas
│   ├── graph/                  # LangGraph pipeline
│   │   ├── graph.py            # Main DAG definition
│   │   └── nodes.py            # Individual pipeline nodes
│   ├── services/               # External integrations
│   │   ├── weaviate_service.py # Weaviate vector store client
│   │   ├── neo4j_service.py    # Neo4j client
│   │   ├── llm_service.py      # LLM/Embedding provider
│   │   └── redis_service.py    # Redis caching
│   └── api/                    # API routes
│
├── scripts/                    # Utility scripts
│   └── ingest_data.py          # Data ingestion script
│
├── kubernetes/                 # K8s deployment configs
│
├── tests/                      # Test suite
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
docker build -t graphrag:latest .

# Run container
docker run -p 8000:8000 --env-file .env graphrag:latest

# Or use docker-compose for full stack
docker-compose up -d
```

### Docker Compose Services
- `app`: Main FastAPI application
- `weaviate`: Vector database
- `neo4j`: Knowledge graph
- `redis`: Cache layer

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
  - `graphrag_requests_total`: Total request count
  - `graphrag_request_duration_seconds`: Request latency histogram

**Logging:**
- Structured JSON logs
- Log levels: INFO, WARNING, ERROR
- Correlation IDs for tracing

## Troubleshooting

### Connection Errors

**Weaviate not connecting:**
```bash
# Check if Weaviate is running
docker ps | grep weaviate

# Check logs
docker logs graphrag-weaviate-1

# Restart
docker-compose restart weaviate
```

**Neo4j authentication failed:**
```bash
# Reset password
docker exec -it graphrag-neo4j-1 neo4j-admin set-initial-password newpassword

# Update .env
NEO4J_PASSWORD=newpassword
```

### Performance Issues

**Slow responses:**
1. Check Redis cache hit rate
2. Reduce VECTOR_TOP_K in settings
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
- AWS Bedrock / OpenAI - Large language models
- Weaviate - Vector database
- Neo4j - Graph database
- Prometheus - Monitoring
