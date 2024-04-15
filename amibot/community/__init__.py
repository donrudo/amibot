class Community:
    """Community definition with basic behaviors common around
    different platforms"""

    def __init__(self, platform, secret):
        self._platform = platform
        self._secret = secret
        self._bot = None
        self._check = False

    def __str__(self):
        """Prints only platform instead of leaking other information"""
        return f"{self._platform}"

    @property
    def secret(self):
        return self._secret

    @property
    def platform(self):
        return self._platform

    @property
    def is_ready(self) -> bool:
        return self._check

    @property
    def bot(self):
        return self._bot

    @secret.setter
    def secret(self, value):
        self._secret = value

    @platform.setter
    def platform(self, value):
        self._platform = value

    @is_ready.setter
    def is_ready(self, value):
        self._check = value

    @bot.setter
    def bot(self, value):
        self._bot = value
