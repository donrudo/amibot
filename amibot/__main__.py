#!/usr/bin/env python3
import argparse
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from configloader.FromFile import FromFile
from configloader.FromS3 import FromS3
from user.bot import Bot
from community.discord_client import Discord

# REST API INITIALIZATION --- healthchecks for Readyness and liveness probes #


@asynccontextmanager
async def contextmanager(api_checks: FastAPI):
    # yelds to only run on shutdown. #

    print("FastAPI -Context Manager: Started ")

    yield

    print("FastAPI - Context Manager: Stopping the bot and the community")

    # Clean up and release the resources
    await shutdown_event()

api_checks = FastAPI(lifespan=contextmanager)


@api_checks.get("/readiness")
async def readiness():
    # Returns "OK" when both objects are not None, regardless of the status of the bot and the community #
    if community is None and amigo is None:
        raise HTTPException(status_code=202, detail="Not Ready")

    return{"message": "OK"}


@api_checks.get("/liveness")
async def liveness():
    # Returns "OK" if the community and the bot were loaded fine #
    if community.is_ready() is False and amigo.is_ready() is False:
        raise HTTPException(status_code=500, detail="Internal Error")

    if community.is_ready() is False:
        raise HTTPException(status_code=503, detail="Community is Offline")

    if amigo.is_ready() is False:
        raise HTTPException(status_code=503, detail="Bot is gone")

    return {"message": "OK"}


# Main section starts --- #


async def shutdown_event():
    """Gracefully stops the bot and the community"""
    print("Stopping the bot and the community")
    await community.stop()
    amigo.client.close()


async def wait():
    while not asyncio.get_event_loop().is_running():
        await asyncio.sleep(0.5)


def main():
    # Starts the API server for healthchecks and metrics #

    loop = asyncio.new_event_loop()

    api_config = uvicorn.Config(api_checks, host="0.0.0.0", port=23459, loop=loop)
    api_server = uvicorn.Server(api_config)

    try:

        asyncio.run(wait())
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

    amigo = None
    community = None
    load = None

    # Parse arguments
    parser = argparse.ArgumentParser(prog='Amibot', add_help=True)
    parser.add_argument('-c', '--config', type=str, help='Path to configuration file of:'
                                                         '-- file:/path/to/localfile.yaml'
                                                         '-- https://s3.endpoint/bucket/remote/location.yaml'
                                                         '-- s3://bucket/remote/location.yaml')
                                                         # TODO '-- vault://hashicorp_vault_project/app/keys.location'
                                                         # TODO '-- kv://cloudflare_namespace/keys.location ? ')
    args = parser.parse_args()

    # Load Configuration file
    location = args.config.split(':')
    match location[0]:
        case 'file':
            load = FromFile(location[1])
        case 'https':
            load = FromS3(args.config)
        case 's3':
            load = FromS3(args.config)
        case _:
            if len(location) == 1:
                print('No specific protocol identified, assuming local file')
                load = FromFile(args.config)
    if load:
        configuration = load.configuration
    else:
        exit(1)

    # Configuration  ---- Reads the configuration settings and sets up the bot and community
    if configuration:
        # try:
        if "amibot" not in configuration:
            ValueError("undefined amibot settings")
            exit(1)

        # checks for Discord settings
        if "discord" in configuration:
            if "enabled" in configuration['discord'] and configuration['discord']['enabled']:
                amigo = Bot(configuration['amibot']['username'], "Discord",
                            configuration['discord']['public_key'], configuration['amibot']['system_role'])
                community = Discord(configuration['discord']['token'])

        # checks for openai settings
        if amigo and community and "openai" in configuration:
            if "enabled" in configuration['openai'] and configuration['openai']["enabled"]:
                amigo.model = configuration['openai']['model']
                amigo.engine = 'openai'
                amigo.client = configuration['openai']['key']
                community.bot = amigo

    if amigo is None:
        exit(1)

    print("Username: ", amigo.name)
    print("Plataforma: ", amigo.platform)
    print("OpenAI: ", amigo.client)

    main()
