import webbrowser
from pathlib import Path
from difflib import SequenceMatcher as SM

from flox import Flox, ICON_SETTINGS
from playnite import DEFAULT_PLAYNITE_DIR, PlayniteApp
from result import Result
from filters import IsInstalled, IsHidden

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
        self.load_settings()
        games = self.pn.search(query, self.applied_filters)
        for game in games:
            self.add_item(
                **Result(game).to_dict()
            )

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
