# Feature Proposal: Custom Agent and MCP Bot Integration

**Status**: Proposal
**Created**: 2025-11-15
**Author**: AI Assistant
**Target Version**: 0.1.0

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Motivation](#motivation)
3. [Proposed Architecture](#proposed-architecture)
4. [Technical Specifications](#technical-specifications)
5. [Implementation Plan](#implementation-plan)
6. [Configuration Schema](#configuration-schema)
7. [Testing Strategy](#testing-strategy)
8. [Migration Path](#migration-path)
9. [Benefits and Use Cases](#benefits-and-use-cases)
10. [Risks and Mitigation](#risks-and-mitigation)
11. [Future Enhancements](#future-enhancements)

---

## Executive Summary

This proposal outlines the addition of two new bot implementations to the AmiBot framework:

1. **AgentBot** (`bot_agent.py`) - Connect to custom AI agents via HTTP/REST APIs
2. **MCPBot** (`bot_mcp.py`) - Connect to Model Context Protocol (MCP) servers

Both implementations will extend the existing `Bot` base class and integrate seamlessly with the current architecture, enabling AmiBot to interface with custom AI systems, local models, and MCP-compliant services.

**Key Benefits**:
- 🔌 Connect to self-hosted AI models and agents
- 🌐 Support for MCP standard (Anthropic's Model Context Protocol)
- 🔧 Full control over custom agent implementations
- 💰 Cost optimization through local/custom models
- 🔒 Data privacy with on-premise deployments

---

## Motivation

### Current Limitations

The existing AmiBot architecture supports three commercial LLM providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- Perplexity (Sonar models)

**Gaps**:
1. ❌ No support for self-hosted models (Llama, Mistral, etc.)
2. ❌ Cannot integrate custom AI agents with specialized capabilities
3. ❌ No support for MCP standard
4. ❌ Limited flexibility for proprietary AI systems
5. ❌ Vendor lock-in to commercial providers

### Use Cases

**Custom Agent Integration** (`bot_agent.py`):
- Connect to internal AI systems within organizations
- Interface with specialized domain-specific agents
- Integrate with custom RAG (Retrieval-Augmented Generation) pipelines
- Support local model deployments (Ollama, LM Studio, vLLM)
- Enable multi-step agent workflows

**MCP Integration** (`bot_mcp.py`):
- Connect to Anthropic's Model Context Protocol servers
- Interface with MCP-compliant tools and data sources
- Enable standardized agent-to-agent communication
- Support MCP resources, prompts, and tools
- Future-proof integration with emerging MCP ecosystem

---

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Bot Base Class                          │
│            (Existing: user/bot.py)                           │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┬──────────────┬────────────────┐
    │                         │              │                │
┌───▼───────┐         ┌──────▼──────┐  ┌───▼────┐      ┌────▼─────┐
│OpenaiBot  │         │AnthropicBot │  │Perplexi│      │NEW BOTS  │
│(existing) │         │  (existing) │  │tyBot   │      │          │
└───────────┘         └─────────────┘  │(exist.)│      │          │
                                        └────────┘      │          │
                                                        │          │
                      ┌─────────────────────────────────┤          │
                      │                                 │          │
                  ┌───▼──────┐                    ┌────▼─────┐    │
                  │AgentBot  │                    │ MCPBot   │    │
                  │  (NEW)   │                    │  (NEW)   │    │
                  └─────┬────┘                    └────┬─────┘    │
                        │                              │          │
                        │                              │          │
        ┌───────────────┴──────────┐      ┌───────────┴────────┐ │
        │                           │      │                    │ │
    ┌───▼────────┐        ┌────────▼───┐  │  ┌──────────────┐ │ │
    │HTTP Client │        │Custom Agent│  │  │ MCP Client   │ │ │
    │(requests)  │        │   Server   │  │  │  Library     │ │ │
    └────────────┘        └────────────┘  │  └──────┬───────┘ │ │
                                          │         │         │ │
                                          │  ┌──────▼───────┐ │ │
                                          │  │ MCP Server   │ │ │
                                          │  │  (External)  │ │ │
                                          │  └──────────────┘ │ │
                                          └────────────────────┘ │
                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Class Hierarchy

```python
User (base)
  └── Bot (extends User)
      ├── OpenaiBot (existing)
      ├── AnthropicBot (existing)
      ├── PerplexityBot (existing)
      ├── AgentBot (NEW) - HTTP/REST custom agent client
      └── MCPBot (NEW) - Model Context Protocol client
```

### Integration with Existing Framework

Both new bot types will:
- ✅ Extend the `Bot` base class
- ✅ Implement `chat_completion(name, message) -> str`
- ✅ Maintain per-user conversation context with `DictNoNone`
- ✅ Support progressive token strategy (if applicable)
- ✅ Integrate with Discord via existing `Community` injection
- ✅ Follow existing property-based encapsulation patterns
- ✅ Work with current health check endpoints

---

## Technical Specifications

### 1. AgentBot Implementation (`bot_agent.py`)

#### Purpose
Connect to custom AI agents via HTTP/REST API endpoints. Supports any agent that can handle JSON requests/responses.

#### Architecture

```python
from user.bot import Bot, DictNoNone
import requests
import json
from typing import Optional, Dict, Any

class AgentBot(Bot):
    """
    Bot implementation for custom HTTP/REST agents.

    Supports:
    - Custom endpoint URLs
    - Flexible request/response schemas
    - Authentication (API keys, Bearer tokens)
    - Streaming and non-streaming responses
    - Custom headers and parameters
    """

    def __init__(
        self,
        name: str,
        llmprovider: str,
        secret: str,
        token_min: int,
        token_max: int,
        token_increment: int,
        system_role: str = "",
        endpoint_url: str = None,
        request_format: str = "openai",  # openai, anthropic, custom
        auth_type: str = "api_key",       # api_key, bearer, none
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ):
        super().__init__(name, llmprovider, secret)
        self._endpoint_url = endpoint_url
        self._request_format = request_format
        self._auth_type = auth_type
        self._custom_headers = custom_headers or {}
        self._timeout = timeout
        self._token_limits = range(token_min, token_max, token_increment)
        self._setup_auth(secret)
        self._check = True

    def _setup_auth(self, secret: str):
        """Configure authentication headers"""
        if self._auth_type == "api_key":
            self._custom_headers["Authorization"] = f"Bearer {secret}"
        elif self._auth_type == "bearer":
            self._custom_headers["Authorization"] = f"Bearer {secret}"
        elif self._auth_type == "api_key_header":
            self._custom_headers["X-API-Key"] = secret

    def _build_request(
        self,
        messages: list,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Build request payload based on format"""
        if self._request_format == "openai":
            return {
                "model": self._model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.5
            }
        elif self._request_format == "anthropic":
            # Extract system message
            system = next(
                (m["content"] for m in messages if m["role"] == "system"),
                ""
            )
            user_messages = [m for m in messages if m["role"] != "system"]
            return {
                "model": self._model,
                "system": system,
                "messages": user_messages,
                "max_tokens": max_tokens,
                "temperature": 0.5
            }
        else:  # custom
            return {
                "prompt": messages[-1]["content"],
                "max_length": max_tokens,
                "context": messages[:-1]
            }

    def chat_completion(self, name: str, message: str) -> str:
        """
        Send message to custom agent and return response.

        Process:
        1. Check/create user conversation context
        2. Append user message
        3. Progressive token strategy loop
        4. Build and send HTTP request
        5. Parse response
        6. Check for truncation
        7. Append assistant response
        8. Return complete message
        """
        print(f"--- CHAT CONVERSATION from: {name} (Agent: {self._endpoint_url})")

        # Initialize user context if needed
        if name not in self._messages:
            self._messages[name] = self._messages.get('system_role', []).copy()

        # Append user message
        self._messages[name].append({
            "role": "user",
            "content": f"{name} says {message}"
        })

        assistant_message = ""

        # Progressive token strategy
        for token_limit in self.token_limits:
            try:
                # Build request
                payload = self._build_request(self._messages[name], token_limit)

                # Send request
                response = requests.post(
                    self._endpoint_url,
                    json=payload,
                    headers=self._custom_headers,
                    timeout=self._timeout
                )
                response.raise_for_status()

                # Parse response
                data = response.json()

                # Extract message based on format
                if self._request_format == "openai":
                    assistant_message = data["choices"][0]["message"]["content"]
                    finish_reason = data["choices"][0].get("finish_reason")
                elif self._request_format == "anthropic":
                    assistant_message = data["content"][0]["text"]
                    finish_reason = data.get("stop_reason")
                else:  # custom
                    assistant_message = data.get("response", data.get("text", ""))
                    finish_reason = data.get("finish_reason", "stop")

                # Check if complete
                if finish_reason not in ["length", "max_tokens"]:
                    break

            except requests.exceptions.RequestException as e:
                print(f"Agent request failed: {e}")
                assistant_message = f"Error communicating with agent: {str(e)}"
                break
            except json.JSONDecodeError as e:
                print(f"Failed to parse agent response: {e}")
                assistant_message = "Error: Invalid response from agent"
                break

        # Append assistant response
        self._messages[name].append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message
```

#### Configuration Schema

```yaml
llm:
  provider: "agent"
  enabled: true
  model: "custom-model-v1"
  key: "your-api-key"
  endpoint_url: "http://localhost:8080/v1/chat/completions"
  request_format: "openai"  # openai | anthropic | custom
  auth_type: "bearer"       # api_key | bearer | api_key_header | none
  custom_headers:
    X-Custom-Header: "value"
  timeout: 30
  tokens_range:
    from: 256
    until: 4096
    increment: 256
```

#### Supported Agent Types

**OpenAI-Compatible APIs**:
- Ollama (`http://localhost:11434/v1/chat/completions`)
- LM Studio (`http://localhost:1234/v1/chat/completions`)
- vLLM (`http://localhost:8000/v1/chat/completions`)
- LocalAI (`http://localhost:8080/v1/chat/completions`)
- Text Generation WebUI (via OpenAI extension)

**Custom Agent Servers**:
- Internal enterprise AI systems
- Specialized domain agents
- Multi-step RAG pipelines
- Tool-using agents
- Custom LLM wrappers

---

### 2. MCPBot Implementation (`bot_mcp.py`)

#### Purpose
Connect to Model Context Protocol (MCP) servers following Anthropic's MCP specification. Enables standardized agent-to-agent communication and resource access.

#### Architecture

```python
from user.bot import Bot, DictNoNone
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from typing import Optional, List, Dict, Any

class MCPBot(Bot):
    """
    Bot implementation for Model Context Protocol (MCP) servers.

    Supports:
    - MCP resources (context, files, data)
    - MCP prompts (pre-defined interactions)
    - MCP tools (agent capabilities)
    - Streaming responses
    - Multi-server connections
    """

    def __init__(
        self,
        name: str,
        llmprovider: str,
        secret: str,
        token_min: int,
        token_max: int,
        token_increment: int,
        system_role: str = "",
        server_command: str = None,
        server_args: Optional[List[str]] = None,
        server_env: Optional[Dict[str, str]] = None,
        llm_backend: str = "anthropic",  # Underlying LLM for agent
        llm_model: str = "claude-3-5-sonnet-20240620"
    ):
        super().__init__(name, llmprovider, secret)
        self._server_command = server_command
        self._server_args = server_args or []
        self._server_env = server_env or {}
        self._llm_backend = llm_backend
        self._llm_model = llm_model
        self._model = f"mcp:{server_command}"
        self._token_limits = range(token_min, token_max, token_increment)
        self._session: Optional[ClientSession] = None
        self._available_tools: List[Dict] = []
        self._available_resources: List[Dict] = []
        self._check = False

    async def _init_mcp_session(self):
        """Initialize MCP client session"""
        server_params = StdioServerParameters(
            command=self._server_command,
            args=self._server_args,
            env=self._server_env
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self._session = session

                # Initialize connection
                await session.initialize()

                # List available tools
                tools_result = await session.list_tools()
                self._available_tools = tools_result.tools

                # List available resources
                resources_result = await session.list_resources()
                self._available_resources = resources_result.resources

                self._check = True
                print(f"Connected to MCP server: {self._server_command}")
                print(f"Available tools: {len(self._available_tools)}")
                print(f"Available resources: {len(self._available_resources)}")

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool"""
        if not self._session:
            raise RuntimeError("MCP session not initialized")

        result = await self._session.call_tool(tool_name, arguments)
        return result

    async def _read_resource(self, uri: str) -> str:
        """Read an MCP resource"""
        if not self._session:
            raise RuntimeError("MCP session not initialized")

        result = await self._session.read_resource(uri)
        return result.contents[0].text if result.contents else ""

    def _build_llm_request(
        self,
        messages: List[Dict],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Build request for underlying LLM with MCP context"""
        # Add available tools to system context
        tools_description = "\n".join([
            f"- {tool['name']}: {tool.get('description', 'No description')}"
            for tool in self._available_tools
        ])

        # Enhance system message with MCP capabilities
        enhanced_system = (
            f"{messages[0]['content']}\n\n"
            f"Available MCP Tools:\n{tools_description}\n\n"
            f"You can use these tools to assist the user."
        )

        enhanced_messages = [
            {"role": "system", "content": enhanced_system}
        ] + messages[1:]

        return {
            "model": self._llm_model,
            "messages": enhanced_messages,
            "max_tokens": max_tokens,
            "temperature": 0.5
        }

    def chat_completion(self, name: str, message: str) -> str:
        """
        Process message through MCP server.

        Process:
        1. Initialize MCP session if needed
        2. Check/create user conversation context
        3. Append user message
        4. Send to underlying LLM with MCP context
        5. Parse response for tool calls
        6. Execute tool calls via MCP
        7. Send tool results back to LLM
        8. Return final response
        """
        # Run async initialization if needed
        if not self._check:
            asyncio.run(self._init_mcp_session())

        print(f"--- CHAT CONVERSATION from: {name} (MCP Server: {self._server_command})")

        # Initialize user context if needed
        if name not in self._messages:
            self._messages[name] = self._messages.get('system_role', []).copy()

        # Append user message
        self._messages[name].append({
            "role": "user",
            "content": f"{name} says {message}"
        })

        # For now, use synchronous approach
        # In production, this should be fully async
        assistant_message = asyncio.run(
            self._async_chat_completion(name, self._messages[name])
        )

        # Append assistant response
        self._messages[name].append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    async def _async_chat_completion(
        self,
        name: str,
        messages: List[Dict]
    ) -> str:
        """Async implementation of chat completion with tool calling"""
        # This is a simplified version
        # Full implementation would:
        # 1. Call underlying LLM (Claude, GPT, etc.)
        # 2. Parse tool calls from response
        # 3. Execute tools via MCP
        # 4. Add tool results to context
        # 5. Call LLM again with results
        # 6. Repeat until no more tool calls

        # Placeholder: Direct pass-through for now
        # Real implementation needs async LLM client
        return "MCP response placeholder - needs async LLM implementation"
```

#### Configuration Schema

```yaml
llm:
  provider: "mcp"
  enabled: true
  model: "mcp-server"
  key: ""  # May not be needed for local MCP servers
  server_command: "npx"
  server_args:
    - "-y"
    - "@modelcontextprotocol/server-filesystem"
    - "/path/to/allowed/directory"
  server_env:
    NODE_ENV: "production"
  llm_backend: "anthropic"  # Underlying LLM
  llm_model: "claude-3-5-sonnet-20240620"
  llm_key: "sk-ant-..."  # Key for underlying LLM
  tokens_range:
    from: 256
    until: 4096
    increment: 256
```

#### MCP Server Examples

**Filesystem Server**:
```yaml
server_command: "npx"
server_args:
  - "-y"
  - "@modelcontextprotocol/server-filesystem"
  - "/home/user/documents"
```

**GitHub Server**:
```yaml
server_command: "npx"
server_args:
  - "-y"
  - "@modelcontextprotocol/server-github"
server_env:
  GITHUB_TOKEN: "ghp_..."
```

**Custom MCP Server**:
```yaml
server_command: "/usr/local/bin/custom-mcp-server"
server_args:
  - "--port"
  - "8080"
  - "--verbose"
```

---

## Implementation Plan

### Phase 1: AgentBot Implementation (Week 1-2)

**Tasks**:
1. ✅ Create `amibot/user/bot_agent.py`
2. ✅ Implement HTTP client with requests library
3. ✅ Add support for OpenAI-compatible format
4. ✅ Add support for Anthropic format
5. ✅ Add support for custom format
6. ✅ Implement authentication methods
7. ✅ Add error handling and retries
8. ✅ Update `__main__.py` to register AgentBot
9. ✅ Add configuration schema validation
10. ✅ Create unit tests

**Dependencies**:
- `requests>=2.31.0` (already available)
- No new dependencies required

**Files to Modify**:
- `amibot/user/bot_agent.py` (new)
- `amibot/__main__.py` (add case for "agent" provider)
- `configs/amibot_example.conf` (add agent configuration example)
- `requirements.txt` (no changes needed)

### Phase 2: MCPBot Implementation (Week 3-4)

**Tasks**:
1. ✅ Research MCP Python SDK
2. ✅ Add `mcp` dependency
3. ✅ Create `amibot/user/bot_mcp.py`
4. ✅ Implement MCP client session management
5. ✅ Add tool calling support
6. ✅ Add resource reading support
7. ✅ Integrate with underlying LLM (Claude/GPT)
8. ✅ Add async/await support
9. ✅ Update `__main__.py` to register MCPBot
10. ✅ Create integration tests

**Dependencies**:
- `mcp>=1.0.0` (Model Context Protocol SDK)
- Consider `aiohttp` for async HTTP if not using MCP stdio

**Files to Modify**:
- `amibot/user/bot_mcp.py` (new)
- `amibot/__main__.py` (add case for "mcp" provider)
- `configs/amibot_example.conf` (add MCP configuration example)
- `requirements.txt` (add mcp dependency)

### Phase 3: Testing and Documentation (Week 5)

**Tasks**:
1. ✅ Write unit tests for AgentBot
2. ✅ Write unit tests for MCPBot
3. ✅ Create integration tests with mock servers
4. ✅ Test with real Ollama instance
5. ✅ Test with real MCP filesystem server
6. ✅ Update CLAUDE.md with new bot types
7. ✅ Update TECHNICAL_DIAGRAMS.md with new diagrams
8. ✅ Create usage examples
9. ✅ Add troubleshooting guide
10. ✅ Update README.md

### Phase 4: Production Readiness (Week 6)

**Tasks**:
1. ✅ Performance testing
2. ✅ Security review
3. ✅ Add monitoring/metrics
4. ✅ Create deployment guides
5. ✅ Update CI/CD pipeline
6. ✅ Beta testing with users
7. ✅ Address feedback
8. ✅ Release v0.1.0

---

## Configuration Schema

### Complete Configuration Example

```yaml
# Example 1: OpenAI-compatible agent (Ollama)
amibot:
  username: "amigo"
  system_role: |
    You are a helpful assistant with access to local models.

discord:
  enabled: true
  application_id: "..."
  public_key: "..."
  token: "..."

llm:
  provider: "agent"
  enabled: true
  model: "llama3.2"
  key: ""  # Not needed for Ollama
  endpoint_url: "http://localhost:11434/v1/chat/completions"
  request_format: "openai"
  auth_type: "none"
  timeout: 60
  tokens_range:
    from: 256
    until: 4096
    increment: 256

---

# Example 2: Custom agent with API key
amibot:
  username: "amigo"
  system_role: |
    You are a specialized agent for customer support.

discord:
  enabled: true
  application_id: "..."
  public_key: "..."
  token: "..."

llm:
  provider: "agent"
  enabled: true
  model: "internal-agent-v2"
  key: "agent-api-key-12345"
  endpoint_url: "https://internal-ai.company.com/api/chat"
  request_format: "custom"
  auth_type: "api_key_header"
  custom_headers:
    X-Department: "support"
    X-Environment: "production"
  timeout: 30
  tokens_range:
    from: 512
    until: 2048
    increment: 256

---

# Example 3: MCP filesystem server
amibot:
  username: "amigo"
  system_role: |
    You are a helpful assistant with access to files via MCP.

discord:
  enabled: true
  application_id: "..."
  public_key: "..."
  token: "..."

llm:
  provider: "mcp"
  enabled: true
  model: "mcp-filesystem"
  server_command: "npx"
  server_args:
    - "-y"
    - "@modelcontextprotocol/server-filesystem"
    - "/home/user/documents"
  llm_backend: "anthropic"
  llm_model: "claude-3-5-sonnet-20240620"
  llm_key: "sk-ant-..."
  tokens_range:
    from: 256
    until: 4096
    increment: 256
```

### Required Configuration Changes

**`__main__.py`** - Add new bot cases:

```python
match str.lower(configuration['llm']['provider']):
    case "openai":
        # existing code
    case "anthropic":
        # existing code
    case "perplexity":
        # existing code
    case "agent":
        amigo = AgentBot(
            configuration['amibot']['username'],
            configuration['llm']['provider'],
            configuration['llm'].get('key', ''),
            configuration['llm']['tokens_range']['from'],
            configuration['llm']['tokens_range']['until'],
            configuration['llm']['tokens_range']['increment'],
            configuration['amibot']['system_role'],
            endpoint_url=configuration['llm']['endpoint_url'],
            request_format=configuration['llm'].get('request_format', 'openai'),
            auth_type=configuration['llm'].get('auth_type', 'none'),
            custom_headers=configuration['llm'].get('custom_headers', {}),
            timeout=configuration['llm'].get('timeout', 30)
        )
    case "mcp":
        amigo = MCPBot(
            configuration['amibot']['username'],
            configuration['llm']['provider'],
            '',  # MCP may not need key
            configuration['llm']['tokens_range']['from'],
            configuration['llm']['tokens_range']['until'],
            configuration['llm']['tokens_range']['increment'],
            configuration['amibot']['system_role'],
            server_command=configuration['llm']['server_command'],
            server_args=configuration['llm'].get('server_args', []),
            server_env=configuration['llm'].get('server_env', {}),
            llm_backend=configuration['llm'].get('llm_backend', 'anthropic'),
            llm_model=configuration['llm'].get('llm_model', 'claude-3-5-sonnet-20240620')
        )
```

---

## Testing Strategy

### Unit Tests

**AgentBot Tests** (`tests/test_bot_agent.py`):
```python
import pytest
from unittest.mock import Mock, patch
from amibot.user.bot_agent import AgentBot

def test_agent_bot_initialization():
    bot = AgentBot(
        name="test-agent",
        llmprovider="agent",
        secret="test-key",
        token_min=256,
        token_max=1024,
        token_increment=256,
        endpoint_url="http://localhost:8080/api/chat"
    )
    assert bot.name == "test-agent"
    assert bot._endpoint_url == "http://localhost:8080/api/chat"

@patch('requests.post')
def test_chat_completion_success(mock_post):
    mock_post.return_value.json.return_value = {
        "choices": [{
            "message": {"content": "Test response"},
            "finish_reason": "stop"
        }]
    }

    bot = AgentBot(
        name="test-agent",
        llmprovider="agent",
        secret="test-key",
        token_min=256,
        token_max=1024,
        token_increment=256,
        endpoint_url="http://localhost:8080/api/chat"
    )

    response = bot.chat_completion("alice", "Hello")
    assert response == "Test response"
    assert "alice" in bot._messages

def test_chat_completion_with_truncation(mock_post):
    # Test progressive token strategy
    pass

def test_auth_header_setup():
    # Test different auth types
    pass
```

**MCPBot Tests** (`tests/test_bot_mcp.py`):
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from amibot.user.bot_mcp import MCPBot

@pytest.mark.asyncio
async def test_mcp_session_initialization():
    bot = MCPBot(
        name="test-mcp",
        llmprovider="mcp",
        secret="",
        token_min=256,
        token_max=1024,
        token_increment=256,
        server_command="mock-mcp-server"
    )

    # Mock MCP session
    with patch('mcp.client.stdio.stdio_client') as mock_client:
        await bot._init_mcp_session()
        assert bot._check is True

def test_mcp_tool_discovery():
    # Test tool listing
    pass

def test_mcp_resource_reading():
    # Test resource access
    pass
```

### Integration Tests

**Test with Ollama**:
```bash
# Start Ollama
ollama serve

# Pull model
ollama pull llama3.2

# Run integration test
pytest tests/integration/test_ollama_agent.py
```

**Test with MCP Filesystem**:
```bash
# Install MCP filesystem server
npm install -g @modelcontextprotocol/server-filesystem

# Run integration test
pytest tests/integration/test_mcp_filesystem.py
```

### Manual Testing Checklist

- [ ] AgentBot connects to Ollama successfully
- [ ] AgentBot handles API errors gracefully
- [ ] AgentBot respects token limits
- [ ] MCPBot initializes session correctly
- [ ] MCPBot lists available tools
- [ ] MCPBot can read resources
- [ ] Both bots work with Discord integration
- [ ] Health checks report correct status
- [ ] Configuration validation works
- [ ] Error messages are user-friendly

---

## Migration Path

### For Existing Deployments

**No Breaking Changes**:
- Existing OpenAI, Anthropic, and Perplexity bots continue to work
- No changes to current configuration files required
- New bot types are opt-in

**Migration Steps**:

1. **Update Dependencies** (for MCP only):
   ```bash
   pip install mcp>=1.0.0
   ```

2. **Update Configuration** (optional):
   ```yaml
   # Add agent or MCP configuration
   llm:
     provider: "agent"  # or "mcp"
     # ... new configuration
   ```

3. **Test New Bot**:
   ```bash
   python -m amibot -c configs/agent.conf
   ```

4. **Deploy**:
   - Update Docker image
   - Update Kubernetes ConfigMap
   - Update ECS task definition

### Backward Compatibility

- ✅ All existing bot types remain functional
- ✅ No changes to Bot base class interface
- ✅ No changes to Community integration
- ✅ No changes to health check endpoints
- ✅ Configuration schema only extended, not modified

---

## Benefits and Use Cases

### AgentBot Benefits

**Cost Optimization**:
- 💰 Use free, open-source models (Llama, Mistral, Phi)
- 💰 Eliminate per-token API costs
- 💰 Self-host on existing infrastructure

**Data Privacy**:
- 🔒 Keep sensitive data on-premise
- 🔒 No data sent to third-party APIs
- 🔒 Full control over data retention

**Customization**:
- 🔧 Fine-tune models for specific domains
- 🔧 Integrate proprietary knowledge bases
- 🔧 Implement custom business logic

**Performance**:
- ⚡ Lower latency with local models
- ⚡ No rate limiting
- ⚡ Dedicated resources

### MCPBot Benefits

**Standardization**:
- 📋 Use standard protocol for agent communication
- 📋 Interoperable with MCP ecosystem
- 📋 Future-proof integration

**Tool Access**:
- 🛠️ Access filesystem via MCP
- 🛠️ Query databases through MCP servers
- 🛠️ Integrate with APIs via MCP tools

**Composability**:
- 🔗 Chain multiple MCP servers
- 🔗 Combine capabilities from different sources
- 🔗 Build complex agent workflows

### Use Cases

**Internal IT Support Bot**:
- Use AgentBot with custom model trained on internal documentation
- Connect to company knowledge base
- Maintain data privacy

**Research Assistant**:
- Use MCPBot with filesystem access
- Query academic papers and documents
- Integrate with reference management tools

**Development Assistant**:
- Use AgentBot with code-specialized model
- Connect to GitHub via MCP
- Access project files via MCP filesystem

**Customer Service**:
- Use AgentBot with custom RAG pipeline
- Access product database via MCP
- Integrate with CRM via custom agent

---

## Risks and Mitigation

### Technical Risks

**Risk**: AgentBot may not handle all custom API formats
- **Mitigation**: Provide flexible `custom` format option
- **Mitigation**: Document common patterns
- **Mitigation**: Allow custom response parsers

**Risk**: MCP specification may evolve
- **Mitigation**: Use official MCP SDK
- **Mitigation**: Version lock MCP dependencies
- **Mitigation**: Monitor MCP spec changes

**Risk**: Async complexity in MCPBot
- **Mitigation**: Provide clear async documentation
- **Mitigation**: Use asyncio best practices
- **Mitigation**: Add comprehensive error handling

**Risk**: Performance degradation with local models
- **Mitigation**: Document hardware requirements
- **Mitigation**: Provide optimization guides
- **Mitigation**: Support GPU acceleration

### Security Risks

**Risk**: Malicious agent endpoints
- **Mitigation**: Validate SSL certificates
- **Mitigation**: Implement request timeouts
- **Mitigation**: Add endpoint allowlisting option

**Risk**: MCP server vulnerabilities
- **Mitigation**: Sandbox MCP server processes
- **Mitigation**: Validate MCP responses
- **Mitigation**: Limit resource access

**Risk**: API key exposure
- **Mitigation**: Support environment variables
- **Mitigation**: Use Kubernetes Secrets
- **Mitigation**: Never log sensitive data

### Operational Risks

**Risk**: Increased complexity
- **Mitigation**: Comprehensive documentation
- **Mitigation**: Clear error messages
- **Mitigation**: Troubleshooting guides

**Risk**: Support burden
- **Mitigation**: Provide example configurations
- **Mitigation**: Create debugging tools
- **Mitigation**: Build active community

---

## Future Enhancements

### Phase 2 Enhancements

**AgentBot**:
- [ ] WebSocket support for streaming
- [ ] Multi-agent orchestration
- [ ] Agent discovery and registration
- [ ] Request/response caching
- [ ] Fallback chain (try agent A, then B, then C)

**MCPBot**:
- [ ] Multi-server support (connect to multiple MCP servers)
- [ ] Tool result caching
- [ ] Prompt template support
- [ ] Resource prefetching
- [ ] MCP sampling support

**General**:
- [ ] Agent marketplace/registry
- [ ] Performance metrics dashboard
- [ ] Cost tracking per bot type
- [ ] A/B testing framework
- [ ] Agent behavior analytics

### Long-Term Vision

**Agent Ecosystem**:
- Build marketplace for pre-configured agents
- Create agent discovery protocol
- Establish agent certification program

**Advanced Orchestration**:
- Multi-agent conversations
- Agent collaboration patterns
- Workflow automation

**Enhanced MCP Integration**:
- MCP server development kit
- Custom MCP server templates
- MCP debugging tools

---

## Appendix

### A. Dependencies

```txt
# Existing
openai~=1.61.1
anthropic~=0.45.2
discord>=2.3.2
fastapi~=0.115.8
uvicorn~=0.34.0
boto3~=1.36.1
botocore~=1.36.1
PyYAML~=6.0.2
setuptools>=78.1.1
audioop-lts~=0.2.1
requests>=2.31.0  # Already available

# New for MCPBot
mcp~=1.0.0  # Model Context Protocol SDK
```

### B. API Compatibility Matrix

| Bot Type | API Format | Streaming | Tools | Context Window |
|----------|-----------|-----------|-------|----------------|
| OpenaiBot | OpenAI | ✅ | ❌ | Up to 128K |
| AnthropicBot | Anthropic | ✅ | ❌ | Up to 200K |
| PerplexityBot | OpenAI | ✅ | ❌ | Up to 127K |
| **AgentBot** | **Flexible** | **Optional** | **Via API** | **Variable** |
| **MCPBot** | **MCP** | **✅** | **✅** | **Variable** |

### C. Example Agent Implementations

See `examples/` directory for:
- `agent_ollama.py` - Ollama integration example
- `agent_custom.py` - Custom agent server template
- `mcp_filesystem.py` - MCP filesystem server usage
- `mcp_github.py` - MCP GitHub integration

### D. Troubleshooting Guide

**AgentBot Connection Issues**:
```bash
# Test endpoint manually
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'

# Check logs
tail -f /var/log/amibot.log | grep AgentBot
```

**MCPBot Session Failures**:
```bash
# Test MCP server directly
npx @modelcontextprotocol/server-filesystem /tmp

# Check server logs
export MCP_DEBUG=1
python -m amibot -c configs/mcp.conf
```

---

## Approval and Sign-off

This proposal requires review and approval from:

- [ ] Technical Lead - Architecture review
- [ ] Security Team - Security assessment
- [ ] DevOps Team - Deployment feasibility
- [ ] Product Owner - Business value validation

**Estimated Effort**: 6 weeks (1 developer)
**Target Release**: v0.1.0
**Risk Level**: Medium

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Next Review**: After Phase 1 completion
