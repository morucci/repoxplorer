# Server Specific Configurations
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'static_root': '%(confdir)s/../../public',
    'template_path': '%(confdir)s/../../templates',
    'debug': True,
    'errors': {
        '404': '/error/404',
        '__force_dict__': True
    }
}

projects_file_path = None
idents_file_path = None
