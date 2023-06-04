import discord
from community import Community


class Discord(Community):
    """ Setups the connections and settings for discord interactions """
    pass

    def __init__(self, secret):
        super().__init__("Discord", secret)
        self.client = discord.Client(intents=discord.Intents.all())

        @self.client.event
        async def on_ready():
            print("-- Connected to Discord -- ")
            print("User:", self.client.user)

        @self.client.event
        async def on_message(message):
            if message.author != self.client.user:
                await message.channel.send(message.content[::-1])

    @property
    def start(self):
        self.client.run(self.secret)
