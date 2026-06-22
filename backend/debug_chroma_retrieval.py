import asyncio
import uuid
from storage.chroma import chroma_storage
from utils.embeddings import embedding_service

async def main():
    user_id = uuid.UUID('15fbd066-510b-4794-817b-ea111215bbff')
    await chroma_storage.connect()
    collection_name = f'memories_{user_id}'
    print('collection_name', collection_name)
    try:
        collection = chroma_storage.client.get_collection(name=collection_name)
        print('collection exists', collection is not None)
    except Exception as e:
        print('get_collection error', type(e).__name__, str(e))
        collection = chroma_storage.client.get_or_create_collection(name=collection_name)
        print('created collection', collection.name)
    print('collection count', collection.count())
    print('ids in collection', collection.get(include=['ids'])['ids'])
    content = 'I love mountain biking'
    emb1 = await embedding_service.generate_embedding(content)
    results1 = collection.query(query_embeddings=[emb1], n_results=5, include=['documents','metadatas','distances'])
    print('results1', results1)
    query = 'Do you remember that I love mountain biking?'
    emb2 = await embedding_service.generate_embedding(query)
    results2 = collection.query(query_embeddings=[emb2], n_results=5, include=['documents','metadatas','distances'])
    print('results2', results2)

asyncio.run(main())
