import asyncio
from langsmith import aevaluate
from LangGraph_Bot import get_graph,HumanMessage
import os

# TEST_PATH = os.path.join(os.path.dirname(__file__),'data','Argo-Agent-Testing.csv')

async def start_test(inputs: dict) :
    graph = await get_graph()
    input_data = {'messages': [HumanMessage(content=inputs['question'])]}
    # config={'configurable':{'thread_id': "test_thread"}}
    res = await graph.ainvoke(input_data)
    
    return {
        "final_response": res['messages'][-1].content,
        "map_pins_extracted": len(res.get('points', []))
    }

async def main() :
    results = await aevaluate(
        start_test,
        data="Argo-Agent-Testing", 
        description="Testing Token Limits, Tools, and Map Extraction",
        evaluators=[], 
    )

if __name__ == '__main__' :
    asyncio.run(main())