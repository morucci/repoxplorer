import yaml


class Users(object):
    def __init__(self, path="/usr/local/etc/idents.yaml"):
        self.users = yaml.load(file(path))
        self.idents = {}

    def get_users(self):
        for user in self.users:
            main_email = user['emails'][0]
            self.idents[main_email] = (main_email, user['name'])
            for email in user['emails'][1:]:
                self.idents[email] = (main_email, user['name'])
        return self.idents
