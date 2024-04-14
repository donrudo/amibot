#!/usr/bin/env python3
from fastapi import FastAPI, Request
from user.bot import Bot
from community.discord import *
import asyncio
import argparse
import yaml
import uvicorn


parser = argparse.ArgumentParser(prog='Amibot', add_help=True)
parser.add_argument('-c', '--config', type=str, help='path to configuration file')
args = parser.parse_args()

amigo = None
Checks = FastAPI()


@Checks.get("/")
async def root():
    """Returns "OK" if the community and the bot were loaded fine"""
    if community.check() and amigo.check():
        return {"message": "OK"}

    return{"message": "False"}


def api_start():
    uvicorn.run(Checks, host="0.0.0.0", port=23459)


async def start():

    """Starts the bot and the community"""
    async with asyncio.TaskGroup() as tasks:
        task_community = tasks.create_task(asyncio.to_thread(community.start))
        task_apiserver = tasks.create_task(asyncio.to_thread(api_start))

    while True:
        await asyncio.sleep(1)
        if not task_community.done():
            continue

        if not task_apiserver.done():
            continue
        break

"""Reads the configuration file and sets up the bot and community"""
with open(args.config, "r") as stream:
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

app = FastAPI()

asyncio.run(start())

"""
Flow:
1-start application
2.- Read communities from configuration. 
3.- Connect to each community.
4.- process message.

"""