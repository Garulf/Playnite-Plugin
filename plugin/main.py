import webbrowser
from pathlib import Path

from flox import Flox
from playnite import DEFAULT_PLAYNITE_DIR, PlayniteApp
from result import Result, OpenInPlaynite, LaunchGameContext
from filters import IsInstalled, IsHidden
from exceptions import PlayniteNotFound, LibraryNotFound

PLUGIN_URI = 'playnite://playnite/installaddon/FlowLauncherExporter'

class Playnite(Flox):

    def load_settings(self):
        self.applied_filters = []
        self.playnite_path = self.settings.setdefault('playnite_path', str(DEFAULT_PLAYNITE_DIR))
        self.hide_uninstalled = self.settings.get('hide_uninstalled', True)
        if self.hide_uninstalled:
            self.applied_filters.append(IsInstalled)
        # If has "Show Hidden" setting, hide hidden games
        if not self.settings.get('show_hidden', False):
            self.applied_filters.append(IsHidden(invert=True))
        self.pn = PlayniteApp(self.playnite_path)

    def query(self, query):
        try:
            self.load_settings()
            games = self.pn.search(query, self.applied_filters)
            for game in games:
                self.add_item(
                    **Result(game).to_dict()
            )
        except PlayniteNotFound:
            self.add_item(
                title='Playnite not found! Set the path in the settings.',
                subtitle='Open settings.',
                method=self.open_setting_dialog
            )
        except LibraryNotFound:
            self.add_item(
                title='Flow Launcher Exporter not found! Install it in Playnite.',
                subtitle='Click to install now.',
                method=self.uri,
                parameters=[PLUGIN_URI]
            )

    def context_menu(self, data):
        self.load_settings()
        game = self.pn.game(data)
        if game:
            self.add_item(**OpenInPlaynite(game).to_dict())
            self.add_item(**LaunchGameContext(game).to_dict())

    def uri(self, uri):
        webbrowser.open(uri)

if __name__ == "__main__":
    Playnite()
