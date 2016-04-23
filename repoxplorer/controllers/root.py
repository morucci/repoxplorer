from pecan import expose
from datetime import datetime

from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.users import Users


class RootController(object):

    @expose(template='index.html')
    def index(self):
        projects = Projects().get_projects()
        return {'projects': projects}

    def top_authors_sanitize(self, top_authors):
        idents = Users().get_users()
        sanitized = {}
        for k, v in top_authors[1].items():
            if k in idents:
                main_email = idents[k][0]
                name = idents[k][1]
                amount = int(v[0])
            else:
                main_email = str(k)
                name = v[1].encode('ascii', errors='ignore')
                amount = int(v[0])
            if k in sanitized:
                amount += sanitized[k][0]
            sanitized[main_email] = [amount, name]
        top_authors_s = []
        for k, v in sanitized.items():
            top_authors_s.append({'email': str(k),
                                  'amount': v[0],
                                  'name': str(v[1])})
        top_authors_s_sorted = sorted(top_authors_s,
                                      key=lambda k: k['amount'],
                                      reverse=True)
        return top_authors_s_sorted

    @expose(template='project.html')
    def project(self, pid, dfrom=None, dto=None):
        odfrom = None
        odto = None
        if dfrom:
            odfrom = dfrom
            dfrom = datetime.strptime(
                dfrom, "%m/%d/%Y").strftime('%s')
        if dto:
            odto = dto
            dto = datetime.strptime(
                dto, "%m/%d/%Y").strftime('%s')
        c = Commits(index.Connector())
        projects = Projects().get_projects()
        project = projects[pid]
        p_filter = []
        for p in project:
            p_filter.append("%s:%s:%s" % (p['uri'],
                                          p['name'],
                                          p['branch']))
        histo = c.get_commits_histo(projects=p_filter,
                                    fromdate=dfrom,
                                    todate=dto)
        histo = [{'date': str(d['key_as_string']),
                  'value': str(d['doc_count'])} for d in histo[1]]
        top_authors = c.get_top_authors(projects=p_filter,
                                        fromdate=dfrom,
                                        todate=dto)
        top_authors = self.top_authors_sanitize(top_authors)
        commits_amount = c.get_commits_amount(
            projects=p_filter,
            fromdate=dfrom,
            todate=dto)
        first, last, duration = c.get_commits_time_delta(
            projects=p_filter,
            fromdate=dfrom,
            todate=dto)
        return {'pid': pid,
                'histo': histo,
                'top_authors': top_authors[:25],
                'authors_amount': len(top_authors),
                'commits_amount': commits_amount,
                'first': datetime.fromtimestamp(first),
                'last': datetime.fromtimestamp(last),
                'duration': (datetime.fromtimestamp(duration) -
                             datetime.fromtimestamp(0)),
                'subprojects': len(project),
                'period': (odfrom, odto)}
