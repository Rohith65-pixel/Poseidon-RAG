from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from LangGraph_Bot import graph,HumanMessage
import uvicorn


app = FastAPI()
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel) :
    message: str

@app.get('/')
def home() :
    return {'response' : 'Agent is running'}

@app.post('/api/agent')
def process_req(data: ChatInput) :
    input = {'messages':[HumanMessage(content=data.message)]}
    print(data)
    res = graph.invoke(input)

    return {'response' : res['messages'][-1].content}

if __name__ == '__main__':
    uvicorn.run(app,port=8000)