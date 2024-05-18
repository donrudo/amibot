import asyncio
import discord
from community import Community


class Discord(Community):
    """ Setups the connections and settings for discord interactions """

    def __init__(self, secret):
        self._check = False
        self._bot = None
        super().__init__("Discord", secret)
        self.client = discord.Client(intents=discord.Intents.all())

        @self.client.event
        async def on_connect():
            print("-- Discord.on_connect(): Connected to Discord -- ")
            # await self.client.login(self.secret)

        @self.client.event
        async def on_ready():
            print("-- Discord.on_ready() -- ")
            self._check = True
            print("User:", self.client.user)
            if self.client.user is None:
                await self.client.login(self.secret)

        @self.client.event
        async def on_error():
            self._check = False
            print("Error: disconnected from Discord")

        @self.client.event
        async def on_message(chat_msg):
            found = False
            if chat_msg.guild is None or chat_msg.mention_everyone:
                found = True
            else:
                for value in chat_msg.mentions:
                    print(type(value), type(discord.member.Member))
                    if type(value) is discord.member.Member and value.name == self.client.user.name:
                        found = True
                        break
                    else:
                        print(value)

            if found:
                if chat_msg.author != self.client.user:
                    print(chat_msg.author.name)
                    start = 0
                    msg_limit = 2000
                    reply = self.bot.chat_completion(chat_msg.author.name, chat_msg.content.capitalize())

                    while start < len(reply):
                        # TODO: Clumsy split in chunks,
                        #  needs improvement making sure sentences and format are not broken.
                        await chat_msg.channel.send(reply[start: start+msg_limit])
                        start += msg_limit

    def is_ready(self) -> bool:
        return self._check

    async def stop(self):
         await self.client.close()

    async def start(self) -> None:
        await self.client.start(self.secret)
