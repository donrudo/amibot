class ConfigLoader:
    def __init__(self, path):
        self._path = path

    @property
    def configuration(self):
        return None