import asyncio
import time

import discord
from discord import channel, client, Client, Thread, User, utils, Message
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
        async def on_error(first=None, second=None):
            if first is not None:
                print(f'Error at {first}: \n\t{second}')
            self._check = False
            print("Error: disconnected from Discord")

        def split_into_chunks(message, chunk_size=2000):
            return [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]

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
                    print(f'msg from: {chat_msg.author.name}')

                    reply = self.bot.chat_completion(chat_msg.author.name, chat_msg.content.capitalize())
                    print(f'{reply}')
                    msgs = split_into_chunks(reply)
                    sent = 0

                    for msg in msgs:
                        print(f"Sending {sent} of {len(msgs)}")
                        sent += 1
                        async with chat_msg.channel.typing():
                        # TODO: Clumsy split in chunks,
                        #  needs improvement making sure sentences and format are not broken.

                        # FIXME: long responses are being interrupted and cut by half.
                            try:
                                await chat_msg.channel.send(msg)
                            except discord.errors.RateLimited as e:
                                await asyncio.sleep(e.retry_after)
                                await chat_msg.channel.send(msg)
                            finally:
                                time.sleep(1)

    def is_ready(self) -> bool:
        return self._check

    async def stop(self):
        await self.client.close()

    async def start(self) -> None:
        await self.client.start(self.secret)
