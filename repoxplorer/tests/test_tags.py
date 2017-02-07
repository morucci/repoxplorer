from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.tags import Tags


class TestTags(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.t = Tags(cls.con)
        cls.tags = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'date': 1410456010,
                'name': 'tag1',
                'project': 'https://github.com/nakata/monkey.git:monkey:master',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
                'date': 1410456011,
                'name': 'tag2',
                'project': 'https://github.com/nakata/monkey.git:monkey:master',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b186',
                'date': 1410456012,
                'name': 'tag3',
                'project': 'https://github.com/nakata/monkey.git:monkey:stable-2.3',
            },
        ]
        cls.t.add_tags(cls.tags)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_tags(self):
        projects = ['https://github.com/nakata/monkey.git:monkey:master']
        ret = self.t.get_tags(projects=projects)
        tag_names = [d['_source']['name'] for d in ret]
        self.assertIn('tag1', tag_names)
        self.assertIn('tag2', tag_names)
        self.assertEqual(len(tag_names), 2)
