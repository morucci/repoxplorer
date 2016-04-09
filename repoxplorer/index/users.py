import yaml


class Users(object):
    def __init__(self, path=None):
        assert path is not None
        self.users = yaml.load(file(path))

    def get_users(self):
        return self.users
