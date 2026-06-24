from mcp.server.fastmcp import FastMCP
import sqlite3
import sqlparse
import re
import os

mcp = FastMCP('search_database')

PER_DIR = os.path.join(os.path.dirname(__file__), 'data')
print(PER_DIR)

def isAgg(query: str) :
    parse = sqlparse.parse(query)
    clean_statement = str(parse[0]).strip()
    return bool(re.search(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', clean_statement, re.IGNORECASE))

@mcp.tool()
def execute_query(query: str) -> dict:
    """
    Validates Given query allowing only SELECT Statements and Rejecting Query involving other Keywords like
    DROP,DELETE,ALTER,etc.Also allows max of 1000 rows as results for non aggregate queries.
    Returns result as a dictionary
    """

    parse = sqlparse.parse(query)
    if not parse or parse[0].get_type() != 'SELECT' :
        return {'result': []}
    
    clean_query = str(parse[0]).strip()
    
    if not isAgg(clean_query) :
        if not re.search(r'\b(LIMIT)',clean_query,re.IGNORECASE) :
            if clean_query.endswith(';') :
                clean_query = clean_query[:-1]
            clean_query += ' LIMIT 200;'
    
    try :
        conn = sqlite3.connect(os.path.join(PER_DIR,'argo_data.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        return {'result': []} 

    return {'result': rows}    

if __name__ == "__main__":
    mcp.run(transport='streamable-http',)
