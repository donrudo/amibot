import re
import anthropic
from user.bot import DictNoNone, Bot


class AnthropicBot(Bot):

    def __init__(self, name, llmprovider, secret, token_min, token_max, token_increment, system_role=""):
        super().__init__(name, llmprovider, secret="")
        self._client = anthropic.Anthropic(api_key=secret)
        self._token_limits = range(token_min, token_max, token_increment)
        self._messages['system_role'] = [
            {"role": "system",
             "content": f"Goes by the nickname {name}; "
                        f"Summarized Paragraphs with short and understandable messages;"
                        f"the code is at https://gitlab.com/donrudo/amibot "
                        f"{system_role}"}
        ]
        self._check = True

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, token):
        self._client = anthropic.Anthropic(api_key=token)
        if self._client.is_closed():
            self._check = False
        else:
            self._check = True
        print("Connected to OpenAI API")

    # function from https://www.geeksforgeeks.org/python-check-url-string/
    def get_urls(self, input: str):
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        url_mask = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(url_mask, input)
        return [x[0] for x in url]

    def chat_completion(self, name, message) -> str:
        print(f"--- CHAT CONVERSATION from: {name}, using {self.model}")

        if name not in self._messages:
            self._messages[name] = [{"role": "user", "content": f"{name} says {message}"}]
        else:
            self._messages[name].append({"role": "user", "content": f"{name} says {message}"})

        assistant_message = ''
        consumed_resource = 0
        for token_limit in self.token_limits:
            print(f'{self._messages[name]}')
            assistant_message = ''
            with self.client.messages.stream(
                model=self.model,
                system=f"{self._messages.get('system_role', [])}",
                temperature=0.5,
                max_tokens=token_limit,
                messages= self._messages[name]
            ) as response_stream:
                response_stream.until_done()
                response = response_stream.get_final_message()
                print(response.model)
                print(f'Response event: {response.stop_sequence}')
                print(f'Output tokens: {response.usage.output_tokens}')
                print(f'Input tokens: {response.usage.input_tokens}')
                consumed_resource += response.usage.output_tokens + response.usage.input_tokens

                for text in response_stream.text_stream:
                    assistant_message += text

                match response.stop_reason:
                    case "end_turn":
                        if assistant_message == '':
                            assistant_message = response_stream.get_final_text()
                        print(f'Consumed Tokens: {consumed_resource}')
                        break
                    case "max_tokens":
                        print(assistant_message)
                        continue
                    case "*":
                        print(f'stop_reason: {response.stop_reason} \n tokens: {token_limit}')

        # Append the complete assistant's response
        self._messages[name].append({"role": "assistant", "content": assistant_message})

        # Return the assistant's complete response
        return assistant_message
