from pecan import expose

from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects


class RootController(object):

    @expose(template='index.html')
    def index(self):
        projects = Projects().get_projects()
        return {'projects': projects}

    @expose(template='project.html')
    def project(self, pid=None):
        c = Commits(index.Connector())
        projects = Projects().get_projects()
        project = projects[pid]
        p_filter = []
        for p in project:
            p_filter.append("%s:%s:%s" % (p['uri'],
                p['name'], p['branch']))
        histo = c.get_commits_histo(projects=p_filter)
        return {'pid': pid,
                'histo': histo}
