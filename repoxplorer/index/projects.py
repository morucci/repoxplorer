import yaml


class Projects(object):
    def __init__(self, path="/usr/local/etc/projects.yaml"):
        self.data = yaml.load(file(path))
        self.projects = {}
        for elm in self.data:
            pid = elm.keys()[0]
            self.projects[pid] = []
            for prj in elm[pid]:
                 self.projects[pid].append(prj)

    def get_projects(self):
        return self.projects
