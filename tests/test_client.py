# coding: utf-8
import six
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.database import Database
from bson import ObjectId
from datetime import datetime


class ClientTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def tearDown(self):
        super(ClientTestCase, self).tearDown()
        Database().collection_test.remove({})
        Database._instance = None

    def test_insert_a_single_document(self):
        """[ClientTestCase] - insert a single document with client"""

        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        document = {'_id': ObjectId(), 'name': 'shouldbename'}

        db.collection_test.insert(document, callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['ok'], 1.0)
        self.assertIsNone(error)

    def test_insert_a_document_list(self):
        """[ClientTestCase] - insert a list of document with client"""

        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['ok'], 1.0)
        self.assertIsNone(error)

    def test_remove_document_by_id(self):
        """[ClientTestCase] - remove a document by id"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.remove(documents[0]['_id'], callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['ok'], 1.0)
        self.assertIsNone(error)

    def test_remove_document_by_spec(self):
        """[ClientTestCase] - remove a document by spec"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.remove({'name': 'shouldbename'}, callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['ok'], 1.0)
        self.assertIsNone(error)

    def test_update_document(self):
        """[ClientTestCase] - update a document"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'name': 'shouldbename'},
            {'_id': ObjectId(), 'name': 'shouldbename2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.update(documents[0], {'$set': {'name':
            'should be a new name'}}, callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['ok'], 1.0)
        self.assertIsNone(error)

    def test_find_document(self):
        """[ClientTestCase] - find a document"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'someflag': 1},
            {'_id': ObjectId(), 'someflag': 1},
            {'_id': ObjectId(), 'someflag': 2}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find({'someflag': 1}, callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response[0]['_id'], documents[0]['_id'])
        self.assertEquals(response[1]['_id'], documents[1]['_id'])
        self.assertIsNone(error)

    def test_find_one_document(self):
        """[ClientTestCase] - find one document"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find_one({'param': 'shouldbeparam1'},
            callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['_id'], documents[1]['_id'])
        self.assertIsNone(error)

    def test_find_one_document_by_id(self):
        """[ClientTestCase] - find one document by id"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find_one(documents[2]['_id'],
            callback=self.stop)
        response, error = self.wait()

        self.assertEquals(response['_id'], documents[2]['_id'])
        self.assertIsNone(error)

    def test_count_documents_in_find(self):
        """[ClientTestCase] - counting documents in query"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find({"param": 'shouldbeparam1'}).count(callback=self.stop)
        total = self.wait()

        self.assertEquals(total, 2)

    def test_count_all_documents(self):
        """[ClientTestCase] - counting among all documents"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam1'},
            {'_id': ObjectId(), 'param': 'shouldbeparam2'}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.count(callback=self.stop)
        total = self.wait()

        self.assertEquals(total, 3)

    def test_distinct_documents_in_find(self):
        """[ClientTestCase] - distinct documents in query"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam1', 'uuid': 100},
            {'_id': ObjectId(), 'param': 'shouldbeparam1', 'uuid': 100},
            {'_id': ObjectId(), 'param': 'shouldbeparam2', 'uuid': 200}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.find({"param": 'shouldbeparam1'}).distinct('uuid', callback=self.stop)
        distincts = self.wait()

        self.assertEquals(len(distincts), 1)
        self.assertEquals(distincts[0], 100)

    def test_distinct_all_documents(self):
        """[ClientTestCase] - distinct among all documents"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{'_id': ObjectId(), 'param': 'shouldbeparam1', 'uuid': 100},
            {'_id': ObjectId(), 'param': 'shouldbeparam1', 'uuid': 100},
            {'_id': ObjectId(), 'param': 'shouldbeparam2', 'uuid': 200}]

        db.collection_test.insert(documents, callback=self.stop)
        response, error = self.wait()

        db.collection_test.distinct('uuid', callback=self.stop)
        distincts = self.wait()

        self.assertEquals(len(distincts), 2)
        self.assertEquals(distincts[0], 100)
        self.assertEquals(distincts[1], 200)

    def test_aggregate_collection(self):
        """[ClientTestCase] - aggregate command"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')

        documents = [{
            "title": "this is my title",
            "author": "bob",
            "posted": datetime.now(),
            "pageViews": 5,
            "tags": ["good", "fun"],
        }, {
            "title": "this is my title",
            "author": "joe",
            "posted": datetime.now(),
            "pageViews": 5,
            "tags": ["good"],
        }]

        db.articles.insert(documents, callback=self.stop)
        response, error = self.wait()

        try:
            pipeline = {
                "$project": {
                     "author": 1,
                     "tags": 1,
                }
            }, {
                "$unwind": "$tags"
            }, {
                "$group": {
                     "_id": {"tags": "$tags"},
                     "authors": {"$addToSet": "$author"}
                }
            }
            db.articles.aggregate(pipeline, callback=self.stop)

            response = self.wait()

            self.assertEquals(response['result'][0]['_id'], {'tags': 'fun'})
            self.assertEquals(response['result'][0]['authors'], ['bob'])

            self.assertEquals(response['result'][1]['_id'], {'tags': 'good'})
            self.assertEquals(response['result'][1]['authors'], ['joe', 'bob'])
        finally:
            db.articles.remove({}, callback=self.stop)
            self.wait()

    def test_group(self):
        """[ClientTestCase] - group command"""
        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')
        group = {
            'key': None,
            'condition': {'author': 'joe'},
            'initial': {'csum': 0},
            'reduce': 'function(obj,prev){prev.csum+=obj.pageViews;}'
        }

        documents = [{
            "title": "this is my title",
            "author": "bob",
            "posted": datetime.now(),
            "pageViews": 5,
            "tags": ["good", "fun"],
        }, {
            "title": "this is my title",
            "author": "joe",
            "posted": datetime.now(),
            "pageViews": 6,
            "tags": ["good"],
        }, {
            "title": "this is my title",
            "author": "joe",
            "posted": datetime.now(),
            "pageViews": 10,
            "tags": ["good"],
        }]
        db.articles.insert(documents, callback=self.stop)
        response, error = self.wait()

        try:
            db.articles.group(callback=self.stop, **group)
            result = self.wait()
            self.assertEquals(result['retval'][0]['csum'], 16)
        finally:
            db.articles.remove({}, callback=self.stop)
            self.wait()

    def test_insert_and_find_with_elemmatch(self):
        documents = [{
            '_id': ObjectId(),
            'name': 'should be name 1',
            'comment': [{'author': 'joe'}, {'author': 'ana'}]
        }, {
            '_id': ObjectId(),
            'name': 'should be name 2',
            'comment': [{'author': 'ana'}]
        }]

        db = Database.init(["localhost:27027", "localhost:27028"],
            dbname='test')
        db.articles.insert(documents, callback=self.stop)
        self.wait()

        db.articles.find({'comment.author': 'joe'}, ('comment.$.author', ), limit=-1, callback=self.stop)

        result, _ = self.wait()

        keys = list(six.iterkeys(result))
        keys.sort()

        self.assertEquals(keys, ['_id', 'comment'])

        self.assertEquals(str(result['_id']), str(documents[0]['_id']))
        self.assertEquals(len(result['comment']), 1)
        self.assertEquals(result['comment'][0]['author'], 'joe')
        self.assertIsNone(_)
