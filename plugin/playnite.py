import json
from pathlib import Path
import os
import webbrowser


SCRIPT_NAME = 'FlowLauncherExporter'
DATA_FOLDER = Path(os.getenv('APPDATA'), 'Playnite')
PLUGIN_NAME = 'FlowLauncher_Exporter'


def import_games(data_folder=DATA_FOLDER, file_name='library.json'):
    library_file = Path(data_folder, 'ExtensionsData', SCRIPT_NAME, file_name)
    games = []
    with open(library_file, encoding='utf-8-sig') as f:
        data = json.load(f)
        for game in data:
            # print(game)
            games.append(Game(data_folder, game))
    return games

def camel_to_snake(text):
    return ''.join(['_'+char.lower() if char.isupper() else char for char in text]).lstrip('_')

class Game(object):

    def __init__(self, data_folder, data) -> None:
        self.data_folder = data_folder
        self.data = data
        self.hidden = False
        for key, value in data.items():
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            setattr(self, camel_to_snake(key).lower(), value)
        if self.source is None:
            self.source = {
                'Name': 'Unknown',
            }

    @property
    def start_uri(self):
        return f'playnite://playnite/start/{self.id}'

    @property
    def show_uri(self):
        return f'playnite://playnite/showgame/{self.id}'

    @property
    def icon_path(self):
        if self.icon:
            path = Path(self.data_folder, 'library', 'files', self.icon)
            if path.is_file():
                return path
        return ''

    def start(self):
        webbrowser.open(self.uri)

    def show_game(self):
        webbrowser.open(self.show_uri)


if __name__ == "__main__":
    games = import_games()
    for game in games:
        print(game.icon_path)