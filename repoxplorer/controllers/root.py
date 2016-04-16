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
                                          p['name'],
                                          p['branch']))
        histo = c.get_commits_histo(projects=p_filter)
        histo = [{'date': str(d['key_as_string']),
                  'value': str(d['doc_count'])} for d in histo[1]]
        top_authors = c.get_top_authors(projects=p_filter)
        top_authors = [{'email': str(k), 'amount': int(v)}
                       for k, v in top_authors[1].items()]
        top_authors_sorted = sorted(top_authors, key=lambda k: k['amount'],
                                    reverse=True)
        return {'pid': pid,
                'histo': histo,
                'top_authors': top_authors_sorted[:10]}
