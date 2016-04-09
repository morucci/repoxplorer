import yaml


class Projects(object):
    def __init__(self, path="/usr/local/etc/projects.yaml"):
        self.projects = yaml.load(file(path))

    def get_projects(self):
        return self.projects
