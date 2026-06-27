# Poseidon-RAG: MCP Implementation Documentation

**Last Updated**: June 24, 2024  
**Status**: Production-Ready Resume Project  
**Architecture**: Model Context Protocol (MCP) + LangGraph + FastAPI

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [MCP Server Details](#mcp-server-details)
4. [Data Flow](#data-flow)
5. [Security Measures](#security-measures)
6. [Installation & Setup](#installation--setup)
7. [Running the System](#running-the-system)
8. [API Endpoints](#api-endpoints)
9. [Example Queries](#example-queries)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React)                             │
│                    @ localhost:5173                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTP
                    POST /api/agent
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend Server                             │
│              @ localhost:5000                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            LangGraph Agent (Main Orchestrator)          │   │
│  │                                                         │   │
│  │  1. retrieve_rag_context: Fetch relevant docs          │   │
│  │  2. chatbot: Generate response + decide on tools       │   │
│  │  3. tools: Execute MCP tools (query database)          │   │
│  │  4. get_points: Extract geospatial data from results   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓ HTTP (JSON-RPC 2.0)
│                  (MCP Protocol via adapter)
│                            ↓
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      MCP Server (FastMCP @ localhost:8000/mcp)         │   │
│  │                                                         │   │
│  │  Tool: execute_query                                   │   │
│  │  - Validates query (only SELECT allowed)               │   │
│  │  - Enforces LIMIT 200 for non-aggregate queries        │   │
│  │  - Executes via SQLite connection                      │   │
│  │  - Returns results as dict                             │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓ SQL
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         SQLite Database (argo_data.db)                 │   │
│  │                                                         │   │
│  │  Table: measurements                                   │   │
│  │  - platform_number (TEXT)                              │   │
│  │  - temp (REAL) - Temperature in °C                     │   │
│  │  - psal (REAL) - Salinity in PSU                       │   │
│  │  - pres (REAL) - Pressure in dbar                      │   │
│  │  - latitude (REAL)                                     │   │
│  │  - longitude (REAL)                                    │   │
│  │  - time (DATETIME)                                     │   │
│  │                                                         │   │
│  │  Vector DB: Chroma (for RAG context retrieval)         │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         External LLM (Groq API)                         │   │
│  │         Model: llama-3.3-70b / gpt-oss-120b            │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 System Components

### 1. **mcp_server.py** - MCP Tool Provider
**Purpose**: Exposes database query tool via MCP protocol  
**Type**: FastMCP application  
**Key Features**:
- Single tool: `execute_query(query: str) -> dict`
- Query validation using `sqlparse`
- Automatic LIMIT enforcement for performance
- Returns JSON-serializable dictionary

**Location**: `Backend/mcp_server.py`  
**Port**: Not exposed directly (accessed via LangGraph adapter)

```python
@mcp.tool()
def execute_query(query: str) -> dict:
    """
    Validates Given query allowing only SELECT Statements and 
    Rejecting Query involving other Keywords like DROP,DELETE,ALTER,etc.
    Also allows max of 1000 rows as results for non aggregate queries.
    Returns result as a dictionary
    """
```

### 2. **LangGraph_Bot.py** - Agent Orchestrator
**Purpose**: Implement RAG + LLM + MCP workflow  
**Type**: LangGraph state machine  
**Nodes**:
1. `retrieve_rag_context` - Fetches relevant metadata from vector DB
2. `chatbot` - LLM processes message + RAG context, decides tool use
3. `tools` - Executes MCP tools (query database)
4. `get_points` - Extracts geospatial coordinates for frontend map

**Key Features**:
- Async/await support for concurrent operations
- MultiServerMCPClient for MCP protocol communication
- LangSmith integration for observability
- In-memory checkpoint for conversation history

**Location**: `Backend/LangGraph_Bot.py`  
**Async Function**: `async def get_graph() -> LangGraph`

### 3. **main.py** - FastAPI Server
**Purpose**: HTTP endpoint for frontend  
**Type**: FastAPI application  
**Key Endpoint**:
```python
POST /api/agent
{
  "message": "Show me floats in Arabian Sea"
}
Returns:
{
  "response": "AI-generated answer",
  "points": [
    {
      "id": "platform_123",
      "lat": 15.5,
      "lng": 72.3,
      "temp": 24.5,
      "psal": 35.2,
      "pres": 1000
    }
  ]
}
```

**Location**: `Backend/main.py`  
**Port**: 5000

### 4. **rag_setup.py** - RAG Pipeline
**Purpose**: Initialize vector database and retriever  
**Type**: Utility module  
**Components**:
- NetCDF file processor (from data/)
- Vector embeddings (using LangChain)
- Chroma vector database
- Semantic retriever for metadata

**Location**: `Backend/rag_setup.py`

---

## 🤖 MCP Server Details

### What is MCP?
**Model Context Protocol** is Anthropic's protocol for connecting LLMs to external tools/data sources.

**Protocol Used**: HTTP (JSON-RPC 2.0 format)

### How MCP Works in This Project

1. **Tool Definition**:
   ```python
   @mcp.tool()
   def execute_query(query: str) -> dict:
       """Execute SQL query on ARGO database"""
   ```

2. **Client-Server Communication**:
   - Client (LangGraph) sends: `{"method": "execute_query", "params": {"query": "SELECT..."}}`
   - Server (FastMCP) validates & executes
   - Server returns: `{"result": [{"platform_number": "123", "temp": 24.5}, ...]}`

3. **Adapter Layer**:
   - `MultiServerMCPClient` from `langchain-mcp-adapters`
   - Handles JSON-RPC serialization/deserialization
   - Makes MCP tools available as LangChain tools

### Query Validation Rules (Security)

The MCP server implements **4-layer validation**:

| Layer | Rule | Consequence |
|-------|------|-------------|
| **Parse** | Only SELECT statements allowed | ❌ Rejects DROP/DELETE/INSERT |
| **Structure** | Must include FROM clause | ❌ Rejects malformed SQL |
| **Limit** | Non-aggregate queries get `LIMIT 200` | ✅ Prevents data exfiltration |
| **Aggregation** | COUNT/SUM/AVG/MIN/MAX recognized | ✅ No limit on aggregates |

**Code**:
```python
def isAgg(query: str) -> bool:
    parse = sqlparse.parse(query)
    clean_statement = str(parse[0]).strip()
    return bool(re.search(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', 
                         clean_statement, re.IGNORECASE))

# In execute_query:
if not isAgg(clean_query):
    if not re.search(r'\b(LIMIT)', clean_query, re.IGNORECASE):
        clean_query += ' LIMIT 200;'
```

---

## 📊 Data Flow

### User Query → Response Pipeline

```
Step 1: User submits message via React frontend
        ↓
Step 2: POST /api/agent with message
        ↓
Step 3: FastAPI receives request, creates async task
        ↓
Step 4: LangGraph triggers retrieve_rag_context
        - Message sent to vector DB retriever
        - Top-k semantically similar docs fetched
        - Metadata (location, platform info) attached
        ↓
Step 5: LangGraph triggers chatbot node
        - System prompt + RAG context + message → LLM
        - LLM decides: respond directly OR use tool
        - If tool needed: generates SQL query
        ↓
Step 6: If tool called, LangGraph triggers tools node
        - ToolNode routes to execute_query tool
        - Tool sends JSON-RPC to MCP server
        ↓
Step 7: MCP server validates query
        - sqlparse checks it's valid SELECT
        - isAgg() determines if LIMIT needed
        - Adds LIMIT 200 if not aggregate
        ↓
Step 8: MCP server executes SQLite query
        - Results converted to list of dicts
        - Returned as JSON
        ↓
Step 9: LangGraph triggers get_points node
        - Extracts lat/lng from results
        - Creates point objects for map visualization
        ↓
Step 10: LangGraph triggers chatbot again
         - LLM sees tool results
         - Generates final natural language response
         ↓
Step 11: FastAPI returns response + points to frontend
         {
           "response": "Found 3 floats in Arabian Sea...",
           "points": [{lat, lng, temp, psal, pres}, ...]
         }
         ↓
Step 12: Frontend displays response + renders map with points
```

---

## 🔒 Security Measures

### 1. Query Validation (MCP Server)
- ✅ Only SELECT statements allowed
- ✅ Automatic LIMIT 200 on non-aggregate queries
- ✅ Uses `sqlparse` for proper SQL parsing (not regex-based)
- ❌ DROP, DELETE, INSERT, UPDATE, CREATE automatically rejected

### 2. System Prompt Guards
- ✅ Instructions never reveal schema details
- ✅ Prompt injection attacks deflected
- ✅ LLM told to never expose table/column names
- ✅ Fallback response for confidentiality: "I cannot discuss internal system architecture..."

### 3. MCP Protocol Security
- ✅ JSON-RPC 2.0 standardized format
- ✅ No arbitrary code execution
- ✅ Tool parameters strictly typed
- ✅ Errors returned safely (never raw SQL errors exposed to user)

### 4. Database Access Control
- ✅ SQLite read-only context (no schema modification)
- ✅ Single database file (argo_data.db)
- ✅ Only `measurements` table exposed
- ✅ No direct SQL string concatenation (using cursor.execute)

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 16+ (for Frontend)
- GROQ_API_KEY (for LLM access)
- LANGSMITH_API_KEY (optional, for observability)

### Backend Setup

```bash
cd Backend

# Install dependencies
pip install -r requirements.txt

# Or manually install key packages:
pip install fastapi uvicorn langgraph langchain langchain-groq
pip install langchain-mcp-adapters mcp[server] streamable-http
pip install chroma-db sentence-transformers
pip install sqlparse python-dotenv

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here (optional)
LANGSMITH_PROJECT=Poseiden-RAG
LANGSMITH_TRACING=true
EOF
```

### Database Setup

```bash
# Database auto-creates on first run from NetCDF
# Vector DB auto-initializes from argo_setup.py
# Check data/ directory exists:
mkdir -p Backend/data/
```

### Frontend Setup

```bash
cd Frontend/react-app

npm install
npm run dev
```

---

## 🚀 Running the System

### Option 1: Development Mode (Recommended for Resume)

**Terminal 1 - Backend Server**:
```bash
cd Backend
python main.py
# Output: 
# Uvicorn running on http://0.0.0.0:5000
# INFO: Uvicorn server process [12345] started with ← process started
```

**Terminal 2 - Frontend**:
```bash
cd Frontend/react-app
npm run dev
# Output:
# VITE v4.x.x  ready in XXX ms
# ➜  Local:   http://localhost:5173
```

Open browser: `http://localhost:5173`

### Option 2: Docker (for Deployment)

```dockerfile
# Create Backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY Backend/requirements.txt .
RUN pip install -r requirements.txt

COPY Backend/ .

CMD ["python", "main.py"]
```

```bash
docker build -t poseidon-rag-backend .
docker run -p 5000:5000 -e GROQ_API_KEY=$GROQ_API_KEY poseidon-rag-backend
```

---

## 🔌 API Endpoints

### Backend (FastAPI)

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/` | GET | Health check | - | `{"response": "Agent is running"}` |
| `/api/agent` | POST | Process user query | `{"message": "..."}` | `{"response": "...", "points": [...]}` |

### MCP Server

| Method | Purpose | Params |
|--------|---------|--------|
| `execute_query` | Execute SQL on measurements table | `{"query": "SELECT ..."}` |

**Example MCP Request** (internal, handled by adapter):
```json
{
  "jsonrpc": "2.0",
  "method": "execute_query",
  "params": {
    "query": "SELECT platform_number, AVG(temp) AS temp FROM measurements WHERE latitude > 0 GROUP BY platform_number LIMIT 10"
  },
  "id": 1
}
```

**Example MCP Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "result": [
      {
        "platform_number": "3900123",
        "temp": 24.5
      },
      {
        "platform_number": "3900456",
        "temp": 18.2
      }
    ]
  },
  "id": 1
}
```

---

## 💡 Example Queries

### 1. Find Floats in Arabian Sea

**User Query**: "Show me floats in Arabian Sea"

**LLM-Generated SQL**:
```sql
SELECT 
  platform_number, 
  AVG(latitude) AS latitude, 
  AVG(longitude) AS longitude, 
  AVG(temp) AS temp,
  AVG(psal) AS psal,
  AVG(pres) AS pres
FROM measurements 
WHERE latitude BETWEEN 0 AND 30 
  AND longitude BETWEEN 40 AND 80
GROUP BY platform_number
LIMIT 25
```

**Response**:
```
"Found 5 active Argo floats in the Arabian Sea:
- Platform 3900123: Located at (15.2°N, 62.5°E), temperature 24.5°C, salinity 35.1 PSU
- Platform 3900456: Located at (18.7°N, 68.3°E), temperature 22.1°C, salinity 35.4 PSU
..."

points: [
  {id: "3900123", lat: 15.2, lng: 62.5, temp: 24.5, psal: 35.1, pres: 1200},
  {id: "3900456", lat: 18.7, lng: 68.3, temp: 22.1, psal: 35.4, pres: 950},
  ...
]
```

### 2. Compare Salinity Across Regions

**User Query**: "Compare salinity levels in equator vs northern hemisphere"

**LLM-Generated SQL**:
```sql
SELECT 
  CASE 
    WHEN latitude < 0 THEN 'Southern Hemisphere'
    WHEN latitude BETWEEN 0 AND 30 THEN 'Tropical Zone'
    ELSE 'Northern Temperate'
  END AS region,
  COUNT(*) AS float_count,
  AVG(psal) AS avg_salinity,
  MIN(psal) AS min_salinity,
  MAX(psal) AS max_salinity
FROM measurements
GROUP BY region
```

### 3. Track Float Movement

**User Query**: "What's the position of float 3900123 over time?"

**LLM-Generated SQL**:
```sql
SELECT 
  platform_number,
  time,
  latitude,
  longitude,
  temp,
  pres
FROM measurements
WHERE platform_number = '3900123'
ORDER BY time DESC
LIMIT 25
```

---

## 🐛 Troubleshooting

### Issue 1: "Cannot connect to MCP Server"

**Symptoms**: Error in terminal, LLM response includes "connection error"

**Solution**:
```bash
# Verify mcp_server.py is running
ps aux | grep mcp_server

# If not running, manually start it:
cd Backend
python mcp_server.py

# Check if port 8000 is accessible:
curl http://localhost:8000/mcp
```

### Issue 2: "Database is locked" Error

**Symptoms**: SQLite error in logs

**Solution**:
```bash
# Close other processes accessing argo_data.db
lsof | grep argo_data.db

# Verify database integrity
sqlite3 Backend/data/argo_data.db ".tables"

# Rebuild if corrupted:
cd Backend
python rag_setup.py  # Rebuilds from NetCDF
```

### Issue 3: LLM Generating Invalid SQL

**Symptoms**: "Query rejected" in response

**Solution**:
- Update system prompt in `LangGraph_Bot.py` line 54-87
- Add example queries to RAG context
- Use few-shot examples: "For salinity queries, use: SELECT platform_number, AVG(psal) FROM..."

### Issue 4: CORS Errors on Frontend

**Symptoms**: Browser console shows "Cross-Origin Request Blocked"

**Solution**:
```python
# In main.py, verify CORS is configured:
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Or specific: ['http://localhost:5173']
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 5: Slow Query Response

**Symptoms**: >10 second wait for response

**Debugging**:
```bash
# Check if LLM is throttled (Groq API rate limit)
# Check database size
du -h Backend/data/argo_data.db

# Profile slow queries:
sqlite3 Backend/data/argo_data.db "EXPLAIN QUERY PLAN SELECT ..."

# Add indexes if needed:
sqlite3 Backend/data/argo_data.db "CREATE INDEX idx_platform ON measurements(platform_number);"
```

---

## 📚 Key Files Reference

| File | Purpose | Lines of Code |
|------|---------|---------------|
| `Backend/mcp_server.py` | MCP tool provider | ~50 |
| `Backend/LangGraph_Bot.py` | Agent orchestrator | ~162 |
| `Backend/main.py` | FastAPI server | ~40 |
| `Backend/rag_setup.py` | RAG initialization | ~150 |
| `Frontend/react-app/src/ChatLayout.jsx` | Chat interface | ~300+ |

---

## ✅ Resume Talking Points

When discussing this project in interviews:

1. **MCP Implementation**:
   > "I implemented a Model Context Protocol server using FastMCP that validates and executes SQL queries. The server enforces security measures like limiting non-aggregate queries to 200 rows and rejecting dangerous statements like DROP/DELETE."

2. **RAG + LLM Integration**:
   > "Integrated a Retrieval-Augmented Generation pipeline with LangGraph that fetches contextual metadata from a vector database before prompting the LLM, improving response accuracy."

3. **Security & Guardrails**:
   > "Implemented query validation middleware using sqlparse to prevent SQL injection, with automatic LIMIT enforcement for performance and security."

4. **Async Architecture**:
   > "Built an async LangGraph agent orchestrator that handles concurrent retrieval, LLM inference, and tool execution with proper state management."

5. **Geospatial Visualization**:
   > "Extracted geospatial data (latitude/longitude) from query results and rendered them on interactive maps for oceanographic data exploration."

---

## 🔗 References

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Chroma Vector Database](https://www.trychroma.com/)
- [ARGO Float Program](https://www.argodatamgt.org/)

---

**Last Updated**: June 24, 2024  
**Author**: Poseidon-RAG Development Team  
**License**: MIT
