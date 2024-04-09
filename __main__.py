from user.bot import Bot
from community.discord import *

import yaml

amigo = None
with open("amibot.conf", "r") as stream:
    try:
        configuration = yaml.safe_load(stream)
        if "amibot" not in configuration:
            ValueError("undefined amibot settings")
            exit(1)

        '''checks for Discord settings'''
        if "discord" in configuration:
            if "enabled" in configuration['discord'] and configuration['discord']['enabled']:
                amigo = Bot(configuration['amibot']['username'], "Discord", configuration['discord']['public_key'])
                community = Discord(configuration['discord']['token'])

        '''checks for openai settings'''
        if amigo is not None and "openai" in configuration:
            if "enabled" in configuration['openai'] and configuration['openai']["enabled"]:
                amigo.model = configuration['openai']['model']
                amigo.engine = 'openai'
                amigo.client = configuration['openai']['key']
                community.bot = amigo

    except yaml.YAMLError as exc:
        amigo = Bot("amigo", "test", "secreto")
        print("Username: ", amigo.name)
        print("Plataforma: ", amigo.platform)
        print("Exception: ", exc)

if amigo is None:
    exit(1)

print("Username: ", amigo.name)
print("Plataforma: ", amigo.platform)
print("OpenAI: ", amigo.client)

community.start()


"""
Flow:
1-start application
2.- Read communities from configuration. 
3.- Connect to each community.
4.- process message.

"""