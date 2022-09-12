from __future__ import annotations

from playnite import Game

class Result:

    def __init__(self, game: Game):
        self.game = game

    @property
    def title(self):
        return self.game.Name

    @property
    def subtitle(self):
        return self.game.InstallDirectory

    @property
    def icon(self):
        return self.game.icon_path

    @property
    def method(self):
        return 'uri'

    @property
    def parameters(self):
        return [self.game.start_uri]

    @property
    def context(self):
        return self.game.Id

    def to_dict(self):
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'icon': self.icon,
            'method': self.method,
            'parameters': self.parameters,
            'context': self.context,
        }

class OpenInPlaynite(Result):

    @property
    def title(self):
        return f'Open in Playnite'

    @property
    def subtitle(self):
        return "Opens the selected game in Playnite"

    @property
    def icon(self):
        return None

    @property
    def method(self):
        return 'uri'

    @property
    def parameters(self):
        return [self.game.show_game_uri]

class LaunchGameContext(Result):
    
        @property
        def title(self):
            return f'Launch Game'
    
        @property
        def subtitle(self):
            return "Launches the selected game"
    
        @property
        def icon(self):
            return None
    
        @property
        def method(self):
            return 'uri'
    
        @property
        def parameters(self):
            return [self.game.start_uri]