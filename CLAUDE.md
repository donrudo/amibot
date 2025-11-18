# CLAUDE.md - AI Assistant Guide for AmiBot

**Last Updated**: 2025-11-15
**Project**: AmiBot - Multi-platform AI Discord Bot
**Repository**: https://gitlab.com/donrudo/amibot
**Python Version**: 3.10+
**Current Version**: 0.0.2
**Security**: CVE-2025-47273 fixed (setuptools upgraded to >=78.1.1)

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technical Diagrams](#technical-diagrams)
4. [Codebase Structure](#codebase-structure)
5. [Development Guidelines](#development-guidelines)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Code Patterns and Conventions](#code-patterns-and-conventions)
9. [API Contracts and Interfaces](#api-contracts-and-interfaces)
10. [State Management](#state-management)
11. [Error Handling and Resilience](#error-handling-and-resilience)
12. [Testing and CI/CD](#testing-and-cicd)
13. [Common Tasks](#common-tasks)
14. [Known Issues and TODOs](#known-issues-and-todos)

---

## Project Overview

AmiBot is a Discord bot that provides conversational AI capabilities through multiple LLM providers (OpenAI, Anthropic Claude, and Perplexity). The bot is designed for cloud-native deployment with support for Kubernetes and AWS ECS.

### Key Features
- Multi-LLM provider support (OpenAI, Anthropic, Perplexity)
- Discord integration with full message handling
- Per-user conversation context management
- Progressive token limit strategy to reduce costs
- Health check endpoints for orchestration
- Configuration loading from local files or AWS S3
- Production-ready with Docker and Kubernetes support

### Tech Stack
- **Language**: Python 3.10+
- **LLM Clients**: openai, anthropic
- **Platform**: discord.py
- **API Framework**: FastAPI + Uvicorn
- **Cloud**: AWS (boto3), Kubernetes
- **CI/CD**: CircleCI
- **IaC**: Terraform

**For Detailed Diagrams**: See [documentation/TECHNICAL_DIAGRAMS.md](documentation/TECHNICAL_DIAGRAMS.md) for comprehensive:
- Class diagrams with full inheritance hierarchy
- Sequence diagrams for all major flows
- State diagrams for bot and Discord lifecycles
- Data flow diagrams
- Deployment architecture diagrams

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Discord                              │
│                     (Community Layer)                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Dependency Injection
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Bot Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  OpenaiBot   │  │ AnthropicBot │  │ PerplexityBot│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                 │
                 │ Configuration
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  ConfigLoader Layer                          │
│         ┌──────────────┐    ┌──────────────┐                │
│         │   FromFile   │    │    FromS3    │                │
│         └──────────────┘    └──────────────┘                │
└─────────────────────────────────────────────────────────────┘
                 │
                 │ Health Checks
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Server                              │
│            /liveness, /readiness (port 23459)                │
└─────────────────────────────────────────────────────────────┘
```

### Class Hierarchy

```python
# Base Classes
User (base)
  └── Bot (extends User)
      ├── OpenaiBot (extends Bot)
      ├── AnthropicBot (extends Bot)
      └── PerplexityBot (extends Bot)

Community (base)
  └── Discord (extends Community)

ConfigLoader (base)
  ├── FromFile (extends ConfigLoader)
  └── FromS3 (extends ConfigLoader)
```

### Message Flow

```
1. Discord Message Event
   └─> on_message() handler
       └─> Check if message is relevant (DM, @mention, @everyone)
           └─> Call bot.chat_completion(username, message)
               └─> Retrieve/create user conversation context
                   └─> Call LLM provider API with streaming
                       └─> Accumulate response
                           └─> Return complete response
                               └─> Split into 2000-char chunks
                                   └─> Send chunks to Discord
```

---

## Technical Diagrams

AmiBot includes comprehensive technical diagrams documenting the system architecture, data flows, and operational patterns. These diagrams are essential for understanding how components interact.

### Available Diagrams

See **[documentation/TECHNICAL_DIAGRAMS.md](documentation/TECHNICAL_DIAGRAMS.md)** for the complete set of diagrams:

1. **Class Diagram** - Full inheritance hierarchy showing User → Bot → (OpenaiBot/AnthropicBot/PerplexityBot), Community → Discord, and ConfigLoader → (FromFile/FromS3)

2. **Sequence Diagrams**:
   - Application startup sequence
   - Message handling flow (Discord → Bot → LLM → Discord)
   - Progressive token strategy flow
   - Configuration loading flow
   - Health check flow

3. **State Diagrams**:
   - Bot lifecycle states (Initializing → Ready → Processing → Shutdown)
   - Discord client states (Created → Connecting → Ready → Processing)

4. **Data Flow Diagrams**:
   - Conversation context management (per-user message histories)
   - Message flow through system
   - DictNoNone custom data structure

5. **Deployment Architecture**:
   - Kubernetes deployment with ConfigMap and health probes
   - AWS ECS deployment with Fargate, S3, and IAM
   - CI/CD pipeline flow (CircleCI → Terraform → ECS)

6. **Component Interaction Diagram** - Shows how all components communicate

### Key Architectural Insights from Diagrams

**Progressive Token Strategy** (see documentation/TECHNICAL_DIAGRAMS.md):
```
Start: 256 tokens → API call → Truncated?
  ├─ No: Return complete response
  └─ Yes: Increase to 512 tokens → Retry → ...
```

**Per-User Context Isolation** (see documentation/TECHNICAL_DIAGRAMS.md):
```python
_messages = {
    'system_role': [...],
    'alice': [user_msg, assistant_msg, ...],
    'bob': [user_msg, assistant_msg, ...]
}
```

**Concurrency Model** (see documentation/TECHNICAL_DIAGRAMS.md):
- Single async event loop runs both Discord and FastAPI
- Discord handlers are async, but bot.chat_completion() is synchronous
- Multiple users can interact, but conversations are processed sequentially

---

## Codebase Structure

### Directory Layout

```
/home/user/amibot/
├── amibot/                      # Main application package
│   ├── __main__.py             # Entry point (run with: python -m amibot)
│   ├── user/                   # Bot implementations
│   │   ├── __init__.py         # User base class
│   │   ├── bot.py              # Bot base class
│   │   ├── bot_openai.py       # OpenAI implementation
│   │   ├── bot_anthropic.py    # Anthropic/Claude implementation
│   │   └── bot_perplexity.py   # Perplexity implementation
│   ├── community/              # Platform integrations
│   │   ├── __init__.py         # Community base class
│   │   └── discord_client.py   # Discord client implementation
│   └── configloader/           # Configuration loaders
│       ├── __init__.py         # ConfigLoader base class
│       ├── FromFile.py         # Local file YAML loader
│       └── FromS3.py           # AWS S3 YAML loader
│
├── configs/                    # Configuration files
│   ├── amibot_example.conf     # Example configuration (YAML)
│   └── cloud_settings.json     # Cloud deployment settings
│
├── scripts/                    # Build and utility scripts
│   ├── build.sh                # Local build script (creates venv, installs deps)
│   ├── start.sh                # Container startup script
│   ├── run_terraform.sh        # Terraform execution wrapper
│   └── get_variablestf.py      # Generates Terraform vars from JSON/YAML
│
├── deployment/                 # Deployment configurations
│   ├── kubernetes/             # Kubernetes manifests
│   │   ├── namespace.yaml      # Creates 'development' namespace
│   │   └── release.yaml        # Pod deployment with health probes
│   └── cloud/aws/              # AWS Terraform configs
│       ├── ecs.tf              # ECS cluster, service, task definition
│       ├── iam.tf              # IAM roles for ECS tasks
│       ├── terraform.tf        # Provider configuration
│       └── variables.tf        # Variable definitions
│
├── build/package/              # Docker build files
│   └── Dockerfile              # Multi-stage build, runs as 'nobody' user
│
├── .circleci/                  # CI/CD pipeline
│   └── config.yml              # CircleCI workflow (prepare → plan → apply)
│
├── requirements.txt            # Python dependencies
├── setup.py                    # Minimal setuptools entry
├── setup.cfg                   # Setuptools configuration
├── pyproject.toml              # Project metadata (PEP 621)
├── kustomization.yaml          # Kustomize config (generates ConfigMap)
├── .gitignore                  # Git ignore rules
└── README.md                   # User documentation
```

### Key Entry Points

| File | Purpose | Usage |
|------|---------|-------|
| `amibot/__main__.py` | Application entry point | `python -m amibot -c <config>` |
| `scripts/build.sh` | Local development setup | `./scripts/build.sh` |
| `scripts/start.sh` | Container startup | Executed by Dockerfile |
| `build/package/Dockerfile` | Container image build | `docker build -f build/package/Dockerfile .` |

---

## Development Guidelines

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://gitlab.com/donrudo/amibot.git
   cd amibot
   ```

2. **Run the build script**:
   ```bash
   ./scripts/build.sh
   ```
   This script:
   - Creates a Python virtual environment if it doesn't exist
   - Activates the venv
   - Installs build tools (pip, setuptools, wheel)
   - Installs requirements from `requirements.txt`
   - Installs the package in editable mode

3. **Create configuration**:
   ```bash
   cp configs/amibot_example.conf configs/amibot.conf
   # Edit configs/amibot.conf with your API keys and tokens
   ```

4. **Run the bot**:
   ```bash
   python -m amibot -c configs/amibot.conf
   ```

### Code Style and Conventions

#### Python Style
- **Python Version**: Minimum 3.10 (for match/case support)
- **Type Hints**: Not extensively used, but encouraged for new code
- **Docstrings**: Minimal; add docstrings for complex logic
- **Formatting**: No strict formatter enforced (consider adopting Black)
- **Naming**:
  - Classes: `PascalCase` (e.g., `OpenaiBot`)
  - Functions/Methods: `snake_case` (e.g., `chat_completion`)
  - Private attributes: `_leading_underscore` (e.g., `_messages`)

#### Property-Based Encapsulation
The codebase extensively uses `@property` decorators for attribute access:

```python
@property
def model(self):
    return self._model

@model.setter
def model(self, value):
    self._model = value
```

**Convention**: When adding new attributes to Bot or Community classes, use properties for public access.

#### Import Organization
Imports in `__main__.py` follow this pattern:
1. Standard library (argparse, asyncio, etc.)
2. Third-party (fastapi, uvicorn)
3. Local modules (configloader, user, community)

### Adding New Features

#### Adding a New LLM Provider

1. **Create new bot class** in `amibot/user/bot_<provider>.py`:
   ```python
   from user.bot import Bot

   class NewProviderBot(Bot):
       def __init__(self, name, llmprovider, key, token_from, token_max, token_increment, system_role):
           super().__init__(name, llmprovider, key, token_from, token_max, token_increment, system_role)
           # Initialize provider client
           self._client = ProviderClient(api_key=key)
           self._model = "default-model"

       def chat_completion(self, user, message):
           # Implement provider-specific logic
           # See bot_openai.py or bot_anthropic.py for examples
           pass
   ```

2. **Register in `__main__.py`** (around line 152):
   ```python
   match str.lower(configuration['llm']['provider']):
       case "openai":
           # existing code
       case "anthropic":
           # existing code
       case "newprovider":
           amigo = NewProviderBot(
               configuration['amibot']['username'],
               configuration['llm']['provider'],
               configuration['llm']['key'],
               configuration['llm']['tokens_range']['from'],
               configuration['llm']['tokens_range']['until'],
               configuration['llm']['tokens_range']['increment'],
               configuration['amibot']['system_role']
           )
   ```

3. **Update dependencies** in `requirements.txt`

#### Adding a New Platform (e.g., Slack, Telegram)

1. **Create new community class** in `amibot/community/<platform>_client.py`:
   ```python
   from community import Community

   class Slack(Community):
       def __init__(self, token):
           super().__init__(token)
           # Initialize platform client

       async def start(self):
           # Start platform connection
           pass

       async def stop(self):
           # Gracefully stop
           pass

       def is_ready(self):
           # Return readiness status
           return self._check
   ```

2. **Register in `__main__.py`** (around line 144):
   ```python
   if "slack" in configuration:
       if "enabled" in configuration['slack'] and configuration['slack']['enabled']:
           community = Slack(configuration['slack']['token'])
   ```

3. **Update configuration schema** in `configs/amibot_example.conf`

---

## Configuration

### Configuration File Format

AmiBot uses YAML configuration files with the following structure:

```yaml
# configs/amibot.conf (example)
amibot:
  username: "amigo"
  system_role: |
    You are a helpful assistant named {username}.
    You provide clear, concise answers and maintain conversation context.

discord:
  enabled: true
  application_id: "1234567890123456789"
  public_key: "your_discord_public_key"
  token: "your_discord_bot_token"

llm:
  provider: "anthropic"  # Options: "openai", "anthropic", "perplexity"
  enabled: true
  model: "claude-3-5-sonnet-20240620"
  key: "sk-ant-api03-..."
  tokens_range:
    from: 256        # Starting token limit
    until: 4096      # Maximum token limit
    increment: 256   # Increment when response is truncated
```

### Configuration Parameters

#### `amibot` Section
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Bot's display name (injected into system_role as `{username}`) |
| `system_role` | string | Yes | System prompt defining bot personality and behavior |

#### `discord` Section
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `enabled` | boolean | Yes | Toggle Discord integration |
| `application_id` | string | Yes | Discord application ID (from Developer Portal) |
| `public_key` | string | Yes | Discord public key (for webhook verification) |
| `token` | string | Yes | Discord bot authentication token |

#### `llm` Section
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | Yes | LLM provider: `"openai"`, `"anthropic"`, `"perplexity"` |
| `enabled` | boolean | Yes | Toggle LLM functionality |
| `model` | string | Yes | Model identifier (e.g., `"gpt-4"`, `"claude-3-5-sonnet-20240620"`, `"sonar"`) |
| `key` | string | Yes | API key for the selected provider |
| `tokens_range.from` | integer | Yes | Initial token limit for responses |
| `tokens_range.until` | integer | Yes | Maximum token limit (progressive strategy) |
| `tokens_range.increment` | integer | Yes | Token increment when response is truncated |

### Configuration Loading Protocols

AmiBot supports multiple configuration sources:

```bash
# Local file (default)
python -m amibot -c /path/to/config.yaml
python -m amibot -c configs/amibot.conf

# Explicit file protocol
python -m amibot -c file:/path/to/config.yaml

# AWS S3
python -m amibot -c s3://my-bucket/configs/amibot.yaml

# S3 via HTTPS
python -m amibot -c https://s3.amazonaws.com/my-bucket/configs/amibot.yaml
```

**Protocol Detection** (`__main__.py:119-130`):
- `file:` → Uses `FromFile` loader
- `s3:` → Uses `FromS3` loader
- `https:` → Uses `FromS3` loader (assumes S3 endpoint)
- No protocol → Defaults to `FromFile`

### Environment-Specific Configuration

For cloud deployments, use `configs/cloud_settings.json` to define infrastructure parameters:

```json
{
  "ecs_cluster": "botfarm",
  "scale_min": "1",
  "ecs_service": "amibot",
  "specs_cpu": "2",
  "specs_ram": "64",
  "image": "registry.gitlab.com/donrudo/amibot",
  "image_version": "0.0.4",
  "env": "dev"
}
```

This file is consumed by `scripts/get_variablestf.py` to generate Terraform variables.

---

## Deployment

### Local Development

```bash
# 1. Build environment
./scripts/build.sh

# 2. Configure bot
cp configs/amibot_example.conf configs/amibot.conf
vim configs/amibot.conf  # Add your API keys

# 3. Run bot
python -m amibot -c configs/amibot.conf
```

### Docker Deployment

**Build Image**:
```bash
# Using Docker
docker build -t amibot:latest -f build/package/Dockerfile .

# Using nerdctl (Rancher Desktop)
nerdctl --namespace=k8s.io build -t amibot:0.0.1 -f build/package/Dockerfile .
```

**Run Container**:
```bash
docker run -d \
  --name amibot \
  -p 23459:23459 \
  -v $(pwd)/configs/amibot.conf:/nonexistent/configs/amibot.conf:ro \
  amibot:latest
```

**Pull Pre-built Image**:
```bash
docker pull registry.gitlab.com/donrudo/amibot:0.0.5
```

### Kubernetes Deployment

**Prerequisites**:
- Kubernetes cluster (minikube, EKS, GKE, etc.)
- kubectl configured

**Deploy**:
```bash
# Deploy using Kustomize
kubectl apply -k .
```

**What Gets Deployed**:
1. **Namespace**: `development` (from `deployment/kubernetes/namespace.yaml`)
2. **ConfigMap**: Generated from `configs/amibot.conf` (via `kustomization.yaml`)
3. **Pod**: AmiBot deployment with:
   - Image: `registry.gitlab.com/donrudo/amibot:0.0.6.0`
   - Health probes: Liveness and Readiness on port 23459
   - ConfigMap mounted to `/nonexistent/configs`
   - DNS policy: `ClusterFirstWithHostNet`

**Verify Deployment**:
```bash
kubectl get pods -n development
kubectl logs -n development -l app=amibot
kubectl port-forward -n development pod/amibot 23459:23459
curl http://localhost:23459/readiness
```

**Update Configuration**:
```bash
# Edit configs/amibot.conf, then:
kubectl delete configmap -n development $(kubectl get configmap -n development -o name | grep amibot)
kubectl apply -k .
kubectl rollout restart deployment/amibot -n development
```

### AWS ECS Deployment (Terraform)

**Prerequisites**:
- AWS account with credentials configured
- Terraform Cloud account (backend configured in `deployment/cloud/aws/terraform.tf`)
- S3 bucket for configuration file
- Configuration file uploaded to S3

**Deployment Variables** (`configs/cloud_settings.json`):
```json
{
  "ecs_cluster": "botfarm",
  "scale_min": "1",
  "ecs_service": "amibot",
  "specs_cpu": "256",      // CPU units (256 = 0.25 vCPU)
  "specs_ram": "512",      // Memory in MB
  "image": "registry.gitlab.com/donrudo/amibot",
  "image_version": "0.0.6.0",
  "env": "dev"
}
```

**Manual Deployment**:
```bash
cd deployment/cloud/aws

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply deployment
terraform apply
```

**CI/CD Deployment** (CircleCI):

The `.circleci/config.yml` defines a multi-stage workflow:

1. **prepare**: Generates `terraform.tfvars` from `configs/cloud_settings.json`
2. **terraform-plan**: Validates and plans infrastructure changes
3. **terraform-approve**: Manual approval gate (requires clicking "Approve" in CircleCI UI)
4. **terraform-apply**: Applies approved changes

**Trigger Deployment**:
```bash
# Push to main branch (or configured branch)
git push origin main
```

**ECS Task Configuration**:
- **Entrypoint**: `scripts/start.sh s3://bucket/path/to/config.yaml`
- **IAM Role**: Grants S3 read access to config file
- **Network Mode**: `awsvpc`
- **Launch Type**: Fargate
- **Health Checks**: ECS uses port 23459 probes

---

## Code Patterns and Conventions

### Design Patterns

#### 1. Template Method Pattern
Base classes define structure; subclasses implement specifics.

**Example** (`user/bot.py` → `user/bot_openai.py`):
```python
# Base class defines interface
class Bot(User):
    def chat_completion(self, user, message):
        raise NotImplementedError

# Subclass implements specifics
class OpenaiBot(Bot):
    def chat_completion(self, user, message):
        # OpenAI-specific implementation
        pass
```

#### 2. Strategy Pattern
Runtime selection of algorithms (config loaders).

**Example** (`__main__.py:119-130`):
```python
location = args.config.split(':')
match location[0]:
    case 'file':
        load = FromFile(location[1])
    case 's3':
        load = FromS3(args.config)
    case _:
        load = FromFile(args.config)
```

#### 3. Dependency Injection
Community receives bot instance at runtime.

**Example** (`__main__.py:179`):
```python
community.bot = amigo  # Bot injected into Discord client
```

#### 4. Progressive Resource Allocation
Incremental token limits reduce costs while ensuring complete responses.

**Example** (`user/bot_openai.py`):
```python
for token_limit in range(self._token_from, self._token_max, self._token_increment):
    response = self._client.chat.completions.create(
        model=self._model,
        messages=messages,
        max_tokens=token_limit,
        stream=True
    )

    if response.choices[0].finish_reason != "length":
        break  # Complete response, no need to retry
```

### Custom Data Structures

#### DictNoNone
A custom dictionary that ignores `None` values to prevent pollution in message histories.

**Implementation** (`user/bot.py:9-13`):
```python
class DictNoNone(dict):
    def __setitem__(self, key, value):
        if key in self or value is not None:
            dict.__setitem__(self, key, value)
```

**Usage**:
```python
self._messages = DictNoNone()
self._messages['user1'] = None  # Ignored, doesn't set the key
self._messages['user1'] = []    # Accepted, sets the key
```

### Conversation Context Management

Each bot maintains per-user conversation histories to prevent cross-talk:

```python
self._messages = {
    'system_role': [{'role': 'system', 'content': system_role}],
    'alice': [
        {'role': 'user', 'content': 'Hello'},
        {'role': 'assistant', 'content': 'Hi Alice!'}
    ],
    'bob': [
        {'role': 'user', 'content': 'What is 2+2?'},
        {'role': 'assistant', 'content': '4'}
    ]
}
```

**Key Points**:
- `system_role` key contains shared system prompt
- Each username gets independent conversation array
- Conversation context persists for bot lifetime (no persistence layer yet)

### Async Event Handling

Discord uses decorator-based event handlers:

```python
@self.client.event
async def on_ready():
    self._check = True  # Mark as ready

@self.client.event
async def on_message(chat_msg):
    # Handle message
    await chat_msg.channel.send(response)
```

**Important**: All Discord event handlers must be `async` functions.

---

## API Contracts and Interfaces

### Bot Interface

All bot implementations must conform to the Bot base class contract:

```python
class Bot(User):
    # Required Properties
    @property
    def model(self) -> str:
        """Returns the LLM model identifier"""

    @property
    def llmprovider(self) -> str:
        """Returns the provider name (openai/anthropic/perplexity)"""

    @property
    def token_limits(self) -> range:
        """Returns the token limit range for progressive strategy"""

    @property
    def messages(self) -> DictNoNone:
        """Returns the conversation history dictionary"""

    # Required Methods
    def is_ready(self) -> bool:
        """Returns True if bot is connected and ready"""

    def chat_completion(self, name: str, message: str) -> str:
        """
        Processes a chat message and returns a response.

        Args:
            name: Username of the person sending the message
            message: The message content

        Returns:
            Complete response string from the LLM

        Implementation Requirements:
        1. Check if user exists in self._messages, create if not
        2. Append user message to conversation history
        3. Iterate through token limits (progressive strategy)
        4. Call LLM API with streaming
        5. Accumulate response chunks
        6. Check for truncation (finish_reason == "length")
        7. Retry with higher token limit if truncated
        8. Append assistant response to history
        9. Return complete response
        """
```

### Community Interface

All platform integrations must conform to the Community base class contract:

```python
class Community:
    # Required Properties
    @property
    def is_ready(self) -> bool:
        """Returns True if platform client is connected"""

    @property
    def bot(self) -> Bot:
        """Returns the injected bot instance"""

    # Required Methods
    async def start(self) -> None:
        """Start the platform client connection"""

    async def stop(self) -> None:
        """Gracefully stop the platform client"""
```

### ConfigLoader Interface

All configuration loaders must conform to the ConfigLoader base class contract:

```python
class ConfigLoader:
    @property
    def configuration(self) -> dict:
        """
        Returns configuration dictionary loaded from source.

        Returns:
            dict: Configuration with keys: amibot, discord, llm
            None: If loading failed

        Expected Structure:
        {
            'amibot': {
                'username': str,
                'system_role': str
            },
            'discord': {
                'enabled': bool,
                'token': str,
                'application_id': str,
                'public_key': str
            },
            'llm': {
                'provider': str,  # 'openai' | 'anthropic' | 'perplexity'
                'enabled': bool,
                'model': str,
                'key': str,
                'tokens_range': {
                    'from': int,
                    'until': int,
                    'increment': int
                }
            }
        }
        """
```

### LLM API Integration Patterns

#### OpenAI/Perplexity Pattern

```python
# Streaming API with progressive token limits
for token_limit in self.token_limits:
    response_stream = self.client.chat.completions.create(
        stream=True,
        model=self.model,
        max_tokens=token_limit,
        temperature=0.5,
        messages=self._messages[name]
    )

    # Accumulate streamed response
    for response in response_stream:
        if response.choices[0].finish_reason == "length":
            # Truncated - try next token limit
            break
        if response.choices[0].delta.content:
            assistant_message += response.choices[0].delta.content

    # Check if complete
    if completed:
        break
```

#### Anthropic Pattern

```python
# Context manager streaming with system role separation
for token_limit in self.token_limits:
    with self.client.messages.stream(
        model=self.model,
        system=f"{self._messages.get('system_role', [])}",
        temperature=0.5,
        max_tokens=token_limit,
        messages=self._messages[name]
    ) as response_stream:
        response_stream.until_done()
        response = response_stream.get_final_message()

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Complete
            break
        elif response.stop_reason == "max_tokens":
            # Truncated - continue with next limit
            continue
```

### Health Check API

**Endpoint**: `GET /liveness`
- **Success**: `200 OK {"message": "OK"}`
- **Failure**: `202 Not Ready` - Objects not initialized

**Endpoint**: `GET /readiness`
- **Success**: `200 OK {"message": "OK"}`
- **Failures**:
  - `500 Internal Error` - Both bot and community not ready
  - `503 Community is Offline` - Discord client not connected
  - `503 Bot is gone` - Bot client not initialized

---

## State Management

### Bot State Lifecycle

```
Initialization Phase:
├─ __init__() called
├─ API client created
├─ _messages initialized with DictNoNone
├─ system_role added to messages['system_role']
└─ _check = True (ready flag set)

Operational Phase (per message):
├─ chat_completion() called
├─ Check/create user in _messages
├─ Append user message
├─ Enter progressive token loop
│  ├─ Call LLM API
│  ├─ Stream response
│  └─ Check completion status
├─ Append assistant message
└─ Return response

Error States:
├─ Client connection fails → _check = False
├─ API error → Log and continue
└─ Rate limit → Retry with backoff
```

### Conversation State

**Per-User Isolation**:
```python
_messages = DictNoNone()

# System role shared across all users
_messages['system_role'] = [
    {'role': 'system', 'content': 'Bot personality...'}
]

# Individual user conversations
_messages['alice'] = [
    {'role': 'user', 'content': 'Alice says: Hello'},
    {'role': 'assistant', 'content': 'Hi Alice!'}
]

_messages['bob'] = [
    {'role': 'user', 'content': 'Bob says: What is Python?'},
    {'role': 'assistant', 'content': 'Python is a programming language...'}
]
```

**State Persistence**:
- ⚠️ **Not Implemented**: Conversations are lost on restart (known issue: "amnesia")
- **In-Memory Only**: `_messages` dictionary stored in bot instance
- **No Database**: No external persistence layer
- **TODO**: Add database support (Pinecone, DynamoDB, PostgreSQL)

### Discord Client State

```
Connection Lifecycle:
├─ Created: Client instantiated
├─ Connecting: start() called, connecting to Discord
├─ Connected: on_connect() triggered
├─ Ready: on_ready() triggered, _check = True
├─ Processing: on_message() handling messages
├─ Error: on_error() triggered, _check = False
└─ Stopped: stop() called, client closed
```

**State Transitions**:
1. `Created → Connecting`: `await client.start(token)`
2. `Connecting → Connected`: Discord WebSocket established
3. `Connected → Ready`: Bot user loaded, can receive events
4. `Ready → Processing`: Message event received
5. `Processing → Ready`: Message handled, waiting for next
6. `Ready/Error → Stopped`: `await client.close()`

### Application State

**Global State** (`__main__.py`):
```python
# Global variables (module-level)
amigo = None        # Bot instance
community = None    # Discord instance
load = None         # ConfigLoader instance

# State transitions:
# 1. Parse arguments
# 2. Load configuration
# 3. Instantiate bot (amigo)
# 4. Instantiate community
# 5. Inject bot into community (community.bot = amigo)
# 6. Start event loop
```

**Event Loop State**:
- Single `asyncio` event loop manages both Discord and FastAPI
- Two concurrent tasks:
  1. `community.start()` - Discord client
  2. `api_server.serve()` - Health check API

---

## Error Handling and Resilience

### Discord Rate Limiting

**Pattern**: Exponential backoff with retry

```python
try:
    await chat_msg.channel.send(msg)
except discord.errors.RateLimited as e:
    await asyncio.sleep(e.retry_after)  # Wait required time
    await chat_msg.channel.send(msg)    # Retry once
finally:
    time.sleep(1)  # Always wait 1s between chunks
```

**Rate Limit Details**:
- Discord limits: 5 messages per 5 seconds per channel
- 2000 character limit per message
- `retry_after` provided in exception (seconds to wait)

### LLM API Errors

**OpenAI/Perplexity**:
```python
# No explicit error handling in current implementation
# Errors propagate to Discord handler
# TODO: Add try/except for:
# - openai.error.RateLimitError
# - openai.error.APIConnectionError
# - openai.error.AuthenticationError
```

**Anthropic**:
```python
# Stream context manager handles connection errors
# Usage tracking available:
response.usage.input_tokens
response.usage.output_tokens

# Stop reasons:
# - "end_turn": Normal completion
# - "max_tokens": Truncated, retry with more tokens
# - Other reasons logged but not handled
```

### Configuration Loading Errors

**YAML Parsing**:
```python
try:
    configuration = yaml.safe_load(stream)
except yaml.YAMLError as exc:
    print(f"Exception: {exc}")
    return None  # Caller must handle None
```

**S3 Access Errors**:
```python
# boto3 exceptions not explicitly caught
# Will raise:
# - botocore.exceptions.NoCredentialsError
# - botocore.exceptions.ClientError
# - botocore.exceptions.ParamValidationError

# TODO: Add explicit error handling
```

### Progressive Token Strategy Resilience

**Cost Control**:
```python
# Start with minimum tokens
for token_limit in range(256, 4096, 256):
    # Make API call
    if response_complete:
        break
    # Otherwise retry with more tokens
```

**Benefits**:
- Prevents overspending on simple queries
- Ensures quality responses for complex queries
- Graceful degradation (warns at max limit)

**Failure Modes**:
- All token limits exhausted: Returns partial response with warning
- API timeout: Returns empty/partial response
- API error: Exception propagates (not caught)

### Graceful Shutdown

```python
async def shutdown_event():
    """Called on FastAPI lifespan shutdown"""
    await community.stop()    # Close Discord connection
    amigo.client.close()      # Close LLM client

# Triggered by:
# - Ctrl+C (KeyboardInterrupt)
# - SIGTERM signal
# - Application error
```

### Known Error Scenarios

1. **Long messages interrupted**: Sometimes Discord responses cut in half
   - **Cause**: Unknown (rate limiting? typing indicator timeout?)
   - **Workaround**: None currently
   - **TODO**: Investigate and add retry logic

2. **Chunking breaks formatting**: Messages split mid-word/code-block
   - **Cause**: Naive 2000-char chunking
   - **Workaround**: None currently
   - **TODO**: Smart chunking respecting boundaries

3. **No usage stats from OpenAI**: Can't track token consumption
   - **Cause**: API change (streaming no longer provides usage)
   - **Workaround**: None
   - **TODO**: Use non-streaming or token counting library

4. **Conversation amnesia**: Context lost on restart
   - **Cause**: No persistence layer
   - **Workaround**: None
   - **TODO**: Implement database storage

---

## Testing and CI/CD

### Current Testing Status

**⚠️ No Test Suite**: The project currently lacks automated tests. This is a gap that should be addressed.

**Recommended Testing Strategy**:
1. **Unit Tests**: Test individual bot implementations, config loaders
2. **Integration Tests**: Test Discord message flow, LLM API interactions
3. **End-to-End Tests**: Test complete message → response cycle

**Framework Recommendation**: `pytest` + `pytest-asyncio` for async tests

### CI/CD Pipeline

**CircleCI Workflow** (`.circleci/config.yml`):

```yaml
workflows:
  version: 2
  pipeline:
    jobs:
      - prepare             # Generate Terraform vars from cloud_settings.json
      - terraform-plan:     # Plan infrastructure changes
          requires:
            - prepare
      - terraform-approve:  # Manual approval gate
          type: approval
          requires:
            - terraform-plan
      - terraform-apply:    # Apply approved changes
          requires:
            - terraform-approve
```

**Pipeline Stages**:

1. **prepare** (executor: `python:3.13`):
   - Runs `scripts/get_variablestf.py`
   - Generates `terraform.tfvars` from `configs/cloud_settings.json`
   - Persists to workspace

2. **terraform-plan** (executor: `hashicorp/terraform:1.11`):
   - Attaches workspace
   - Runs `terraform init`
   - Runs `terraform plan`
   - Persists plan to workspace

3. **terraform-approve** (manual step):
   - Requires human approval in CircleCI UI
   - Prevents accidental infrastructure changes

4. **terraform-apply** (executor: `hashicorp/terraform:1.11`):
   - Attaches workspace
   - Runs `terraform apply` with approved plan
   - Deploys to AWS ECS

**Triggering CI/CD**:
- Push to main branch (or configured branch)
- Manual trigger via CircleCI UI

---

## Common Tasks

### Task 1: Update Bot Personality

**File**: `configs/amibot.conf`

```yaml
amibot:
  username: "amigo"
  system_role: |
    You are {username}, a friendly and knowledgeable assistant.
    You specialize in software engineering topics.
    Always provide code examples when relevant.
```

**Note**: `{username}` is automatically replaced with the value of `amibot.username`.

**Apply Changes**:
- **Local**: Restart the bot
- **Docker**: Restart container
- **Kubernetes**: Update ConfigMap and restart pod (see Kubernetes Deployment section)

### Task 2: Switch LLM Provider

**File**: `configs/amibot.conf`

```yaml
llm:
  provider: "openai"  # Change to "anthropic" or "perplexity"
  model: "gpt-4o"     # Update model accordingly
  key: "sk-..."       # Update API key
```

**Model Recommendations**:
- **OpenAI**: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-5-sonnet-20240620`, `claude-3-opus-20240229`
- **Perplexity**: `sonar`, `sonar-pro`

### Task 3: Adjust Token Limits

**File**: `configs/amibot.conf`

```yaml
llm:
  tokens_range:
    from: 512        # Start with larger responses
    until: 8192      # Allow longer responses
    increment: 512   # Larger increments
```

**Cost vs. Quality Tradeoffs**:
- **Lower `from`**: Cheaper, but may truncate responses
- **Higher `until`**: Better quality, but more expensive
- **Larger `increment`**: Fewer retries, faster responses, but less granular

### Task 4: Add Logging

**Recommendation**: Use Python's `logging` module instead of `print()` statements.

**Example** (`amibot/__main__.py`):
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Replace print() with logger calls
logger.info(f"Username: {amigo.name}")
logger.info(f"Platform: {amigo.llmprovider}")
logger.info(f"Model: {amigo.model}")
```

### Task 5: Debug Health Check Issues

**Check Health Endpoints**:
```bash
# Liveness (checks if objects exist)
curl http://localhost:23459/liveness

# Readiness (checks if bot and community are ready)
curl http://localhost:23459/readiness
```

**Common Issues**:
- **202 Not Ready**: Bot or community objects are `None` (initialization failed)
- **500 Internal Error**: Both `is_ready()` returned `False`
- **503 Community Offline**: Discord client not connected
- **503 Bot Gone**: Bot initialization failed

**Debug Steps**:
1. Check logs for initialization errors
2. Verify configuration is valid
3. Confirm API keys are correct
4. Check network connectivity (Discord, LLM APIs)

### Task 6: Monitor Token Usage

**Current Implementation**:
- OpenAI: ⚠️ Streaming API no longer provides usage stats (see FIXME in `bot_openai.py:82`)
- Anthropic: Tracks `input_tokens` and `output_tokens` from API response
- Perplexity: Same as OpenAI (no usage stats in streaming)

**Recommendation**: Add logging in `chat_completion()` methods:
```python
logger.info(f"User: {user}, Tokens: {input_tokens}/{output_tokens}")
```

---

## Known Issues and TODOs

### Known Issues

#### 1. Message Chunking Breaks Formatting
**Location**: `community/discord_client.py:60-68`

**Issue**: Discord has a 2000-character limit. The current chunking logic:
```python
while response:
    chunk, response = response[:2000], response[2000:]
    await chat_msg.channel.send(chunk)
```

**Problem**: Breaks in the middle of words, code blocks, sentences.

**Workaround**: None currently.

**TODO**: Implement smart chunking that respects:
- Sentence boundaries
- Code block markers (```)
- Markdown formatting

#### 2. Long Responses Get Interrupted
**Location**: `community/discord_client.py:55-57` (comment)

**Issue**: Sometimes long responses are cut in half.

**Suspected Cause**: Discord rate limiting or typing indicator timeout.

**TODO**: Investigate rate limiting, implement proper backoff strategy.

#### 3. OpenAI Streaming No Longer Provides Usage Stats
**Location**: `user/bot_openai.py:82` (FIXME comment)

**Issue**: OpenAI's streaming API changed; `stream_chunk.usage` is now `None`.

**Workaround**: None (usage stats not tracked for OpenAI).

**TODO**: Use non-streaming API for usage tracking, or implement token counting library.

#### 4. No Conversation Persistence
**Location**: Throughout bot implementations

**Issue**: Conversation context is lost when bot restarts (amnesia).

**TODO**: Implement database storage (Pinecone, DynamoDB, PostgreSQL) for conversation history.

#### 5. Gateway Pattern is Expensive
**Location**: README.md TODO section

**Issue**: Current architecture uses a gateway pattern that may be costly.

**TODO**: Evaluate alternative patterns or optimize resource usage.

### Project TODOs

From `README.md`:

- [ ] **Make it cheaper**: Optimize gateway pattern or reduce resource usage
- [x] **Remove local config requirement**: S3 configuration support added
- [x] **Add healthcheck**: FastAPI endpoints implemented
- [ ] **Cure amnesia**: Add database for conversation persistence
- [ ] **K8s: Move config to Secrets**: Currently uses ConfigMap (less secure)
- [ ] **K8s: Use kubeseal**: Encrypt secrets with Sealed Secrets

### Security Considerations

#### Current Security Posture

**Strengths**:
- Docker container runs as `nobody` user (non-root)
- IAM role grants minimal S3 read permissions
- Secrets not exposed in Community `__str__()` method

**Weaknesses**:
- **Kubernetes**: Secrets stored in ConfigMap (plaintext in etcd)
- **No secret rotation**: API keys are static
- **No rate limiting**: Could be vulnerable to abuse
- **No input validation**: Messages passed directly to LLM APIs

#### Recommendations

1. **Use Kubernetes Secrets** instead of ConfigMap:
   ```bash
   kubectl create secret generic amibot-config --from-file=configs/amibot.conf
   ```

2. **Implement Sealed Secrets** (kubeseal):
   ```bash
   kubeseal --format yaml < secret.yaml > sealed-secret.yaml
   kubectl apply -f sealed-secret.yaml
   ```

3. **Add Rate Limiting** (per-user message limits):
   ```python
   # In discord_client.py
   from collections import defaultdict
   from time import time

   rate_limits = defaultdict(list)

   async def on_message(chat_msg):
       user_id = str(chat_msg.author.id)
       now = time()

       # Allow 5 messages per minute
       rate_limits[user_id] = [t for t in rate_limits[user_id] if now - t < 60]
       if len(rate_limits[user_id]) >= 5:
           await chat_msg.channel.send("You're sending messages too quickly!")
           return

       rate_limits[user_id].append(now)
       # Continue with normal processing
   ```

4. **Validate User Input**:
   - Sanitize message content before passing to LLM
   - Implement content filters (profanity, PII, etc.)
   - Add maximum message length limits

5. **Use Secret Management Services**:
   - **AWS**: Secrets Manager or Parameter Store
   - **Kubernetes**: External Secrets Operator
   - **HashiCorp**: Vault (TODOs mention this)

---

## Additional Notes for AI Assistants

### When Modifying Code

1. **Read Before Edit**: Always read the file completely before making changes.

2. **Preserve Patterns**: Maintain existing code patterns (properties, DictNoNone, async/await).

3. **Test Locally**: If possible, test changes locally before committing:
   ```bash
   ./scripts/build.sh
   python -m amibot -c configs/amibot.conf
   ```

4. **Update Documentation**: If adding features, update this CLAUDE.md file.

5. **Check Dependencies**: If adding new libraries, update `requirements.txt`:
   ```bash
   pip freeze | grep <library> >> requirements.txt
   ```

### When Debugging

1. **Check Health Endpoints First**:
   ```bash
   curl http://localhost:23459/readiness
   ```

2. **Review Logs**: Look for initialization errors, API failures, Discord connection issues.

3. **Verify Configuration**: Ensure all required fields are present in config file.

4. **Test Bot Isolation**: Test bot implementations separately from Discord integration.

### When Deploying

1. **Kubernetes**: Use `kubectl apply -k .` (Kustomize handles ConfigMap generation).

2. **AWS ECS**: Use CircleCI pipeline or manual Terraform.

3. **Docker**: Mount config file as read-only volume:
   ```bash
   -v $(pwd)/configs/amibot.conf:/nonexistent/configs/amibot.conf:ro
   ```

4. **Health Checks**: Ensure orchestrator probes port 23459 endpoints.

### Code Locations Reference

| Functionality | File | Line(s) |
|---------------|------|---------|
| Entry point | `amibot/__main__.py` | 102-189 |
| Config loading strategy | `amibot/__main__.py` | 119-130 |
| Bot instantiation | `amibot/__main__.py` | 152-178 |
| Health endpoints | `amibot/__main__.py` | 36-57 |
| OpenAI implementation | `amibot/user/bot_openai.py` | 19-96 |
| Anthropic implementation | `amibot/user/bot_anthropic.py` | 13-90 |
| Discord message handling | `amibot/community/discord_client.py` | 39-77 |
| S3 config loader | `amibot/configloader/FromS3.py` | 14-39 |
| DictNoNone helper | `amibot/user/bot.py` | 9-13 |
| Progressive token strategy | `amibot/user/bot_openai.py` | 44-92 |

---

## Glossary

- **AmiBot**: The project name (also the bot's default username)
- **Community**: Platform integration layer (currently only Discord)
- **LLM**: Large Language Model (OpenAI, Anthropic, Perplexity)
- **System Role**: System prompt defining bot personality
- **Token Limit**: Maximum tokens in LLM response
- **Progressive Token Strategy**: Incrementally increasing token limits to reduce costs
- **Health Probe**: Kubernetes/ECS endpoint for checking service health
- **Kustomize**: Kubernetes configuration management tool
- **ECS**: AWS Elastic Container Service (Fargate)
- **ConfigMap**: Kubernetes configuration object (plaintext)
- **Secret**: Kubernetes secure configuration object (base64-encoded)

---

## Changelog

### 2025-11-15 (Update 2)
- **Added comprehensive technical diagrams** in documentation/TECHNICAL_DIAGRAMS.md:
  - Class diagrams with full inheritance hierarchy
  - Sequence diagrams for all major flows (startup, message handling, token strategy, config loading, health checks)
  - State diagrams for bot and Discord lifecycles
  - Data flow diagrams for conversation context and message routing
  - Deployment architecture diagrams for Kubernetes and AWS ECS
  - CI/CD pipeline flow diagram
  - Component interaction diagram
- **Added new documentation sections**:
  - API Contracts and Interfaces (Bot, Community, ConfigLoader)
  - LLM API Integration Patterns (OpenAI/Perplexity, Anthropic)
  - State Management (Bot lifecycle, conversation state, Discord state, application state)
  - Error Handling and Resilience (rate limiting, API errors, config errors, graceful shutdown)
- Enhanced architecture documentation with diagram references
- Improved code location references

### 2025-11-15 (Initial)
- Initial CLAUDE.md creation
- Documented complete codebase structure
- Added development guidelines
- Added deployment instructions
- Documented known issues and TODOs
- **Security Fix**: Updated setuptools from 75.2.0 to >=78.1.1 to fix CVE-2025-47273 (path traversal vulnerability)

---

**For Questions or Issues**:
- Check this document first
- Review code comments (especially FIXMEs and TODOs)
- Consult README.md for user-facing documentation
- Contact: pro@donrudo.com
