import os
from unittest import TestCase
from pecan import set_config
from pecan.testing import load_test_app

__all__ = ['FunctionalTest']


class FunctionalTest(TestCase):

    def setUp(self):
        self.app = load_test_app(os.path.join(
            os.path.dirname(__file__),
            '/fixtures/config.py'
        ))

    def tearDown(self):
        set_config({}, overwrite=True)
