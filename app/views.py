from bson import ObjectId
from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse

from .database import AsyncIOMotorClient, get_database
from .models import Article
from .utils import article_output

router = APIRouter()


@router.post('/article')
async def create_article(article: Article, db: AsyncIOMotorClient = Depends(get_database)):
    result = await db['articles'].insert_one(article.dict())
    return {'id': str(result.inserted_id), **article.dict()}


@router.get('/article')
async def get_all_articles(db: AsyncIOMotorClient = Depends(get_database)):
    return [article_output(article) async for article in db['articles'].find()]


@router.delete('/article')
async def delete_all_articles(db: AsyncIOMotorClient = Depends(get_database)):
    await db['articles'].delete_many({})
    return Response(status_code=204)


@router.get('/article/{id}')
async def get_single_article(id: str, db: AsyncIOMotorClient = Depends(get_database)):
    article = await db['articles'].find_one({'_id': ObjectId(id)})
    if article is not None:
        return article_output(article)
    return JSONResponse(status_code=404, content={'id': id, 'message': f'article with ID {id} not found'})


@router.put('/article/{id}')
async def update_single_article(id: str, new_article: Article, db: AsyncIOMotorClient = Depends(get_database)):
    article = await db['articles'].find_one({'_id': ObjectId(id)})
    if article is not None:
        await db['articles'].update_one(
            filter={'_id': article['_id']},
            update={'$set': {'content': new_article.content, 'tags': new_article.tags}}
        )
        return {'id': id, **new_article.dict()}
    return JSONResponse(status_code=404, content={'id': id, 'message': f'article with ID {id} not found'})


@router.delete('/article/{id}')
async def delete_single_article(id: str, db: AsyncIOMotorClient = Depends(get_database)):
    article = await db['articles'].find_one({'_id': ObjectId(id)})
    if article is not None:
        await db['articles'].delete_one({'_id': article['_id']})
        return Response(status_code=204)
    return JSONResponse(status_code=404, content={'id': id, 'message': f'article with ID {id} not found'})


@router.get('/article/tag/{tag}')
async def get_all_articles_with_tag(tag: str, db: AsyncIOMotorClient = Depends(get_database)):
    query = {'tags': {'$elemMatch': {'$eq': tag}}}
    return [article_output(article) async for article in db['articles'].find(query)]


@router.get('/tags')
async def get_all_tags(db: AsyncIOMotorClient = Depends(get_database)):
    return await db['articles'].distinct('tags', {})
