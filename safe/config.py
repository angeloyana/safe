import os
from configparser import ConfigParser
import click

HOME = os.path.expanduser('~')
CONFIG_PATH = os.path.join(click.get_app_dir('safe'), 'config.ini')

config = ConfigParser()

if os.path.isfile(CONFIG_PATH):
    config.read(CONFIG_PATH)
else:
    storage_path = os.path.join(HOME, '.safe')
    config['path'] = {
        'password': os.path.join(storage_path, 'safe.key'),
        'database': os.path.join(storage_path, 'safe.db')
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    os.makedirs(storage_path, exist_ok=True)

    with open(CONFIG_PATH, 'w') as f:
        config.write(f)
