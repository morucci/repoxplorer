from repoxplorer.tests import FunctionalTest


class TestRootController(FunctionalTest):

    def test_get(self):
        response = self.app.get('/')
        assert response.status_int == 200
