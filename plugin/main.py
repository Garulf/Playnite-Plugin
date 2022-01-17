import webbrowser
from pathlib import Path
from difflib import SequenceMatcher as SM

from flox import Flox, ICON_SETTINGS
import playnite as pn


SOURCE_FILTER = '#'
INSTALL_FILTER = '@'
SCORE_CUTOFF = 10
PLUGIN_URI = 'playnite://playnite/installaddon/FlowLauncherExporter'

def match(query, text):
    return int(SM(
                lambda x: x == " ", 
                query.lower(), 
                text.lower()).ratio() * 100
            )

class Playnite(Flox):

    def load_settings(self):
        self.playnite_path = self.settings.setdefault('playnite_path', str(pn.DATA_FOLDER))
        if self.settings.get('playnite_path') == '':
            self.playnite_path = str(pn.DATA_FOLDER)
            self.settings['playnite_path'] = str(pn.DATA_FOLDER)
        self.hide_uninstalled = self.settings.get('hide_uninstalled', True)

    def missing_library(self):
        self.add_item(
            title='Library file not found!',
            subtitle="Please set the path to Playnite\'s data directory in settings.",
            icon=ICON_SETTINGS,
            method=self.open_setting_dialog
        )
        self.add_item(
            title='Install FlowLauncherExporter plugin.',
            subtitle='FlowLauncherExporter plugin is required to use this plugin.',
            icon='',
            method=self.uri,
            parameters=[PLUGIN_URI]

        )

    def main_search(self, query):
        for game in self.games:
            score = match(query, game.name)
            if score >= SCORE_CUTOFF or query == '':
                if game.is_installed:
                    subtitle = game.install_directory
                    uri = game.start_uri
                else:
                    subtitle = 'Not Installed'
                    uri = game.show_uri
                self.add_item(
                    title=game.name,
                    subtitle=f'{game.source["Name"]}: {subtitle}',
                    icon=str(game.icon_path),
                    method=self.uri,
                    parameters=[uri],
                    context=[game.show_uri],
                    score=score
                )

    def source_filter(self, query):
        sources = [game.source['Name'] for game in self.games]
        if query == '':
            for source in set(sources):
                _ = self.add_item(
                    title=f'{SOURCE_FILTER}{source}',
                    subtitle='Filter by source.',
                    icon='',
                    method=self.change_query,
                    dont_hide=True,
                )
                _['JsonRPCAction']['Parameters'] = [f"{_['AutoCompleteText']} "]
                self.games = []
            return q
        for source in sources:
            if source.lower() == query.lower():
                self.games = [game for game in self.games if query.lower() == game.source['Name'].lower()]
                return query.lower().replace(source.lower(), '')


    def install_filter(self):
        self.games = [game for game in self.games if not game.is_installed]

    def uninstalled_filter(self):
        self.games = [game for game in self.games if game.is_installed and (game.install_directory != None or game.install_directory != "")]

    def remove_hidden(self):
        self.games = [game for game in self.games if not game.hidden]

    def query(self, query):
        self.load_settings()
        try:
            self.games = pn.import_games(self.playnite_path)
        except FileNotFoundError:
            self.missing_library()
            return
        if query.startswith(SOURCE_FILTER):
            query = query[len(SOURCE_FILTER):]
            self.source_filter(query)
        elif query.startswith(INSTALL_FILTER):
            query = query[len(INSTALL_FILTER):]
            self.install_filter()
        elif self.hide_uninstalled:
            self.uninstalled_filter()
        self.remove_hidden()
        self.main_search(query)
        

    def context_menu(self, data):
        show_uri = data[0]
        icon = str(self.icon if Path(self.icon).is_absolute() else Path(self.plugindir, self.icon))
        self.logger.warning(icon)
        self.add_item(
            title='Open in Playnite',
            subtitle='Shows Game in Playnite library.',
            icon=icon,
            method=self.uri,
            parameters=[show_uri],
        )

    def uri(self, uri):
        webbrowser.open(uri)

if __name__ == "__main__":
    Playnite()
