from user import User
from openai import OpenAI

class Bot(User):
    pass

    def __init__(self, name, platform, secret):
        super().__init__(name, platform, secret)
        self._model = "gpt-4"
        self._engine = ""
        self._client = ""

    @property
    def model(self):
        return self._model

    @property
    def engine(self):
        return self._engine

    @property
    def client(self):
        return self._client

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

    def chat_completion(self, message) -> str:
        print("--- CHAT COMPLETION ---")
        completion = self.client.chat.completions.create(
            stream=False,
            model=self.model,
            messages=[
                {"role": "system",
                 "content": "expert in short texting developer who likes videogames and has bad mood"},
                {"role": "user", "content": message }
           ]
        )
        print("--- CHAT COMPLETION")
        print(completion.choices[0].message.content)

        return completion.choices[0].message.content

