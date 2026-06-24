from argopy import status
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

import sqlite3
import os

PER_DIR = os.path.join(os.path.dirname(__file__), 'data')
VECTOR_DB_DIR = os.path.join(PER_DIR,'argo_vector_db')

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

conn = sqlite3.connect(os.path.join(PER_DIR,'argo_data.db'))
cursor = conn.cursor()

query = '''
    SELECT 
        Platform_number,
        COUNT(*) as total_readings,
        ROUND(MIN(temp), 2) as min_temp,
        ROUND(MAX(temp), 2) as max_temp,
        ROUND(MIN(psal), 2) as min_sal,
        ROUND(MAX(psal), 2) as max_sal,
        ROUND(MIN(pres), 1) as min_pres,
        ROUND(MAX(pres), 1) as max_pres,
        ROUND(AVG(latitude), 4) as avg_lat,
        ROUND(AVG(longitude), 4) as avg_lon,
        time
    FROM measurements
    GROUP BY Platform_number
'''

cursor.execute(query)
rows = cursor.fetchall()

def get_sub_region(lat, lon):
    if lat > 0 and 45 <= lon <= 80: return "Arabian Sea"
    elif lat > 0 and 80 < lon <= 100: return "Bay of Bengal"
    elif -10 <= lat <= 10: return "Equatorial Indian Ocean"
    elif lat < -10: return "Southern Indian Ocean Basin"
    return "Indian Ocean Open Basin"

docs = []
for row in rows:
    float_id = row[0]
    
    region_tag = get_sub_region(row[8], row[9])
    
    page_content = (
        f"Oceanographic profile data summary for Argo float platform ID: {float_id}.\n"
        f"Temporal context: Observed on {row[-1]}.\n"
        f"Geospatial region: Located within the {region_tag} region at coordinates (Latitude: {row[8]}, Longitude: {row[9]}).\n"
        f"Sampling metric: Captured {row[1]} discrete hydrographic column observations.\n"
        f"Vertical profile scale: Spans ocean pressures from a minimum surface boundary of {row[6]} dbar down to a maximum depth boundary of {row[7]} dbar.\n"
        f"Thermodynamic profile parameters: Sea water temperature ranges from a minimum of {row[2]}°C in the deep layers up to a maximum sea surface temperature of {row[3]}°C.\n"
        f"Haline profile parameters: Practical Salinity (PSAL) measurements within this vertical column range from a minimum of {row[4]} PSU to a maximum of {row[5]} PSU."
    )
    
    metadata = {
        "platform_number": float_id,
        "region": region_tag,
        "date": row[-1],
        "max_depth": row[7]
    }
    
    doc = Document(page_content=page_content, metadata=metadata)
    docs.append(doc)

vector_db = None
if os.path.exists(VECTOR_DB_DIR) and 'argo_vector_db' in os.listdir(PER_DIR) :
    print("Loading existing Vector Database...")
    vector_db = Chroma(
                    persist_directory=VECTOR_DB_DIR, 
                    embedding_function=embeddings
                )
else :
    print("Creating new Vector Database and generating embeddings...")
    vector_db = Chroma.from_documents(
                    embedding=embeddings,
                    documents=docs,
                    persist_directory=VECTOR_DB_DIR
            )

retriever = vector_db.as_retriever()
print("Vector pipeline successfully built and ready for RAG query processing!")

if __name__ == '__main__' :
    test_query = "Find me a float operating in the Arabian Sea that dives deep down past 1500 dbar"
    
    matching_docs = retriever.invoke(test_query)
    
    if matching_docs:
        print("=== CRITICAL RAG CONTEXT FOUND ===")
        print(matching_docs[0].page_content)
        print("\n=== ASSOCIATED METADATA ===")
        print(matching_docs[0].metadata)
    else:
        print("No matching documents found. Double check your database initialization!")