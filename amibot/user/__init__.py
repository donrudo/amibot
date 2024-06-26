class User:
    """Bot properties to be used, add openAI behaviors
    and user interactions here"""

    def __init__(self, name, llmprovider, secret):
        self._name = name
        self._llmprovider = llmprovider
        self._check = False

    def __str__(self):
        return f"{self.name()}"

    @property
    def name(self):
        return self._name

    @property
    def is_ready(self):
        return self._check

    @property
    def platform(self):
        return self._llmprovider

    @name.setter
    def name(self, value):
        self._name = value

    @is_ready.setter
    def is_ready(self, value):
        self._check = value
