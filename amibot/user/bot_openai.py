import re
import openai

from user.bot import DictNoNone, Bot
from openai import OpenAI


class OpenaiBot(Bot):

    def __init__(self, name, llmprovider, secret, token_min, token_max, token_increment, system_role=""):
        super().__init__(name, llmprovider, "")
        self._model = "gpt-4o"
        self._client = openai.Client(api_key=secret)
        self._token_limits = range(token_min, token_max, token_increment)
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
        self._client = OpenAI(api_key=token)
        if self._client.is_closed():
            self._check = False
        else:
            self._check = True
        print("Connected to OpenAI API")

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
        if name not in self._messages:
            self._messages[name] = self._messages.get('system_role',[])

        self._messages[name].append({"role": "user", "content": f"{name} says {message}"})

        assistant_message = ''
        consumed_resource = 0
        for token_limit in self.token_limits:
            response_stream = self.client.chat.completions.create(
                stream=True,
                model=self.model,
                max_tokens=token_limit,
                temperature=0.5,
                messages=self._messages[name]
            )
            assistant_message = ""
            completed = True

            # FIXME: response_stream stopped providing the usage object.
            # print(f'Prompt tokens: {response_stream.usage.prompt_tokens}')
            # print(f'Completion tokens: {response_stream.usage.completion_tokens}')
            # print(f'Total tokens: {response_stream.usage.total_tokens}')

            for response in response_stream:
                if response.choices[0].finish_reason == "length":
                    completed = False
                    break

                if response.choices[0].delta.content is not None:
                    assistant_message += response.choices[0].delta.content

            if completed:
                break

        # Append the complete assistant's response
        self._messages[name].append({"role": "assistant", "content": assistant_message})

        # Return the assistant's complete response
        return assistant_message
