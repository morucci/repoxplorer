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
    'root': {'level': 'DEBUG', 'handlers': ['normal']},
    'loggers': {
        'repoxplorer': {'level': 'DEBUG', 'handlers': ['normal', 'console']},
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'normal': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'normal',
            'filename': '/var/log/repoxplorer/repoxplorer.log',
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
        },
    },
    'formatters': {
        'console': {'format': ('%(levelname)-5.5s [%(name)s]'
                    '[%(threadName)s] %(message)s')},
        'normal': {'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                   '[%(threadName)s] %(message)s')},
    }
}

# Additional RepoXplorer configurations
projects_file_path = '%s/local/share/repoxplorer/projects.yaml' % sys.prefix
idents_file_path = '%s/local/share/repoxplorer/idents.yaml' % sys.prefix
git_store = '%s/local/share/repoxplorer/git_store' % sys.prefix
elasticsearch_host = 'localhost'
elasticsearch_port = 9200
elasticsearch_index = 'repoxplorer'
