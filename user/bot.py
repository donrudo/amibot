import openai
from collections import deque
from user import User
from openai import OpenAI

class DictNoNone(dict):
    def __setitem__(self, key, value):
        if key in self or value is not None:
            dict.__setitem__(self, key, value)

class Bot(User):
    pass

    def __init__(self, name, platform, secret):
        super().__init__(name, platform, secret)
        self._model = "gpt-4"
        self._engine = ""
        self._client = openai.Client
        self._messages = DictNoNone()
        self._messages['default'] = [
             {"role": "system",
              "content": "expert in short texting, skilled developer who likes videogames and has bad mood"}
        ]



    @property
    def model(self):
        return self._model

    @property
    def engine(self):
        return self._engine

    @property
    def client(self):
        return self._client

    @property
    def messages(self):
        return self._messages

    @engine.setter
    def engine(self, value):
        self._engine = value

    @model.setter
    def model(self, value):
        self._model = value

    @client.setter
    def client(self, token):
        self._client = OpenAI(api_key=token)
        print("Connected to OpenAI API")

    @messages.setter
    def messages(self, key, value):
        self._messages[key] = value

    # def chat_start(self, name, message) -> dict:
    #     print("--- NEW CHAT COMPLETION ---")
    #     chat_start = [
    #             {"role": "system",
    #              "content": "expert in short texting developer who likes videogames and has bad mood"},
    #             {"role": "user", "content": message }
    #        ]
    #     return chat_start

    def chat_completion(self, name, message) -> str:
        print("--- CHAT CONVERSATION from:", name)
        if name not in self._messages:
            self._messages[name] = self._messages['default']

        self._messages[name].append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            stream=False,
            model=self.model,
            max_tokens=512,
            messages= self._messages[name]
        )
        self._messages[name].append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content
