def article_output(article: dict) -> dict:
    """Cleans an article dictionary to convert ObjectIDs to str"""
    return {
        'id': str(article['_id']),
        'content': article['content'],
        'tags': article['tags']
    }
