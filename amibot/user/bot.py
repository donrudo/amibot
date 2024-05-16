import openai

from user import User
from openai import OpenAI


class DictNoNone(dict):
    def __setitem__(self, key, value):
        if key in self or value is not None:
            dict.__setitem__(self, key, value)


class Bot(User):
    pass

    def __init__(self, name, platform, secret, system_role=""):
        super().__init__(name, platform, secret)
        self._model = "gpt-4"
        self._engine = ""
        self._client = openai.Client
        self._messages = DictNoNone()
        self._messages['system_role'] = [
            {"role": "system",
             "content": f"Goes by the nickname {name}; "
                        f"answers into Summarized Paragraphs with short and understandable messages;"
                        f"the code is at https://gitlab.com/donrudo/amibot "
                        f"{system_role}"}
        ]
        self._check = True

    @property
    def model(self):
        return self._model

    @property
    def engine(self):
        return self._engine

    @property
    def client(self):
        return self._client

    def is_ready(self):
        return self._check

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
        if self._client.is_closed():
            self._check = False
        else:
            self._check = True
        print("Connected to OpenAI API")

    @messages.setter
    def messages(self, key, value):
        self._messages[key] = value

    def chat_completion(self, name, message) -> str:
        print(f"--- CHAT CONVERSATION from: {name}")
        if name not in self._messages:
            self._messages[name] = self._messages.get('system_role',[])

        self._messages[name].append({"role": "user", "content": f"{name} says {message}"})

        response_stream = self.client.chat.completions.create(
            stream=True,
            model=self.model,
            max_tokens=512,
            messages=self._messages[name]
        )

        # Process the streaming response
        assistant_message = ""
        print_once = True
        for response in response_stream:
            if print_once:
                print(response.choices[0].delta.model_config)
                print_once = False
            if response.choices[0].delta.content is not None:
                assistant_message += response.choices[0].delta.content

        # Append the complete assistant's response
        self._messages[name].append({"role": "assistant", "content": assistant_message})

        # Return the assistant's complete response
        return assistant_message
