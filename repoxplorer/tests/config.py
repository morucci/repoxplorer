import tempfile
from repoxplorer.controllers.renderers import CSVRenderer

# Server Specific Configurations
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'custom_renderers': {'csv': CSVRenderer},
    'static_root': '%(confdir)s/../../public',
    'debug': True,
    'errors': {
        '404': '/error/404',
        '__force_dict__': True
    }
}

projects_file_path = None
git_store = None
db_path = tempfile.mkdtemp()
db_cache_path = tempfile.mkdtemp()
db_default_file = None
xorkey = None
elasticsearch_host = 'localhost'
elasticsearch_port = 9200
elasticsearch_index = 'repoxplorertest'

admin_token = '12345'
