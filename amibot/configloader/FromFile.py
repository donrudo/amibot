from configloader import ConfigLoader
import yaml


class FromFile(ConfigLoader):

    def __init__(self, path):
        super().__init__(path)

    @property
    def configuration(self):
        with open(self._path, "r") as stream:
            configuration = None
            try:
                configuration = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"FromFile.configuration Exception: {exc}")
        return configuration
