
class LibraryNotFound(Exception):
    
    def __init__(self, library):
        self.library = library

    def __str__(self):
        return f"No library file not found for {self.library}"

class PlayniteNotFound(Exception):
    
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"Playnite directory not found at {self.path}"