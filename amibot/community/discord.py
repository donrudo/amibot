import discord
import asyncio
from community import Community


class Discord(Community):
    """ Setups the connections and settings for discord interactions """
    pass

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
        async def on_message(message):
            if message.author != self.client.user:
                print(message.content.capitalize())
                print(message.author.name)
                reply = self.bot.chat_completion(message.author.name, message.content.capitalize())
                await message.channel.send(reply)

    def is_ready(self) -> bool:
        return self._check

    async def stop(self):
         await self.client.close()

    async def start(self) -> None:
        await self.client.start(self.secret)
