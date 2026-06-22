import asyncio
import uuid
from storage.postgres import postgres_storage
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service

async def main():
    user_id = uuid.UUID('15fbd066-510b-4794-817b-ea111215bbff')
    queries = [
        'Do you remember that I love mountain biking?',
        'What do you know about me?',
        'I love mountain biking',
        'Tell me what you know about me'
    ]

    print('=== keyword search ===')
    for q in queries:
        results = await postgres_storage.search_memories_keyword(user_id=user_id, query=q, top_k=10)
        print('query:', q)
        print('count', len(results))
        for r in results:
            print('  ', r.id, r.content)

    print('\n=== choma retrieval ===')
    await chroma_storage.connect()
    collection_name = f'memories_{user_id}'
    try:
        collection = chroma_storage.client.get_collection(name=collection_name)
        print('collection exists', collection.name)
    except Exception as e:
        print('collection missing or error', type(e).__name__, str(e))
        collection = chroma_storage.client.get_or_create_collection(name=collection_name)
        print('created empty collection', collection.name)

    print('collection count', collection.count())
    for q in queries:
        emb = await embedding_service.generate_embedding(q)
        res = collection.query(query_embeddings=[emb], n_results=5, include=['documents','metadatas','distances'])
        print('query', q)
        print(res)

asyncio.run(main())
