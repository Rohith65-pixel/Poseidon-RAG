from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from LangGraph_Bot import get_graph,HumanMessage
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
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
async def process_req(data: ChatInput) :
    config = {"configurable": {"thread_id": "thread-1"}}
    input = {'messages':[HumanMessage(content=data.message)]}
    print(f"Received: {data}")
    try :
        graph = await get_graph()
        res = await graph.ainvoke(input=input)
    except Exception as e:
        print("LLM ERROR:",str(e))
        return  {
                    'response' : f"An error occurred while processing your request. {str(e)}",
                }

    return  {
                'response' : res['messages'][-1].content,
                'points' : res.get('points', []),
                'csv_data' : res.get('csv_data', [])
            }

if __name__ == '__main__':
    uvicorn.run(app,port=5000)