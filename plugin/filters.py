from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from playnite import Game

HIDDEN_FILTER = 'hidden'
INSTALLED_FILTER = 'installed'
SOURCE_FILTER = 'source'


class LibraryFilter:

    def __init__(self, invert: bool = False):
        self.invert = invert

    def filter(self, game: 'Game') -> bool:
        pass

    def __call__(self, game: 'Game') -> bool:
        if self.invert:
            return not self.filter(game)
        return self.filter(game)

class IsHidden(LibraryFilter):

    def filter(self, game: 'Game') -> bool:
        return game.Hidden

class IsInstalled(LibraryFilter):

    def filter(self, game: 'Game') -> bool:
        return game.IsInstalled

class IsSource(LibraryFilter):

    def __init__(self, source: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = source

    def filter(self, game: 'Game') -> bool:
        if game.Source is not None:
            return game.Source["Name"].lower() == self.source.lower()
        return False

FILTERS = {
    HIDDEN_FILTER: IsHidden,
    INSTALLED_FILTER: IsInstalled,
    SOURCE_FILTER: IsSource,
}

def filter_game(filters: List[LibraryFilter], game: "Game", query: str = None) -> bool:
    for filter in filters:
        if not isinstance(filter, LibraryFilter):
            filter = filter()
        if not filter(game):
            return False
    return True