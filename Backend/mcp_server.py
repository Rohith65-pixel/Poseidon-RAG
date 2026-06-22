from mcp.server.fastmcp import FastMCP
import sqlite3
import sqlparse
import re

mcp = FastMCP('search_database')

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
        return {'result' : 'INVALID SQL QUERY'}
    
    clean_query = str(parse[0]).strip()
    
    
    if not isAgg(clean_query) :
        if not re.search(r'\b(LIMIT)',clean_query,re.IGNORECASE) :
            if clean_query.endswith(';') :
                clean_query = clean_query[:-1]
            clean_query += ' LIMIT 1000;'
    
    with sqlite3.connect('data/argo_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = cursor.fetchall()

    return {'result' : rows}
    

if __name__ == "__main__":
    mcp.run(transport='streamable-http',)
