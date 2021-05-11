import json

from fastapi.testclient import TestClient
from pymongo import MongoClient
from pytest import fixture

from .database import get_mongo_uri, get_database, db
from .main import app


async def override_get_database():
    yield await get_database('test_articles')


@fixture(scope='session')
def test_client():
    """Create a FastAPI test client for all the tests"""
    app.dependency_overrides[get_database] = override_get_database
    with TestClient(app) as test_client:
        yield test_client


@fixture(autouse=True)
def articles_db():
    """Create a synchronous DB connection for tests"""
    db_client = MongoClient(get_mongo_uri())
    articles_db = db_client['test_articles'].articles

    # Clear DB before every test
    articles_db.delete_many({})
    yield articles_db

    # Clear DB after all tests finish
    articles_db.delete_many({})
    return


class TestArticleViews:
    def test_view_can_create_valid_articles(self, test_client, articles_db):
        # First POST request
        payload = {
            'content': 'Remember to keep all windows open for my Hogwarts letter',
            'tags': ['hogwarts', 'school-stuff', 'Privet-Stuff']
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )
        assert response.status_code == 200
        assert articles_db.count_documents({}) == 1

        # Second POST request
        payload = {
            'content': 'Hide my wand',
            'tags': ['privet-stuff']
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 200
        assert articles_db.count_documents({}) == 2
        assert len(articles_db.distinct('tags', {})) == 3

    def test_view_converts_tags_to_lower_case_and_does_not_create_duplicate_tags(self, test_client, articles_db):
        payload = {
            'content': "Remember to keep all windows open for my Hogwart's letter!",
            'tags': ['hogwarts', 'SChool-stUFF', 'Hogwarts']
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 200
        assert articles_db.count_documents({}) == 1
        assert len(articles_db.distinct('tags', {})) == 2
        assert set(articles_db.distinct('tags', {})) == {'hogwarts', 'school-stuff'}

    def test_view_does_not_save_articles_with_invalid_characters(self, test_client, articles_db):
        # First invalid payload with a '/'
        payload = {
            'content': "Gonna try and crash the server with a '/' >:D",
            'tags': ['hog/warts', 'Hogwarts']
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 422
        assert articles_db.count_documents({}) == 0
        assert len(articles_db.distinct('tags', {})) == 0

        # Second invalid payload with a '?'
        payload = {
            'content': "One of the tags contains a '?'",
            'tags': ['school?q=hogwarts', 'Hogwarts']
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 422
        assert articles_db.count_documents({}) == 0
        assert len(articles_db.distinct('tags', {})) == 0

    def test_view_saves_articles_with_empty_list_for_tags(self, test_client, articles_db):
        payload = {
            'content': 'A article without a tag, is like a needle in a haystack.',
            'tags': []
        }
        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 200
        assert articles_db.count_documents({}) == 1
        assert len(articles_db.distinct('tags', {})) == 0

    def test_view_can_save_articles_without_a_tag_item(self, test_client, articles_db):
        payload = {
            'content': 'All content, no tags',
        }
        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 200
        assert articles_db.count_documents({}) == 1
        assert len(articles_db.distinct('tags', {})) == 0

    def test_view_does_not_save_articles_with_tags_in_the_wrong_format(self, test_client, articles_db):
        payload = {
            'content': 'Try to pass off a single tag instead of a list',
            'tags': 'I am a TAG!'
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 422
        assert articles_db.count_documents({}) == 0
        assert len(articles_db.distinct('tags', {})) == 0

    def test_view_does_not_save_articles_which_are_completely_in_the_wrong_format(self, test_client, articles_db):
        # First incorrect payload
        payload = {
            'amazing-content': 'I have chosen not to follow any formats! Down with the system!'
        }

        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 422
        assert articles_db.count_documents({}) == 0
        assert len(articles_db.distinct('tags', {})) == 0

        # Second incorrect payload
        payload = "This payload ain't even JSON formatted!"
        response = test_client.post(
            url='/v1/article',
            data=json.dumps(payload),
        )

        assert response.status_code == 422
        assert articles_db.count_documents({}) == 0
        assert len(articles_db.distinct('tags', {})) == 0

    def test_view_shows_all_articles_correctly(self, test_client, articles_db):
        # Create 3 tags and 2 articles
        articles_db.insert_many([
            {'id_int': 1, 'content': 'Remind Snape to check his email! Ssssssss', 'tags': ['Snape', 'Kill Dumbledore']},
            {'id_int': 2, 'content': 'Purchase Harry Potter dartboard on Lazada', 'tags': ['Harry']},
        ])

        response = test_client.get('/v1/article')
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[1]['content'] == 'Purchase Harry Potter dartboard on Lazada'
        assert response.json()[0]['tags'] == ['Snape', 'Kill Dumbledore']

    def test_view_shows_empty_list_if_no_articles(self, test_client, articles_db):
        response = test_client.get('/v1/article')
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_view_deletes_all_articles_and_tags_correctly(self, test_client, articles_db):
        # Create 3 tags and 2 articles
        articles_db.insert_many([
            {'id_int': 1, 'content': 'Remind Snape to check his email! Ssssssss', 'tags': ['Snape', 'Kill Dumbledore']},
            {'id_int': 2, 'content': 'Purchase Harry Potter dartboard on Lazada', 'tags': ['Harry']},
        ])

        assert articles_db.count_documents({}) == 2
        assert len(articles_db.distinct('tags', {})) == 3

        response = test_client.delete('/v1/article')
        assert response.status_code == 204
        assert not response.content
        assert articles_db.count_documents({}) == 0
        assert len(articles_db.distinct('tags', {})) == 0


class TestSingleArticleViews:
    def create_n_articles_and_tags(self, n, articles_db):
        # Create n tags and n articles
        new_article_ids = []
        for i in range(n):
            new_article = articles_db.insert_one({'id_int': i+1, 'content': f'article{i+1}', 'tags': [f'Tag{i+1}']})
            new_article_ids.append(new_article.inserted_id)
        return new_article_ids

    def test_view_can_display_correct_article(self, test_client, articles_db):
        # Create 3 test articles and tags
        new_article_ids = self.create_n_articles_and_tags(n=3, articles_db=articles_db)

        # Retrieve the 2nd article
        response = test_client.get(f'v1/article/{new_article_ids[1]}')
        assert response.status_code == 200
        assert response.json()['content'] == 'article2'
        assert response.json()['tags'] == ['Tag2']

    def test_view_displays_correct_error_when_article_not_found(self, test_client, articles_db):
        # Create 3 test articles and tags
        self.create_n_articles_and_tags(n=3, articles_db=articles_db)

        # Try to retrieve an unknown article using a GET method
        response = test_client.get('v1/article/999999999999999999999999')

        assert response.status_code == 404
        assert response.json()['message'] == 'article with ID 999999999999999999999999 not found'
        assert response.json()['id'] == '999999999999999999999999'

        # Try to update an unknown article using a PUT method
        response = test_client.put(
            'v1/article/999999999999999999999999',
            data=json.dumps({'content': 'New Stuff', 'tags': []})
        )
        assert response.status_code == 404
        assert response.json()['message'] == 'article with ID 999999999999999999999999 not found'
        assert response.json()['id'] == '999999999999999999999999'

        # Try to delete a 4th article using a DELETE method
        response = test_client.delete('v1/article/999999999999999999999999')
        assert response.status_code == 404
        assert response.json()['message'] == 'article with ID 999999999999999999999999 not found'
        assert response.json()['id'] == '999999999999999999999999'

    def test_view_correctly_updates_a_article_and_deletes_unused_tags(self, test_client, articles_db):
        # Create 3 test articles and tags
        new_article_ids = self.create_n_articles_and_tags(n=3, articles_db=articles_db)

        payload = {
            'content': "I don't like the 2nd article so I wrote a new one!",
            'tags': ['New', 'Down with Tag2']
        }

        # Update only the 2nd article
        response = test_client.put(
            url=f'v1/article/{new_article_ids[1]}',
            data=json.dumps(payload),
        )

        assert response.status_code == 200
        assert articles_db.count_documents({}) == 3
        assert len(articles_db.distinct('tags', {})) == 4
        assert set(articles_db.distinct('tags', {})) == {'Tag1', 'Tag3', 'new', 'down with tag2'}
        assert response.json()['content'] == "I don't like the 2nd article so I wrote a new one!"
        assert set(response.json()['tags']) == {'new', 'down with tag2'}

    def test_view_does_not_update_articles_with_invalid_characters(self, test_client, articles_db):
        # Create 1 test article and tag
        new_article_ids = self.create_n_articles_and_tags(n=1, articles_db=articles_db)

        payload = {
            'content': "Gonna try and crash the server with a '/' >:D",
            'tags': ['hog/warts', 'Hogwarts']
        }

        response = test_client.put(
            url=f'v1/article/{new_article_ids[0]}',
            data=json.dumps(payload),
        )

        assert response.status_code == 422
        assert articles_db.count_documents({}) == 1
        assert len(articles_db.distinct('tags', {})) == 1

        article = articles_db.find_one({})
        assert article['content'] == 'article1'
        assert article['tags'] == ['Tag1']

    def test_view_deletes_correct_article_and_unused_tags(self, test_client, articles_db):
        # Create 3 test articles and tags
        new_article_ids = self.create_n_articles_and_tags(n=3, articles_db=articles_db)

        # Delete the 2nd article
        response = test_client.delete(f'v1/article/{new_article_ids[1]}')
        assert response.status_code == 204
        assert not response.content
        all_articles = articles_db.find({})
        assert {article['content'] for article in all_articles} == {'article1', 'article3'}
        assert set(articles_db.distinct('tags', {})) == {'Tag1', 'Tag3'}

    def test_view_deletes_correct_article_and_leaves_used_tags(self, test_client, articles_db):
        # Create 3 test articles and tags
        new_article_ids = self.create_n_articles_and_tags(n=3, articles_db=articles_db)

        # Create a 4th tag with tags: Tag1, Tag2, Tag3

        article = articles_db.insert_one(
            {
                'id_int': 4,
                'content': 'This 4th article will be deleted in this test',
                'tags': ['Tag1', 'Tag2', 'Tag3']
            }
        )

        # Delete the 4th article
        response = test_client.delete(f'/v1/article/{article.inserted_id}')
        assert response.status_code == 204
        assert not response.content
        all_articles = articles_db.find({})
        assert {article['content'] for article in all_articles} == {'article1', 'article2', 'article3'}
        assert set(articles_db.distinct('tags', {})) == {'Tag1', 'Tag2', 'Tag3'}


class TestTagsView:
    def test_view_shows_all_tags(self, test_client, articles_db):
        # Create 4 tags
        articles_db.insert_many([
            {'id_int': 1, 'content': 'article1', 'tags': ['wizard']},
            {'id_int': 2, 'content': 'article2', 'tags': ['muggle']},
            {'id_int': 2, 'content': 'article2', 'tags': ['dementor']},
            {'id_int': 2, 'content': 'article2', 'tags': ['zombie']},
        ])

        response = test_client.get('v1/tags')

        assert response.status_code == 200
        assert set(response.json()) == {'wizard', 'muggle', 'dementor', 'zombie'}


class TestSingleTagView:
    def create_song_name_articles_with_tags(self, articles_db):
        # Create 3 tags and 3 articles containing songs and artist names
        articles_db.insert_many([
            {'id_int': 1, 'content': 'Battery', 'tags': ['song', 'metallica']},
            {'id_int': 2, 'content': 'Inner Universe', 'tags': ['song', 'yoko kanno']},
            {'id_int': 2, 'content': 'Master of Puppets', 'tags': ['song', 'metallica']},
        ])

    def test_view_can_display_correct_articles(self, test_client, articles_db):
        # Create 3 tags and 3 articles
        self.create_song_name_articles_with_tags(articles_db)

        # Retrieve all articles with the tag 'song'
        response = test_client.get('/v1/article/tag/song')
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert response.json()[0]['content'] == 'Battery'
        assert response.json()[0]['tags'] == ['song', 'metallica']

        # Retrieve all articles with the tag 'yoko kanno'
        response = test_client.get('/v1/article/tag/yoko kanno')
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]['content'] == 'Inner Universe'
        assert response.json()[0]['tags'] == ['song', 'yoko kanno']

        # Retrieve all articles with the tag 'metallica'
        response = test_client.get('/v1/article/tag/metallica')
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[1]['content'] == 'Master of Puppets'
        assert response.json()[1]['tags'] == ['song', 'metallica']

    def test_view_displays_correct_error_when_tag_not_found(self, test_client, articles_db):
        # Create 3 tags and 3 articles
        self.create_song_name_articles_with_tags(articles_db)

        # Retrieve all articles with the tag 'jack black'
        response = test_client.get('/v1/article/tag/jack black')

        assert response.status_code == 200
        assert len(response.json()) == 0
