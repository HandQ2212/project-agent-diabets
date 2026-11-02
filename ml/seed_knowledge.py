"""Seed knowledge documents into Neo4j graph with vector embeddings."""
import json
import logging
from pathlib import Path
from backend.app.rag import driver, embed

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def seed(path: str = 'knowledge/sources.json'):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    log.info(f"Loaded {len(data)} documents from {path}")
    
    with driver() as db:
        # Create constraint for Document id
        db.execute_query(
            'CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE',
            database_='neo4j'
        )
        # Create constraint for Topic name
        db.execute_query(
            'CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE',
            database_='neo4j'
        )
        
        count = 0
        for doc in data:
            log.info(f"Embedding and upserting: [{doc['id']}] {doc['title']}")
            vector = embed(doc['text'])
            db.execute_query(
                '''
                MERGE (d:Document {id: $id})
                SET d.title = $title,
                    d.url = $url,
                    d.text = $text,
                    d.topic = $topic,
                    d.date = $date,
                    d.license = $license,
                    d.embedding = $embedding
                MERGE (t:Topic {name: $topic})
                MERGE (d)-[:ABOUT]->(t)
                ''',
                id=doc['id'],
                title=doc['title'],
                url=doc['url'],
                text=doc['text'],
                topic=doc['topic'],
                date=doc.get('date', ''),
                license=doc.get('license', ''),
                embedding=vector,
                database_='neo4j'
            )
            count += 1
            
    print(f"Successfully loaded and embedded {count} documents into Neo4j.")

if __name__ == '__main__':
    seed()
