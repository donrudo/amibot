class ConfigLoader:
    def __init__(self, path):
        print(f'ConfigLoader: {path}')
        self._path = path

    @property
    def configuration(self):
        return None

    @configuration.setter
    def configuration(self, value):
        pass
