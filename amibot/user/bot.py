import re

from user import User

class DictNoNone(dict):
    def __setitem__(self, key, value):
        if key in self or value is not None:
            dict.__setitem__(self, key, value)


class Bot(User):
    pass

    def __init__(self, name, llmprovider, secret, system_role=""):
        super().__init__(name, llmprovider, secret)
        self._model = "unset"
        self._client = "unset"
        self._messages = DictNoNone()
        self._messages['system_role'] = [
            {"role": "system",
             "content": f"Goes by the nickname {name}; "
                        f"Summarized Paragraphs with short and understandable messages;"
                        f"the code is at https://gitlab.com/donrudo/amibot "
                        f"{system_role}"}
        ]
        self._check = True

    @property
    def model(self):
        return self._model

    @property
    def llmprovider(self):
        return self._llmprovider

    @property
    def token_limits(self):
        return self._token_limits

    @property
    def client(self):
        return self._client

    def is_ready(self):
        return self._check

    @property
    def messages(self):
        return self._messages

    @token_limits.setter
    def token_limits(self, value):
        self.token_limits = value

    @llmprovider.setter
    def llmprovider(self, value):
        self._llmprovider = value

    @model.setter
    def model(self, value):
        self._model = value

    @client.setter
    def client(self, token):
        self._check = True
        print("Connected to None")

    @messages.setter
    def messages(self, key, value):
        self._messages[key] = value

    # function from https://www.geeksforgeeks.org/python-check-url-string/
    def get_urls(self, input: str):
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        url_mask = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(url_mask, input)
        return [x[0] for x in url]

    def chat_completion(self, name, message) -> str:
        print(f"--- CHAT CONVERSATION from: {name}")

        # Return the assistant's complete response
        return f"Hello {name} you said {message}"
