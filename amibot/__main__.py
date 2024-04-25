#!/usr/bin/env python3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from user.bot import Bot
from community.discord import *
import argparse
import yaml
import uvicorn


amigo = None
parser = argparse.ArgumentParser(prog='Amibot', add_help=True)
parser.add_argument('-c', '--config', type=str, help='path to configuration file')
args = parser.parse_args()


""" Configuration  ---- Reads the configuration file and sets up the bot and community"""
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


"""REST API INITIALIZATION --- healthchecks for Readyness and liveness probes"""


@asynccontextmanager
async def contextmanager(api_checks: FastAPI):
    """yelds to only run on shutdown."""

    print("FastAPI -Context Manager: Started ")

    yield

    print("FastAPI - Context Manager: Stopping the bot and the community")

    # Clean up and release the resources
    await shutdown_event()

api_checks = FastAPI(lifespan=contextmanager)


@api_checks.get("/readiness")
async def readiness():
    """Returns "OK" when both objects are not None, regardless of the status of the bot and the community"""
    if community is None and amigo is None:
        raise HTTPException(status_code=202, detail="Not Ready")

    return{"message": "OK"}


@api_checks.get("/liveness")
async def liveness():
    """Returns "OK" if the community and the bot were loaded fine"""
    if community.is_ready() is False and amigo.is_ready() is False:
        raise HTTPException(status_code=500, detail="Internal Error")

    if community.is_ready() is False:
        raise HTTPException(status_code=503, detail="Community is Offline")

    if amigo.is_ready() is False:
        raise HTTPException(status_code=503, detail="Bot is gone")

    return {"message": "OK"}


""" Main section starts --- """


async def shutdown_event():
    """Gracefully stops the bot and the community"""
    print("Stopping the bot and the community")
    await community.stop()
    amigo.client.close()


def main():
    """Starts the API server for healthchecks and metrics"""

    loop = asyncio.get_event_loop()

    api_config = uvicorn.Config(api_checks, host="0.0.0.0", port=23459, loop=loop)
    api_server = uvicorn.Server(api_config)

    try:

        loop.create_task(community.start())

        try:
            loop.run_until_complete(api_server.serve())
        except KeyboardInterrupt:
            print("Application stopped by user")

    except Exception as e:
        print("Exception: ", e)

    else:
        if loop.is_running():
            loop.stop()
        loop.close()


if __name__ == "__main__":
    # asyncio.run(start())
    main()
