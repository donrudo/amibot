# AmiBot Technical Diagrams and Architecture

This document contains detailed technical diagrams and architecture documentation for AmiBot.

## Table of Contents
1. [Class Diagram](#class-diagram)
2. [Sequence Diagrams](#sequence-diagrams)
3. [State Diagrams](#state-diagrams)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Deployment Architecture](#deployment-architecture)

---

## Class Diagram

### Complete Class Hierarchy

```mermaid
classDiagram
    %% Base Classes
    class User {
        -string _name
        -string _llmprovider
        -bool _check
        +__init__(name, llmprovider, secret)
        +__str__() string
        +name property
        +is_ready property
        +platform property
    }

    class Bot {
        -string _model
        -client _client
        -DictNoNone _messages
        -range _token_limits
        +__init__(name, llmprovider, secret, system_role)
        +model property
        +llmprovider property
        +token_limits property
        +client property
        +messages property
        +is_ready() bool
        +get_urls(input) list
        +chat_completion(name, message) string
    }

    class DictNoNone {
        +__setitem__(key, value)
    }

    class OpenaiBot {
        -OpenAI _client
        -string _model "gpt-4o"
        -range _token_limits
        +__init__(name, llmprovider, secret, token_min, token_max, token_increment, system_role)
        +chat_completion(name, message) string
    }

    class AnthropicBot {
        -Anthropic _client
        -range _token_limits
        +__init__(name, llmprovider, secret, token_min, token_max, token_increment, system_role)
        +chat_completion(name, message) string
    }

    class PerplexityBot {
        -OpenAI _client
        -string _model "sonar"
        -range _token_limits
        +__init__(name, llmprovider, secret, token_min, token_max, token_increment, system_role)
        +chat_completion(name, message) string
    }

    %% Community Classes
    class Community {
        -string _platform
        -string _secret
        -Bot _bot
        -bool _check
        +__init__(platform, secret)
        +__str__() string
        +secret property
        +platform property
        +is_ready property
        +bot property
    }

    class Discord {
        -Client client
        +__init__(secret)
        +is_ready() bool
        +start() async
        +stop() async
        -on_connect() async
        -on_ready() async
        -on_error() async
        -on_message(chat_msg) async
        -split_into_chunks(message, chunk_size) list
    }

    %% Config Loader Classes
    class ConfigLoader {
        -string _path
        +__init__(path)
        +configuration property
    }

    class FromFile {
        +__init__(path)
        +configuration property
    }

    class FromS3 {
        -string _bucket
        -string _location
        -string _address
        +__init__(url)
        +configuration property
    }

    %% Relationships
    User <|-- Bot : extends
    Bot <|-- OpenaiBot : extends
    Bot <|-- AnthropicBot : extends
    Bot <|-- PerplexityBot : extends
    Bot *-- DictNoNone : uses
    Community <|-- Discord : extends
    Community o-- Bot : has-a
    ConfigLoader <|-- FromFile : extends
    ConfigLoader <|-- FromS3 : extends
    dict <|-- DictNoNone : extends
```

---

## Sequence Diagrams

### 1. Application Startup Sequence

```mermaid
sequenceDiagram
    participant Main as __main__.py
    participant Parser as argparse
    participant Loader as ConfigLoader
    participant BotFactory as Bot Factory
    participant Bot as Bot Instance
    participant Community as Discord
    participant FastAPI as Health API
    participant Loop as Event Loop

    Main->>Parser: Parse CLI arguments
    Parser-->>Main: args (config path)

    Main->>Main: Analyze config protocol
    alt S3 Protocol
        Main->>Loader: FromS3(url)
    else File Protocol
        Main->>Loader: FromFile(path)
    end

    Loader->>Loader: Load YAML config
    Loader-->>Main: configuration dict

    Main->>BotFactory: Match provider type
    alt OpenAI
        BotFactory->>Bot: OpenaiBot(params)
    else Anthropic
        BotFactory->>Bot: AnthropicBot(params)
    else Perplexity
        BotFactory->>Bot: PerplexityBot(params)
    end

    Bot->>Bot: Initialize client
    Bot->>Bot: Setup system_role
    Bot-->>Main: bot instance

    Main->>Community: Discord(token)
    Community->>Community: Setup Discord client
    Community->>Community: Register event handlers
    Community-->>Main: community instance

    Main->>Community: Set bot property
    Community-->>Main: Bot injected

    Main->>FastAPI: Create FastAPI app
    Main->>FastAPI: Setup /liveness endpoint
    Main->>FastAPI: Setup /readiness endpoint

    Main->>Loop: Create event loop
    Main->>Loop: Start community.start()
    Main->>Loop: Start api_server.serve()

    Loop->>Community: Run Discord client
    Loop->>FastAPI: Run health API
```

### 2. Message Handling Flow

```mermaid
sequenceDiagram
    participant User as Discord User
    participant Discord as Discord Client
    participant Handler as on_message
    participant Bot as Bot Instance
    participant LLM as LLM API
    participant Response as Discord Channel

    User->>Discord: Send message
    Discord->>Handler: Trigger on_message(chat_msg)

    Handler->>Handler: Check if DM or @mention
    alt Not relevant
        Handler-->>Discord: Ignore message
    end

    Handler->>Handler: Check if not self
    alt Is self message
        Handler-->>Discord: Ignore message
    end

    Handler->>Bot: chat_completion(username, message)

    Bot->>Bot: Check if user in _messages
    alt New user
        Bot->>Bot: Initialize with system_role
    end

    Bot->>Bot: Append user message

    loop For each token_limit in range
        Bot->>LLM: Stream completion request
        LLM-->>Bot: Stream response chunks

        Bot->>Bot: Accumulate response

        alt finish_reason == "length"
            Bot->>Bot: Increase token limit
        else Response complete
            Bot->>Bot: Break loop
        end
    end

    Bot->>Bot: Append assistant message
    Bot-->>Handler: Complete response string

    Handler->>Handler: split_into_chunks(response)

    loop For each chunk
        Handler->>Response: Send chunk (async)
        Response->>Response: Show typing indicator
        alt Rate limited
            Response-->>Handler: RateLimited exception
            Handler->>Handler: Sleep(retry_after)
            Handler->>Response: Retry send
        end
        Handler->>Handler: Sleep(1s)
    end

    Response-->>User: Display message chunks
```

### 3. Progressive Token Strategy Flow

```mermaid
sequenceDiagram
    participant Bot
    participant TokenLoop as Token Loop
    participant LLM as LLM API
    participant Stream as Response Stream

    Bot->>TokenLoop: range(token_from, token_max, increment)

    loop For each token_limit
        Note over Bot,Stream: Attempt: 256 → 512 → 768 → ... → 4096

        TokenLoop->>LLM: Create completion(max_tokens=current_limit)
        LLM->>Stream: Start streaming response

        loop For each chunk
            Stream->>Bot: Delta content
            Bot->>Bot: Accumulate message

            alt finish_reason == "length"
                Note over Bot: Response truncated!
                Stream-->>Bot: Incomplete flag
                Bot->>Bot: Break chunk loop
                Bot->>TokenLoop: Try next token_limit
            else finish_reason == "stop"
                Note over Bot: Response complete!
                Stream-->>Bot: Complete response
                Bot->>Bot: Append to history
                Bot-->>TokenLoop: Break token loop
            end
        end
    end

    alt Max token limit reached
        Note over Bot: Still truncated at max
        Bot->>Bot: Prepend "Max tokens limit reached"
    end

    Bot-->>Bot: Return complete response
```

### 4. Configuration Loading Flow

```mermaid
sequenceDiagram
    participant Main as __main__.py
    participant Parser as Protocol Parser
    participant FromFile
    participant FromS3
    participant S3 as AWS S3
    participant YAML as YAML Parser

    Main->>Parser: args.config

    Parser->>Parser: Split on ':'

    alt Protocol: "file:"
        Parser->>FromFile: FromFile(path)
        FromFile->>FromFile: Open file
        FromFile->>YAML: safe_load(stream)
        YAML-->>FromFile: dict
        FromFile-->>Main: configuration
    else Protocol: "s3:" or "https:"
        Parser->>FromS3: FromS3(url)
        FromS3->>FromS3: Parse URL components
        FromS3->>FromS3: Extract bucket and key
        FromS3->>S3: boto3.get_object(bucket, key)
        S3-->>FromS3: Response body
        FromS3->>YAML: safe_load(body)
        YAML-->>FromS3: dict
        FromS3-->>Main: configuration
    else No protocol
        Parser->>FromFile: FromFile(args.config)
        FromFile->>FromFile: Open file
        FromFile->>YAML: safe_load(stream)
        YAML-->>FromFile: dict
        FromFile-->>Main: configuration
    end
```

### 5. Health Check Flow

```mermaid
sequenceDiagram
    participant K8s as Kubernetes/ECS
    participant API as FastAPI
    participant Main as __main__.py
    participant Community as Discord
    participant Bot as Bot Instance

    K8s->>API: GET /liveness
    API->>Main: Check if amigo is not None
    API->>Main: Check if community is not None
    alt Both exist
        API-->>K8s: 200 OK
    else One or both None
        API-->>K8s: 202 Not Ready
    end

    K8s->>API: GET /readiness
    API->>Community: is_ready()
    Community-->>API: bool
    API->>Bot: is_ready()
    Bot-->>API: bool

    alt Both ready
        API-->>K8s: 200 OK {"message": "OK"}
    else Both not ready
        API-->>K8s: 500 Internal Error
    else Community not ready
        API-->>K8s: 503 Community Offline
    else Bot not ready
        API-->>K8s: 503 Bot Gone
    end
```

---

## State Diagrams

### Bot Lifecycle States

```mermaid
stateDiagram-v2
    [*] --> Initializing: __init__()

    Initializing --> Ready: Client connected
    Initializing --> Failed: Connection error

    Ready --> Processing: chat_completion() called
    Processing --> Ready: Response complete
    Processing --> Failed: API error

    Failed --> Ready: Reconnection successful

    Ready --> Shutdown: stop() called
    Shutdown --> [*]

    note right of Ready
        _check = True
        Client connected
        Messages initialized
    end note

    note right of Processing
        Streaming from LLM
        Accumulating response
        Managing token limits
    end note

    note right of Failed
        _check = False
        Client closed/error
    end note
```

### Discord Client States

```mermaid
stateDiagram-v2
    [*] --> Created: __init__()

    Created --> Connecting: start() called
    Connecting --> Connected: on_connect()
    Connected --> Ready: on_ready()

    Ready --> Processing: on_message() triggered
    Processing --> Ready: Message sent

    Ready --> Error: on_error()
    Error --> Reconnecting: Auto-retry
    Reconnecting --> Connected: Success
    Reconnecting --> Terminated: Max retries

    Ready --> Stopping: stop() called
    Stopping --> Terminated: Connection closed
    Terminated --> [*]

    note right of Ready
        _check = True
        Can receive messages
        Bot injected
    end note

    note right of Processing
        Calling bot.chat_completion()
        Chunking response
        Handling rate limits
    end note
```

---

## Data Flow Diagrams

### Conversation Context Management

```mermaid
graph TB
    subgraph Bot Instance
        SystemRole[System Role Message]
        Messages[DictNoNone _messages]

        subgraph User Contexts
            User1[alice: List of messages]
            User2[bob: List of messages]
            User3[charlie: List of messages]
        end
    end

    SystemRole --> Messages
    Messages --> User1
    Messages --> User2
    Messages --> User3

    User1 --> Msg1A[role: user, content: Hello]
    User1 --> Msg1B[role: assistant, content: Hi Alice!]
    User1 --> Msg1C[role: user, content: How are you?]

    User2 --> Msg2A[role: user, content: What is 2+2?]
    User2 --> Msg2B[role: assistant, content: 4]

    style SystemRole fill:#e1f5ff
    style Messages fill:#fff4e1
    style User1 fill:#e8f5e9
    style User2 fill:#e8f5e9
    style User3 fill:#e8f5e9
```

### Message Flow Through System

```mermaid
graph LR
    A[Discord User] --> B{Discord Client}
    B --> C{Message Filter}

    C -->|DM| D[Bot.chat_completion]
    C -->|@mention| D
    C -->|@everyone| D
    C -->|Ignore| E[Drop]

    D --> F{User Context Exists?}
    F -->|No| G[Create with System Role]
    F -->|Yes| H[Append to Existing]

    G --> I[Add User Message]
    H --> I

    I --> J{Token Loop}

    J --> K[LLM API Call]
    K --> L{Response Complete?}

    L -->|No - Truncated| M[Increase Token Limit]
    M --> J

    L -->|Yes - Complete| N[Append Assistant Reply]

    N --> O[Split into 2000-char Chunks]
    O --> P[Send to Discord Channel]

    P --> Q{Rate Limited?}
    Q -->|Yes| R[Sleep & Retry]
    Q -->|No| S[Next Chunk]

    R --> P
    S --> T[Complete]

    style D fill:#ffebee
    style K fill:#e3f2fd
    style N fill:#e8f5e9
    style P fill:#f3e5f5
```

---

## Deployment Architecture

### Kubernetes Deployment

```mermaid
graph TB
    subgraph Kubernetes Cluster
        subgraph Namespace: development
            subgraph Pod: amibot
                Container[AmiBot Container<br/>Port 23459]
                ConfigMount[ConfigMap Volume<br/>/nonexistent/configs]
            end

            ConfigMap[ConfigMap<br/>Generated from configs/amibot.conf]
        end

        subgraph Health Probes
            Liveness[Liveness Probe<br/>GET /liveness]
            Readiness[Readiness Probe<br/>GET /readiness]
        end
    end

    Registry[GitLab Container Registry<br/>registry.gitlab.com/donrudo/amibot:0.0.6.0]
    Discord[Discord API<br/>Gateway WebSocket]
    LLM[LLM APIs<br/>OpenAI/Anthropic/Perplexity]

    Registry --> Container
    ConfigMap --> ConfigMount
    ConfigMount --> Container
    Container --> Liveness
    Container --> Readiness
    Container <--> Discord
    Container <--> LLM

    style Container fill:#e3f2fd
    style ConfigMap fill:#fff9c4
    style Liveness fill:#c8e6c9
    style Readiness fill:#c8e6c9
```

### AWS ECS Deployment

```mermaid
graph TB
    subgraph AWS Cloud
        subgraph VPC
            subgraph ECS Cluster: botfarm
                subgraph Fargate Task
                    Container[AmiBot Container<br/>CPU: 256<br/>RAM: 512MB]
                    S3Config[S3 Config Loader]
                end
            end

            subgraph IAM
                TaskRole[Task Execution Role<br/>S3 Read Access]
            end
        end

        S3Bucket[S3 Bucket<br/>Config Storage]
        CloudWatch[CloudWatch Logs]
    end

    Registry[GitLab Registry]
    Discord[Discord API]
    LLM[LLM APIs]

    Registry --> Container
    TaskRole --> Container
    TaskRole --> S3Bucket
    S3Bucket --> S3Config
    S3Config --> Container
    Container --> CloudWatch
    Container <--> Discord
    Container <--> LLM

    style Container fill:#e3f2fd
    style S3Bucket fill:#fff9c4
    style TaskRole fill:#ffccbc
    style CloudWatch fill:#d1c4e9
```

### CI/CD Pipeline Flow

```mermaid
graph LR
    A[Git Push] --> B[CircleCI Triggered]

    B --> C[Job: prepare]
    C --> D[Generate terraform.tfvars<br/>from cloud_settings.json]
    D --> E[Persist to Workspace]

    E --> F[Job: terraform-plan]
    F --> G[terraform init]
    G --> H[terraform plan]
    H --> I[Persist Plan]

    I --> J[Job: terraform-approve<br/>Manual Gate]

    J -->|Approved| K[Job: terraform-apply]
    K --> L[terraform apply]
    L --> M[Update ECS Service]
    M --> N[Deploy New Task]

    J -->|Rejected| O[Stop Pipeline]

    style C fill:#e3f2fd
    style F fill:#fff9c4
    style J fill:#ffccbc
    style K fill:#c8e6c9
```

---

## Component Interaction Diagram

```mermaid
graph TB
    subgraph External Services
        DiscordAPI[Discord API]
        OpenAIAPI[OpenAI API]
        AnthropicAPI[Anthropic API]
        PerplexityAPI[Perplexity API]
        S3[AWS S3]
    end

    subgraph AmiBot Application
        subgraph Main Process
            MainPy[__main__.py<br/>Orchestrator]
            FastAPI[FastAPI Server<br/>Port 23459]
        end

        subgraph Bot Layer
            Bot[Bot Base]
            OpenAI[OpenaiBot]
            Anthropic[AnthropicBot]
            Perplexity[PerplexityBot]
        end

        subgraph Community Layer
            Community[Community Base]
            DiscordClient[Discord Client]
        end

        subgraph Config Layer
            ConfigLoader[ConfigLoader]
            FromFile[FromFile]
            FromS3[FromS3]
        end
    end

    subgraph Configuration
        LocalFile[Local YAML]
        S3File[S3 YAML]
    end

    MainPy --> ConfigLoader
    ConfigLoader --> FromFile
    ConfigLoader --> FromS3
    FromFile --> LocalFile
    FromS3 --> S3
    S3 --> S3File

    MainPy --> Bot
    Bot --> OpenAI
    Bot --> Anthropic
    Bot --> Perplexity

    MainPy --> Community
    Community --> DiscordClient

    DiscordClient --> Bot
    DiscordClient --> DiscordAPI

    OpenAI --> OpenAIAPI
    Anthropic --> AnthropicAPI
    Perplexity --> PerplexityAPI

    MainPy --> FastAPI

    style MainPy fill:#e1f5ff
    style Bot fill:#fff4e1
    style Community fill:#f3e5f5
    style ConfigLoader fill:#e8f5e9
```

---

## DictNoNone Custom Data Structure

```mermaid
graph TB
    subgraph Standard Python Dict
        A[dict]
    end

    subgraph DictNoNone Custom Dict
        B[DictNoNone]
        C[__setitem__ override]
    end

    A -->|extends| B
    B --> C

    D[Set key=value] --> E{value is None?}
    E -->|Yes| F{key already exists?}
    F -->|Yes| G[Update value]
    F -->|No| H[Ignore - Don't set]
    E -->|No| I[Set key=value normally]

    style B fill:#e3f2fd
    style C fill:#fff9c4
    style H fill:#ffebee
    style I fill:#e8f5e9
```

**Purpose**: Prevents `None` values from polluting message histories. If a key doesn't exist and you try to set it to `None`, the operation is ignored.

**Example**:
```python
messages = DictNoNone()
messages['user1'] = None      # Ignored - key not created
messages['user1'] = []        # Accepted - key created with empty list
messages['user1'] = None      # Accepted - key exists, can be updated
```

---

## Progressive Token Allocation Strategy

```mermaid
graph LR
    A[Start: token_min=256] --> B{Make API Call}
    B --> C{Response Complete?}

    C -->|Yes| D[Success - Return Response]
    C -->|No - Truncated| E[Increment: +256]

    E --> F{At token_max?}
    F -->|No| B
    F -->|Yes| G[Return with Warning:<br/>'Max tokens limit reached']

    style A fill:#e3f2fd
    style D fill:#c8e6c9
    style G fill:#ffccbc
```

**Benefits**:
- **Cost Optimization**: Start with minimum tokens, only increase when needed
- **Quality Assurance**: Retry with more tokens if response truncated
- **Transparency**: Warn user when max limit reached

**Example Configuration**:
```yaml
tokens_range:
  from: 256        # Start cheap
  until: 4096      # Allow quality
  increment: 256   # Gradual increase
```

**Token Progression**: 256 → 512 → 768 → 1024 → 1280 → ... → 4096

---

## Error Handling Patterns

```mermaid
graph TB
    subgraph Discord Rate Limiting
        A[Send Message] --> B{Rate Limited?}
        B -->|No| C[Success]
        B -->|Yes| D[Catch RateLimited Exception]
        D --> E[Extract retry_after]
        E --> F[Sleep retry_after seconds]
        F --> A
    end

    subgraph LLM API Errors
        G[API Request] --> H{Error?}
        H -->|No| I[Process Response]
        H -->|Connection Error| J[Log Error]
        H -->|Auth Error| K[Mark Bot Not Ready]
        H -->|Timeout| L[Continue with Partial]
    end

    subgraph Config Loading
        M[Load Config] --> N{Valid YAML?}
        N -->|Yes| O[Return Config Dict]
        N -->|No| P[Catch YAMLError]
        P --> Q[Print Exception]
        Q --> R[Return None]
        R --> S[Exit Application]
    end

    style C fill:#c8e6c9
    style I fill:#c8e6c9
    style O fill:#c8e6c9
    style S fill:#ffebee
```

---

## Concurrency Model

```mermaid
graph TB
    subgraph Main Thread
        A[Main Process]
        B[Argument Parsing]
        C[Config Loading]
        D[Object Initialization]
    end

    subgraph Async Event Loop
        E[asyncio.new_event_loop]
        F[Discord Client Task]
        G[FastAPI Server Task]
    end

    subgraph Discord Events
        H[on_connect - async]
        I[on_ready - async]
        J[on_message - async]
        K[on_error - async]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    E --> G

    F --> H
    F --> I
    F --> J
    F --> K

    J --> L[bot.chat_completion<br/>Synchronous Call]
    L --> M[LLM API Stream<br/>Synchronous Iteration]
    M --> N[Return Response]
    N --> J

    style E fill:#e3f2fd
    style F fill:#fff4e1
    style G fill:#f3e5f5
    style L fill:#ffccbc
```

**Key Points**:
- **Event Loop**: Single async event loop runs both Discord client and FastAPI
- **Discord Handlers**: All event handlers are `async` functions
- **Bot Methods**: `chat_completion()` is synchronous (blocking)
- **LLM Streaming**: Synchronous iteration over response chunks
- **Concurrency**: Multiple users can interact, but each conversation is processed sequentially

---

This document provides comprehensive technical diagrams for understanding AmiBot's architecture, data flows, and operational patterns.
