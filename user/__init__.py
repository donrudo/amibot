class User:
    """Bot properties to be used, add openAI behaviors
    and user interactions here"""

    def __init__(self, name, platform, secret):
        self._name = name
        self._platform = platform

    def __str__(self):
        return f"{self.name()}"

    @property
    def name(self):
        return self._name

    @property
    def platform(self):
        return self._platform

    @name.setter
    def name(self, value):
        self._name = value

    @platform.setter
    def platform(self, value):
        self._platform = value
