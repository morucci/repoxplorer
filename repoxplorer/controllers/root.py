import json

from pecan import conf
from pecan import expose
from pecan.rest import RestController
from pecan.core import abort


class ProjectCtrl(RestController):
    @expose(content_type='application/json')
    def get(self, **kwargs):
        return json.dumps("Hello world")

class RootController(object):

    project = ProjectCtrl()
