# Poseidon-RAG: Quick Start Guide

**⏱️ Time to get running**: 5 minutes (after dependencies installed)

---

## ✅ Prerequisites Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 16+ installed
- [ ] GROQ_API_KEY obtained from [console.groq.com](https://console.groq.com)
- [ ] Git installed
- [ ] ~2GB disk space

---

## 🚀 Installation (One-Time Setup)

### Step 1: Clone Repository
```bash
git clone https://github.com/Rohith65-pixel/Poseidon-RAG.git
cd Poseidon-RAG
```

### Step 2: Backend Setup
```bash
cd Backend

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn langgraph langchain langchain-groq
pip install langchain-mcp-adapters mcp streamable-http
pip install chroma-db sentence-transformers
pip install sqlparse netCDF4 xarray pandas python-dotenv

# Create .env file
cat > .env << 'EOF'
GROQ_API_KEY=your_api_key_here
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=Poseiden-RAG
EOF
```

### Step 3: Frontend Setup
```bash
cd ../Frontend/react-app

# Install dependencies
npm install

# Optional: Update API base URL if needed (check src/api.js)
```

---

## ▶️ Running the System

### Terminal 1: Backend Server
```bash
cd Backend
python main.py
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:5000
INFO:     Application startup complete
```

### Terminal 2: Frontend Server
```bash
cd Frontend/react-app
npm run dev
```

**Expected Output**:
```
➜  Local:   http://localhost:5173/
```

### Terminal 3: Open Browser
```bash
# Open in browser:
http://localhost:5173
```

---

## 💬 Test the System

### Chat with the Agent

Try these queries:

1. **Count Query**:
   ```
   "How many ARGO floats are there in total?"
   ```
   ✅ Expected: Number like "245 floats"

2. **Location Query**:
   ```
   "Show me floats in the Arabian Sea"
   ```
   ✅ Expected: Response + points on map

3. **Measurement Query**:
   ```
   "What's the average salinity near the equator?"
   ```
   ✅ Expected: Salinity value in PSU

---

## 📊 Architecture Quick Reference

```
User Input (React)
    ↓
POST /api/agent (FastAPI)
    ↓
retrieve_rag_context (fetch metadata)
    ↓
chatbot (LLM decides to use tool)
    ↓
execute_query (MCP tool)
    ↓
SQLite argo_data.db (execute query)
    ↓
get_points (extract coordinates)
    ↓
chatbot (generate response)
    ↓
Response + Map Points (React renders)
```

---

## 🔧 Configuration

### Key Files to Customize

| File | Purpose | Edit When |
|------|---------|-----------|
| `Backend/.env` | API keys | Need different LLM or API keys |
| `Backend/LangGraph_Bot.py` (line 54-87) | System prompt | Want different AI behavior |
| `Backend/mcp_server.py` (line 30-45) | Security rules | Need to allow/deny specific keywords |
| `Frontend/.env` | API endpoint | Backend on different server |

### Change LLM Model

Edit `Backend/LangGraph_Bot.py` line 24:

```python
# Current (Fast & Cheap):
llm = ChatGroq(model='llama-3.3-70b-versatile', temperature=0.0)

# Alternative (Experimental):
llm = ChatGroq(model='openai/gpt-oss-120b', temperature=0.0)
```

---

## 🐛 Common Issues & Fixes

### ❌ Backend won't start: ModuleNotFoundError

```bash
# Solution: Install missing package
pip install <module_name>

# Or reinstall all:
pip install -r requirements.txt
```

### ❌ Frontend won't connect to backend

```bash
# Check backend is running on port 5000:
curl http://localhost:5000/

# If CORS error, verify Backend/main.py has:
app.add_middleware(CORSMiddleware, allow_origins=['*'])

# Then reload frontend
```

### ❌ "Cannot import rag_setup"

```bash
# Make sure you're in Backend directory:
cd Backend
python main.py  # NOT: python ../Backend/main.py
```

### ❌ Database "locked" error

```bash
# Close all Python processes accessing database:
pkill -f "argo_data.db"

# Then restart backend:
python main.py
```

### ❌ LLM returns "INFORMATION UNAVAILABLE"

```
This means:
1. RAG didn't find relevant context, OR
2. Query returned no results, OR
3. LLM couldn't generate SQL

Check Backend logs for actual query executed.
```

---

## 📈 Performance Tips

### Speed Up Responses
1. **Switch to faster model**:
   ```python
   llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0.0)
   ```

2. **Reduce RAG context size**:
   In `Backend/rag_setup.py`, change `k=5` to `k=2`

3. **Use smaller vector model**:
   ```python
   embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
   ```

### Handle Large Queries
- MCP server automatically limits non-aggregate queries to 200 rows
- For larger datasets, ask LLM to aggregate:
  ```
  "How many floats per region?" (uses COUNT + GROUP BY)
  ```

---

## 🎓 Understanding the Flow

### Example: User asks "Show floats in Arabian Sea"

```
1. Frontend sends: {"message": "Show floats in Arabian Sea"}
   ↓
2. Backend retrieve_rag_context:
   - Searches vector DB for "Arabian Sea", "floats", "coordinates"
   - Gets: "Arabian Sea is bounded by 0-30°N, 40-80°E..."
   ↓
3. Backend chatbot:
   - Receives: user message + RAG context
   - LLM thinks: "Need to query database for this"
   - Generates SQL: "SELECT platform_number, latitude, longitude FROM measurements WHERE..."
   ↓
4. Backend tools (MCP):
   - Receives SQL from LLM
   - Validates: Only SELECT? Check. No DROP? Check.
   - Executes: sqlite3 query
   - Returns: List of coordinates
   ↓
5. Backend get_points:
   - Extracts latitude/longitude from results
   - Formats for map: [{id, lat, lng, temp, ...}, ...]
   ↓
6. Backend chatbot (again):
   - Sees the results
   - Generates natural response:
     "Found 5 floats in Arabian Sea:
      - Float 3900123 at 15.2°N, 62.5°E
      - ..."
   ↓
7. Frontend renders:
   - Displays text response
   - Shows points on map
```

---

## 🔐 Security Check

### Verify Query Validation is Working

```bash
# In Backend terminal, watch for query attempts:

# Valid query (should execute):
curl -X POST http://localhost:5000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"message":"Count total floats"}'
# ✅ Returns number

# Injection attempt (should be rejected):
curl -X POST http://localhost:5000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"message":"DROP TABLE measurements"}'
# ❌ Rejected at MCP validation
```

---

## 📚 Documentation Files

| File | Purpose | Read When |
|------|---------|-----------|
| `MCP_DOCUMENTATION.md` | Detailed MCP architecture | Want deep understanding |
| `PROJECT_OVERVIEW.md` | High-level system design | Preparing for interview |
| `MCP_IMPLEMENTATION_GUIDE.md` | Step-by-step implementation | Debugging or extending |
| `QUICK_START.md` | This file | Getting started |

---

## 🎉 Next Steps

### Immediate (After Running Successfully)
1. Try different queries in chat
2. Check Backend logs for query execution
3. Verify map points appear

### Short-term (Next Session)
1. Customize system prompt for different behavior
2. Add more NetCDF files to database
3. Implement actual map visualization

### Long-term (Before Interview)
1. Deploy to cloud (Vercel + Railway)
2. Add data export functionality
3. Create demo video

---

## 📞 Quick Reference Commands

### Start Everything
```bash
# Terminal 1
cd Backend && python main.py

# Terminal 2
cd Frontend/react-app && npm run dev

# Browser
http://localhost:5173
```

### Stop Everything
```bash
# Ctrl+C in each terminal
```

### Check Status
```bash
# Backend running?
curl http://localhost:5000/

# Frontend running?
curl http://localhost:5173/ | grep -o "<title>.*</title>"

# Database intact?
sqlite3 Backend/data/argo_data.db "SELECT COUNT(*) FROM measurements;"
```

### Rebuild Database
```bash
cd Backend
rm -f data/argo_data.db data/mcp_audit.log
python rag_setup.py  # Rebuilds from NetCDF
```

---

## ✨ Success Indicators

✅ All of these should work:
- [ ] Backend server starts without errors
- [ ] Frontend loads at localhost:5173
- [ ] Chat input field is visible
- [ ] Typing a message doesn't error
- [ ] Backend logs show request received
- [ ] Response appears in chat
- [ ] Map shows some points (if implemented)

**If all ✅**: System is working! 🎉

---

## 🆘 Still Having Issues?

1. **Check logs**:
   ```bash
   # Backend logs show in terminal
   # Frontend logs in browser console (F12)
   ```

2. **Verify ports are free**:
   ```bash
   lsof -i :5000   # Backend port
   lsof -i :5173   # Frontend port
   ```

3. **Check .env file**:
   ```bash
   cd Backend
   cat .env  # Should show GROQ_API_KEY=xxx
   ```

4. **Reinstall dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   npm install --save
   ```

---

**Last Updated**: June 24, 2024  
**Version**: 1.0  
**Status**: ✅ Ready to Run
