AmiBot
======

Just a bot to gpt with.

Currently only works on Discord.

## Installation
1. Clone the repository
1. `scrpts/build.sh`
1. Signup for an OpenAI API key and for a Discord bot token
1. edit your configs/amibot_example.conf and save it as configs/amibot.conf

## Running
1. `pip amibot -c configs/amibot.conf`

## Using Kubernetes
1. Build the docker image, I use `nerdctl`
   * `~/.rd/bin/nerdctl --namespace=k8s.io build -t amibot:0.0.1 -f ./build/package/Dockerfile .`
2. Run the pod
   * `~/.rd/bin/kubectl apply -k .`


## TODO:
- [ ] Python: Make it cheaper: currently uses a Gateway pattern, which is expensive.
- [ ] Python: Add process to copy the config file to a temporary location, then delete it after the bot is running.
- [ ] Python: Add a healthcheck.
- [ ] K8s: Move config file to secrets.
- [ ] K8s: Use kubeseal to encrypt the config file.
