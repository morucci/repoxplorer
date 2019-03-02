from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.tags import Tags


class TestTags(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(
            index='repoxplorertest',
            index_suffix='tags')
        cls.t = Tags(cls.con)
        cls.tags = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'date': 1410456010,
                'name': 'tag1',
                'repo': 'https://github.com/nakata/monkey.git:mon:master',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
                'date': 1410456011,
                'name': 'tag2',
                'repo': 'https://github.com/nakata/monkey.git:mon:master',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b186',
                'date': 1410456012,
                'name': 'tag3',
                'repo': 'https://github.com/nakata/monkey.git:mon:stable-2',
            },
        ]
        cls.t.add_tags(cls.tags)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_tags(self):
        repos = ['https://github.com/nakata/monkey.git:mon:master']
        ret = self.t.get_tags(repos=repos)
        tag_names = [d['_source']['name'] for d in ret]
        self.assertIn('tag1', tag_names)
        self.assertIn('tag2', tag_names)
        self.assertEqual(len(tag_names), 2)
