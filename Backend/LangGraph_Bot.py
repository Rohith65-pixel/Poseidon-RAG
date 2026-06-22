from langgraph.graph import START,END,StateGraph,MessagesState
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage,HumanMessage
from typing import Annotated,TypedDict

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')

from rag_setup import retriever,PER_DIR

llm = ChatGroq(model='llama-3.3-70b-versatile',temperature=0.0)

class AgentState(MessagesState) :
    rag_context: str

@tool
def execute_query(query: str) -> str:
    """
        The query parameter must be strict SQLite syntax based query to retrieve releveant data based on user's request
        The output is results of the query in string format
    """

    try :
        conn = sqlite3.connect(os.path.join(PER_DIR,'argo_data.db'))
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()    
        return str(rows)
    except Exception as e:
        conn.close()
        return f'INVALID QUERY!! {str(e)}'
    

tools = [execute_query]
tool_node = ToolNode(tools)
llm_with_tools = llm.bind_tools(tools=tools)

def retrive_rag_context(state: AgentState) :
    message = state['messages'][-1].content
    context_msg = '\n'.join([doc.page_content for doc in retriever.invoke(message)])
    return  {
                'rag_context' : context_msg
            }      

def chatbot(state: AgentState) :
    message = state['messages']
    rag_context = state.get('rag_context','')
    
    system_prompt = SystemMessage(content=f"""
    You are an expert oceanographic AI assistant managing an Argo float database table named 'measurements'.
    
    Database Schema Layout:
    - Platform_number: Unique ID string for the Argo robot float.
    - temp: Sea water temperature in Celsius.
    - psal: Practical Salinity (PSAL) in PSU.
    - pres: Water pressure in decibars (dbar), directly representing ocean depth.
    - latitude: Numeric coordinate.
    - longitude: Numeric coordinate.
    
    Live Database Context (From RAG):
    {rag_context}
    
    Analyze the context provided above to identify platform numbers or coordinates, write a valid SQLite query, and execute it using 'execute_query' to fetch the actual numbers before giving an answer.
    If you don't have enough information/context or can't find any useful data return 'INFORMATION UNAVAILABLE'
    CRITICAL RULE: Never return thousands of rows. If querying raw measurements, ALWAYS append 'LIMIT 10' to your query unless you are using math aggregations like AVG() or COUNT().
       """)

    return  {
                'messages' : [llm_with_tools.invoke([system_prompt] + message)]
            }

graph_builder = StateGraph(AgentState)

graph_builder.add_node('retrive_rag_context',retrive_rag_context)
graph_builder.add_node('chatbot',chatbot)
graph_builder.add_node('tools',tool_node)

graph_builder.add_edge(START,'retrive_rag_context')
graph_builder.add_edge('retrive_rag_context','chatbot')
graph_builder.add_conditional_edges('chatbot',tools_condition)
graph_builder.add_edge('tools','chatbot')

graph = graph_builder.compile()

if __name__ == '__main' :
    inputs = {
        "messages": [HumanMessage(content="How many floats are there in Atlantic Ocean?")]
    }

    for event in graph.stream(inputs, stream_mode='updates'):
        for node_name, state_update in event['messages']:
            if 'messages' in state_update:
                for msg in state_update['messages']:
                    print(f"\n--- [Node: {node_name}] Output ---")
                    msg.pretty_print()



