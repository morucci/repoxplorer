import sys

# Backend Server Specific Configurations

# Internal dev pecan server
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan REST and rendering configuration
app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/templates',
    'debug': True,
    'errors': {
        404: '/error/404',
        '__force_dict__': True
    }
}

# Logging configuration
logging = {
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'repoxplorer': {'level': 'DEBUG', 'handlers': ['console'],
                        'propagate': False},
        'pecan': {'level': 'DEBUG', 'handlers': ['console'],
                  'propagate': False},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
            '__force_dict__': True
        }
    }
}

# Additional RepoXplorer configurations
projects_file_path = '%s/local/share/repoxplorer/projects.yaml' % sys.prefix
idents_file_path = '%s/local/share/repoxplorer/idents.yaml' % sys.prefix
git_store = '%s/local/share/repoxplorer/git_store' % sys.prefix
elasticsearch_host = 'localhost'
elasticsearch_port = 9200
elasticsearch_index = 'repoxplorer'
