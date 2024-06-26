AmiBot
======

Just a bot to gpt with, supports Anthropic and OpenAI.

Currently only works on Discord.

## Installation
1. Clone the repository
1. `scrpts/build.sh`
1. Signup for an OpenAI API key and for a Discord bot token
1. edit your configs/amibot_example.conf and save it as configs/amibot.conf

## Running
1. Can be run using an S3 hosted file `python -m amibot -c s3:/bucket/to/config.yaml`
2. Or. Can be run using the local config file `python -m amibot -c configs/amibot.conf`

## Using Kubernetes
1. Build the docker image, I use `nerdctl`
   * `~/.rd/bin/nerdctl --namespace=k8s.io build -t amibot:0.0.1 -f ./build/package/Dockerfile .`
   * or pull image from registry `docker pull registry.gitlab.com/donrudo/amibot:0.0.5`
2. Run the pod
   * `kubectl apply -k .`


## TODO:
- [ ] Python: Make it cheaper: currently uses a Gateway pattern, which is expensive.
- [X] Python: Replaced the need of a local configuration file, other configuration sources 
- [X] Python: Add a healthcheck.
- [ ] Python: Cure bot's amnesia, add database support (ex. pinecone, dynamodb, etc) to store conversations relevant fragments.
- [ ] K8s: Move config file to secrets.
- [ ] K8s: Use kubeseal to encrypt the config file.
