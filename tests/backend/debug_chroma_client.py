import asyncio
import uuid
from storage.chroma import chroma_storage
from storage.postgres import postgres_storage
from utils.embeddings import embedding_service

async def main():
    user_id = uuid.UUID('15fbd066-510b-4794-817b-ea111215bbff')
    await chroma_storage.connect()
    coll_name = f'memories_{user_id}'
    print('collection name', coll_name)
    print('client', type(chroma_storage.client))
    print('client attrs', [a for a in dir(chroma_storage.client) if a.startswith('get_')][:10])
    try:
        col1 = chroma_storage.client.get_collection(name=coll_name)
        print('get_collection count', col1.count())
        print('get_collection get', col1.get(include=['documents','metadatas','distances']))
    except Exception as e:
        print('get_collection error', type(e).__name__, str(e))

    try:
        col2 = chroma_storage.client.get_or_create_collection(name=coll_name)
        print('get_or_create_collection count', col2.count())
        print('get_or_create_collection get', col2.get(include=['documents','metadatas','distances']))
    except Exception as e:
        print('get_or_create_collection error', type(e).__name__, str(e))

    try:
        col3 = chroma_storage._get_collection(user_id)
        print('_get_collection count', col3.count())
        print('_get_collection get', col3.get(include=['documents','metadatas','distances']))
    except Exception as e:
        print('_get_collection error', type(e).__name__, str(e))

    # query exact content
    query = 'I love mountain biking'
    emb = await embedding_service.generate_embedding(query)
    for name, col in [('col1', locals().get('col1')), ('col2', locals().get('col2')), ('col3', locals().get('col3'))]:
        if col is None:
            continue
        try:
            res = col.query(query_embeddings=[emb], n_results=5, include=['documents','metadatas','distances'])
            print(name, 'query', res)
        except Exception as e:
            print(name, 'query error', type(e).__name__, str(e))

asyncio.run(main())
