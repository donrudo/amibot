# Feature Proposal: Multi-Platform Community Integration (Slack & Signal)

**Status**: Proposal
**Created**: 2025-11-15
**Author**: AI Assistant
**Target Version**: 0.2.0

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

This proposal outlines the addition of two new community platform integrations to the AmiBot framework:

1. **Slack** (`slack_client.py`) - Enterprise team collaboration platform
2. **Signal** (`signal_client.py`) - Privacy-focused encrypted messaging

Both implementations will extend the existing `Community` base class and integrate seamlessly with the current architecture, enabling AmiBot to serve users across multiple communication platforms simultaneously or independently.

**Key Benefits**:
- 💼 Enterprise adoption through Slack integration
- 🔒 Privacy-conscious deployment via Signal
- 🌐 Multi-platform presence from single bot instance
- 🔧 Platform-agnostic bot implementations
- 📊 Broader user reach and accessibility

---

## Motivation

### Current Limitations

The existing AmiBot architecture supports only one community platform:
- Discord (chat/gaming communities)

**Gaps**:
1. ❌ No enterprise workspace integration (Slack, Microsoft Teams)
2. ❌ No privacy-focused messaging platforms (Signal, Matrix)
3. ❌ Cannot serve multiple communities simultaneously
4. ❌ Limited to Discord's user base and use cases
5. ❌ No support for encrypted/secure messaging

### Use Cases

**Slack Integration** (`slack_client.py`):
- Deploy AI assistants in enterprise workspaces
- Integrate with business workflows and tools
- Serve internal teams and departments
- Support Slack threads and channels
- Enable workspace-specific customization
- Integrate with Slack's app directory

**Signal Integration** (`signal_client.py`):
- Privacy-first AI assistant deployment
- End-to-end encrypted conversations
- Personal/small group use cases
- Security-conscious organizations
- Journalist/activist support
- Healthcare/legal compliance scenarios

---

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                   Community Base Class                       │
│              (Existing: community/__init__.py)               │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┬──────────────┬────────────────┐
    │                         │              │                │
┌───▼───────┐         ┌──────▼──────┐  ┌───▼────┐      ┌────▼─────┐
│Discord    │         │  Slack      │  │ Signal │      │ FUTURE   │
│(existing) │         │   (NEW)     │  │ (NEW)  │      │ Telegram │
└─────┬─────┘         └──────┬──────┘  └───┬────┘      │ Matrix   │
      │                      │             │           │ WhatsApp │
      │                      │             │           └──────────┘
 ┌────▼────┐           ┌─────▼────┐  ┌────▼────┐
 │discord  │           │slack_bolt│  │signal   │
 │  .py    │           │  SDK     │  │ -cli    │
 └─────────┘           └──────────┘  └─────────┘
```

### Class Hierarchy

```python
Community (base)
  ├── Discord (existing) - Discord.py client
  ├── Slack (NEW) - Slack Bolt framework
  └── Signal (NEW) - signal-cli wrapper
```

### Integration with Existing Framework

All new community types will:
- ✅ Extend the `Community` base class
- ✅ Implement `start()` and `stop()` async methods
- ✅ Provide `is_ready()` status check
- ✅ Accept injected Bot instance via `bot` property
- ✅ Handle message routing to `bot.chat_completion()`
- ✅ Manage platform-specific authentication
- ✅ Support message chunking and formatting
- ✅ Work with existing health check endpoints

---

## Technical Specifications

### 1. Slack Integration (`slack_client.py`)

#### Purpose
Connect AmiBot to Slack workspaces using the Slack Bolt framework. Supports app mentions, direct messages, and threaded conversations.

#### Architecture

```python
from community import Community
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import asyncio
import re
from typing import Optional

class Slack(Community):
    """
    Slack integration using Bolt framework with Socket Mode.

    Features:
    - App mentions (@bot_name)
    - Direct messages
    - Threaded conversations
    - Rich message formatting
    - Reaction handling
    - File attachments (read-only)
    """

    def __init__(
        self,
        bot_token: str,
        app_token: str,
        signing_secret: Optional[str] = None
    ):
        super().__init__("Slack", bot_token)
        self._app_token = app_token
        self._signing_secret = signing_secret
        self._check = False
        self._handler = None

        # Initialize Slack Bolt app
        self.app = AsyncApp(
            token=bot_token,
            signing_secret=signing_secret
        )

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register Slack event handlers"""

        @self.app.event("app_mention")
        async def handle_mention(event, say, client):
            """Handle @mentions of the bot"""
            await self._handle_message(event, say, client, is_mention=True)

        @self.app.event("message")
        async def handle_message(event, say, client):
            """Handle direct messages"""
            # Only respond to DMs, not all messages
            if event.get("channel_type") == "im":
                await self._handle_message(event, say, client, is_mention=False)

        @self.app.event("app_home_opened")
        async def handle_app_home(event, client):
            """Handle App Home tab opened"""
            user_id = event["user"]
            await client.views_publish(
                user_id=user_id,
                view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Welcome to {self._bot.name}!* :wave:\n\n"
                                        "I'm an AI assistant powered by advanced language models.\n\n"
                                        "*How to interact with me:*\n"
                                        "• Mention me with `@{bot_name}` in any channel\n"
                                        "• Send me a direct message\n"
                                        "• Reply in a thread where I'm active"
                            }
                        }
                    ]
                }
            )

    async def _handle_message(
        self,
        event: dict,
        say,
        client,
        is_mention: bool = False
    ):
        """Process incoming message and send response"""

        # Extract message details
        user_id = event.get("user")
        text = event.get("text", "")
        channel = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")

        # Ignore bot's own messages
        if event.get("bot_id"):
            return

        # Get user info
        user_info = await client.users_info(user=user_id)
        username = user_info["user"]["real_name"] or user_info["user"]["name"]

        # Remove bot mention from text if present
        if is_mention:
            text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()

        # Call bot for response
        try:
            response = self._bot.chat_completion(username, text)

            # Split response if needed (Slack limit is ~40,000 chars, but we'll use 3000 for readability)
            chunks = self._split_message(response, 3000)

            # Send response(s) in thread
            for i, chunk in enumerate(chunks):
                if i == 0:
                    # First message
                    await say(
                        text=chunk,
                        thread_ts=thread_ts
                    )
                else:
                    # Follow-up messages
                    await client.chat_postMessage(
                        channel=channel,
                        text=chunk,
                        thread_ts=thread_ts
                    )

        except Exception as e:
            print(f"Error processing message: {e}")
            await say(
                text=f"Sorry, I encountered an error: {str(e)}",
                thread_ts=thread_ts
            )

    def _split_message(self, message: str, chunk_size: int = 3000) -> list:
        """
        Split message into chunks while respecting code blocks and formatting.

        TODO: Implement smart chunking that respects:
        - Code block boundaries (```)
        - Paragraph breaks
        - List formatting
        """
        # Simple chunking for now
        chunks = []
        while message:
            if len(message) <= chunk_size:
                chunks.append(message)
                break

            # Try to break at newline
            split_pos = message.rfind('\n', 0, chunk_size)
            if split_pos == -1:
                split_pos = chunk_size

            chunks.append(message[:split_pos])
            message = message[split_pos:].lstrip()

        return chunks

    def is_ready(self) -> bool:
        """Check if Slack connection is ready"""
        return self._check

    async def start(self) -> None:
        """Start Slack Socket Mode connection"""
        print(f"Starting Slack integration...")

        # Create Socket Mode handler
        self._handler = AsyncSocketModeHandler(
            app=self.app,
            app_token=self._app_token
        )

        # Start handler (this is non-blocking in newer versions)
        await self._handler.start_async()
        self._check = True
        print("Slack integration ready!")

    async def stop(self) -> None:
        """Stop Slack Socket Mode connection"""
        print("Stopping Slack integration...")
        if self._handler:
            await self._handler.close_async()
        self._check = False
        print("Slack integration stopped")
```

#### Configuration Schema

```yaml
# Slack configuration
slack:
  enabled: true
  bot_token: "xoxb-your-bot-token"
  app_token: "xapp-your-app-token"  # For Socket Mode
  signing_secret: "your-signing-secret"  # Optional

amibot:
  username: "amigo"
  system_role: |
    You are a helpful AI assistant in a Slack workspace.
    Keep responses professional and formatted for Slack.

llm:
  provider: "anthropic"
  enabled: true
  model: "claude-3-5-sonnet-20240620"
  key: "sk-ant-..."
  tokens_range:
    from: 256
    until: 4096
    increment: 256
```

#### Slack App Setup Requirements

**Required Slack App Permissions** (OAuth Scopes):
- `app_mentions:read` - See mentions
- `channels:history` - Read channel messages
- `chat:write` - Send messages
- `im:history` - Read DMs
- `im:write` - Send DMs
- `users:read` - Get user information
- `files:read` - Read file uploads (optional)

**Event Subscriptions**:
- `app_mention` - Bot is mentioned
- `message.im` - Direct messages
- `app_home_opened` - App Home tab

**Features**:
- Socket Mode enabled (for firewall-friendly connection)
- Bot User enabled
- App Home enabled (optional)

---

### 2. Signal Integration (`signal_client.py`)

#### Purpose
Connect AmiBot to Signal messenger using signal-cli wrapper. Provides encrypted messaging with individuals and groups.

#### Architecture

```python
from community import Community
import asyncio
import subprocess
import json
import re
from typing import Optional, Dict, Any
import threading
import queue

class Signal(Community):
    """
    Signal messenger integration using signal-cli.

    Features:
    - Individual conversations
    - Group messaging
    - End-to-end encryption (via Signal protocol)
    - Read receipts
    - Typing indicators
    - Reply detection

    Requirements:
    - signal-cli installed and configured
    - Registered phone number
    - Linked to Signal account
    """

    def __init__(
        self,
        phone_number: str,
        signal_cli_path: str = "signal-cli",
        signal_cli_config: str = "/var/lib/signal-cli"
    ):
        super().__init__("Signal", phone_number)
        self._phone_number = phone_number
        self._signal_cli_path = signal_cli_path
        self._signal_cli_config = signal_cli_config
        self._check = False
        self._running = False
        self._message_queue = queue.Queue()
        self._receive_thread = None

    def _run_signal_command(
        self,
        command: list,
        capture_output: bool = True
    ) -> Optional[str]:
        """Execute signal-cli command"""
        full_command = [
            self._signal_cli_path,
            "--config", self._signal_cli_config,
            "-u", self._phone_number
        ] + command

        try:
            if capture_output:
                result = subprocess.run(
                    full_command,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.stdout
            else:
                subprocess.Popen(full_command)
                return None
        except subprocess.TimeoutExpired:
            print("Signal command timed out")
            return None
        except Exception as e:
            print(f"Error running signal-cli: {e}")
            return None

    def _receive_messages(self):
        """Background thread to receive Signal messages"""
        print("Starting Signal message receiver...")

        # Start signal-cli in receive mode (daemon)
        command = [
            self._signal_cli_path,
            "--config", self._signal_cli_config,
            "-u", self._phone_number,
            "daemon",
            "--json"
        ]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self._check = True

            # Read messages line by line
            for line in process.stdout:
                if not self._running:
                    break

                try:
                    # Parse JSON message
                    data = json.loads(line.strip())

                    # Handle sync messages (incoming)
                    if "envelope" in data:
                        envelope = data["envelope"]

                        # Extract message
                        if "dataMessage" in envelope:
                            message_data = envelope["dataMessage"]
                            sender = envelope.get("source") or envelope.get("sourceNumber")
                            message_text = message_data.get("message", "")
                            timestamp = envelope.get("timestamp")
                            group_id = message_data.get("groupInfo", {}).get("groupId")

                            # Queue message for processing
                            self._message_queue.put({
                                "sender": sender,
                                "message": message_text,
                                "timestamp": timestamp,
                                "group_id": group_id,
                                "is_group": group_id is not None
                            })

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error parsing message: {e}")
                    continue

        except Exception as e:
            print(f"Signal receiver error: {e}")
            self._check = False
        finally:
            if process:
                process.terminate()

    async def _process_messages(self):
        """Process queued messages"""
        while self._running:
            try:
                # Get message from queue (non-blocking with timeout)
                try:
                    msg_data = self._message_queue.get(timeout=1)
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                sender = msg_data["sender"]
                message = msg_data["message"]
                group_id = msg_data.get("group_id")

                # Skip empty messages
                if not message or not message.strip():
                    continue

                # Get sender name (use phone number as fallback)
                username = self._get_contact_name(sender) or sender

                # Call bot for response
                try:
                    response = self._bot.chat_completion(username, message)

                    # Send response
                    await self._send_message(
                        recipient=sender,
                        message=response,
                        group_id=group_id
                    )

                except Exception as e:
                    print(f"Error processing Signal message: {e}")
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    await self._send_message(
                        recipient=sender,
                        message=error_msg,
                        group_id=group_id
                    )

            except Exception as e:
                print(f"Message processing error: {e}")
                await asyncio.sleep(1)

    async def _send_message(
        self,
        recipient: str,
        message: str,
        group_id: Optional[str] = None
    ):
        """Send message via signal-cli"""
        # Split long messages
        chunks = self._split_message(message, 2000)

        for chunk in chunks:
            if group_id:
                # Send to group
                command = [
                    "send",
                    "-g", group_id,
                    "-m", chunk
                ]
            else:
                # Send to individual
                command = [
                    "send",
                    recipient,
                    "-m", chunk
                ]

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._run_signal_command,
                command,
                False
            )

            # Small delay between chunks
            await asyncio.sleep(0.5)

    def _split_message(self, message: str, chunk_size: int = 2000) -> list:
        """Split message into chunks"""
        chunks = []
        while message:
            if len(message) <= chunk_size:
                chunks.append(message)
                break

            # Try to break at newline
            split_pos = message.rfind('\n', 0, chunk_size)
            if split_pos == -1:
                split_pos = chunk_size

            chunks.append(message[:split_pos])
            message = message[split_pos:].lstrip()

        return chunks

    def _get_contact_name(self, number: str) -> Optional[str]:
        """Get contact name for phone number"""
        # Query signal-cli for contact info
        command = ["listContacts", "--json"]
        output = self._run_signal_command(command)

        if output:
            try:
                contacts = json.loads(output)
                for contact in contacts:
                    if contact.get("number") == number:
                        return contact.get("name") or contact.get("number")
            except:
                pass

        return None

    def is_ready(self) -> bool:
        """Check if Signal connection is ready"""
        return self._check

    async def start(self) -> None:
        """Start Signal message receiver"""
        print(f"Starting Signal integration for {self._phone_number}...")

        # Verify signal-cli is available
        try:
            result = subprocess.run(
                [self._signal_cli_path, "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("signal-cli not accessible")
        except Exception as e:
            print(f"Error: signal-cli not found or not working: {e}")
            return

        self._running = True

        # Start receiver thread
        self._receive_thread = threading.Thread(
            target=self._receive_messages,
            daemon=True
        )
        self._receive_thread.start()

        # Start message processor
        asyncio.create_task(self._process_messages())

        print("Signal integration ready!")

    async def stop(self) -> None:
        """Stop Signal integration"""
        print("Stopping Signal integration...")
        self._running = False

        if self._receive_thread:
            self._receive_thread.join(timeout=5)

        self._check = False
        print("Signal integration stopped")
```

#### Configuration Schema

```yaml
# Signal configuration
signal:
  enabled: true
  phone_number: "+1234567890"
  signal_cli_path: "/usr/local/bin/signal-cli"
  signal_cli_config: "/var/lib/signal-cli"

amibot:
  username: "amigo"
  system_role: |
    You are a privacy-focused AI assistant on Signal.
    Keep conversations secure and confidential.

llm:
  provider: "anthropic"
  enabled: true
  model: "claude-3-5-sonnet-20240620"
  key: "sk-ant-..."
  tokens_range:
    from: 256
    until: 4096
    increment: 256
```

#### Signal Setup Requirements

**Prerequisites**:
1. Install signal-cli:
   ```bash
   # Using package manager
   sudo apt install signal-cli  # Debian/Ubuntu
   brew install signal-cli      # macOS

   # Or download from releases
   wget https://github.com/AsamK/signal-cli/releases/download/v0.12.0/signal-cli-0.12.0.tar.gz
   ```

2. Register phone number:
   ```bash
   signal-cli -u +1234567890 register
   # Follow verification process
   signal-cli -u +1234567890 verify CODE
   ```

3. Link to existing Signal account (alternative):
   ```bash
   signal-cli -u +1234567890 link -n "AmiBot"
   # Scan QR code with Signal app
   ```

---

## Implementation Plan

### Phase 1: Slack Integration (Week 1-2)

**Tasks**:
1. ✅ Research Slack Bolt framework
2. ✅ Create `amibot/community/slack_client.py`
3. ✅ Implement Socket Mode connection
4. ✅ Add app mention handling
5. ✅ Add direct message handling
6. ✅ Implement thread support
7. ✅ Add message formatting (Slack mrkdwn)
8. ✅ Add error handling
9. ✅ Update `__main__.py` to support Slack
10. ✅ Create Slack app setup guide
11. ✅ Write unit tests

**Dependencies**:
- `slack-bolt>=1.18.0` - Slack Bolt framework
- `slack-sdk>=3.23.0` - Slack SDK (dependency of bolt)

**Files to Modify**:
- `amibot/community/slack_client.py` (new)
- `amibot/__main__.py` (add Slack initialization)
- `configs/amibot_example.conf` (add Slack example)
- `requirements.txt` (add slack-bolt)

### Phase 2: Signal Integration (Week 3-4)

**Tasks**:
1. ✅ Research signal-cli wrapper options
2. ✅ Create `amibot/community/signal_client.py`
3. ✅ Implement daemon mode receiver
4. ✅ Add message parsing (JSON)
5. ✅ Add individual message handling
6. ✅ Add group message handling
7. ✅ Implement contact name resolution
8. ✅ Add error handling and reconnection
9. ✅ Update `__main__.py` to support Signal
10. ✅ Create Signal setup guide
11. ✅ Write integration tests

**Dependencies**:
- `signal-cli` (external binary, not Python package)
- System dependency management in docs

**Files to Modify**:
- `amibot/community/signal_client.py` (new)
- `amibot/__main__.py` (add Signal initialization)
- `configs/amibot_example.conf` (add Signal example)
- `documentation/` (setup guides)

### Phase 3: Multi-Platform Support (Week 5)

**Tasks**:
1. ✅ Support running multiple communities simultaneously
2. ✅ Update `__main__.py` for multi-community configuration
3. ✅ Add platform-specific bot configuration
4. ✅ Test Discord + Slack together
5. ✅ Test Discord + Signal together
6. ✅ Test all three platforms together
7. ✅ Performance testing
8. ✅ Update health checks for multiple platforms
9. ✅ Update documentation
10. ✅ Create deployment examples

### Phase 4: Documentation and Release (Week 6)

**Tasks**:
1. ✅ Update CLAUDE.md with new platforms
2. ✅ Update TECHNICAL_DIAGRAMS.md
3. ✅ Create platform-specific guides
4. ✅ Add troubleshooting sections
5. ✅ Update README.md
6. ✅ Create video tutorials (optional)
7. ✅ Beta testing
8. ✅ Address feedback
9. ✅ Release v0.2.0

---

## Configuration Schema

### Multi-Platform Configuration

```yaml
# Example: Running on all three platforms simultaneously

amibot:
  username: "amigo"
  system_role: |
    You are a helpful AI assistant available across multiple platforms.
    Adapt your communication style to each platform's culture.

# Discord (existing)
discord:
  enabled: true
  application_id: "..."
  public_key: "..."
  token: "..."

# Slack (NEW)
slack:
  enabled: true
  bot_token: "xoxb-..."
  app_token: "xapp-..."
  signing_secret: "..."

# Signal (NEW)
signal:
  enabled: true
  phone_number: "+1234567890"
  signal_cli_path: "/usr/local/bin/signal-cli"
  signal_cli_config: "/var/lib/signal-cli"

# Bot configuration (shared across platforms)
llm:
  provider: "anthropic"
  enabled: true
  model: "claude-3-5-sonnet-20240620"
  key: "sk-ant-..."
  tokens_range:
    from: 256
    until: 4096
    increment: 256
```

### Platform-Specific Bot Configuration (Advanced)

```yaml
# Example: Different bot behavior per platform

amibot:
  username: "amigo"
  system_role: |
    Default system role for all platforms.

discord:
  enabled: true
  token: "..."
  # Platform-specific bot config
  llm:
    provider: "openai"
    model: "gpt-4-turbo"
    key: "sk-..."

slack:
  enabled: true
  bot_token: "xoxb-..."
  app_token: "xapp-..."
  # Platform-specific bot config
  llm:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20240620"
    key: "sk-ant-..."

signal:
  enabled: true
  phone_number: "+1234567890"
  # Platform-specific bot config
  llm:
    provider: "agent"
    endpoint_url: "http://localhost:11434/v1/chat/completions"
    model: "llama3.2"
```

### Configuration Changes Required

**`__main__.py`** - Support multiple communities:

```python
# Initialize communities list
communities = []

# Check for Discord
if "discord" in configuration and configuration['discord'].get('enabled'):
    discord_community = Discord(configuration['discord']['token'])
    communities.append(discord_community)

# Check for Slack
if "slack" in configuration and configuration['slack'].get('enabled'):
    from community.slack_client import Slack
    slack_community = Slack(
        bot_token=configuration['slack']['bot_token'],
        app_token=configuration['slack']['app_token'],
        signing_secret=configuration['slack'].get('signing_secret')
    )
    communities.append(slack_community)

# Check for Signal
if "signal" in configuration and configuration['signal'].get('enabled'):
    from community.signal_client import Signal
    signal_community = Signal(
        phone_number=configuration['signal']['phone_number'],
        signal_cli_path=configuration['signal'].get('signal_cli_path', 'signal-cli'),
        signal_cli_config=configuration['signal'].get('signal_cli_config', '/var/lib/signal-cli')
    )
    communities.append(signal_community)

# Inject bot into all communities
for community in communities:
    community.bot = amigo

# Start all communities
for community in communities:
    loop.create_task(community.start())
```

---

## Testing Strategy

### Unit Tests

**Slack Tests** (`tests/test_slack_client.py`):
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from amibot.community.slack_client import Slack

@pytest.mark.asyncio
async def test_slack_initialization():
    slack = Slack(
        bot_token="xoxb-test",
        app_token="xapp-test"
    )
    assert slack.platform == "Slack"
    assert not slack.is_ready()

@pytest.mark.asyncio
async def test_slack_mention_handling():
    # Mock Slack app
    with patch('slack_bolt.async_app.AsyncApp'):
        slack = Slack(
            bot_token="xoxb-test",
            app_token="xapp-test"
        )

        # Set mock bot
        mock_bot = Mock()
        mock_bot.chat_completion.return_value = "Test response"
        slack.bot = mock_bot

        # Simulate mention event
        event = {
            "user": "U12345",
            "text": "<@UBOT123> Hello",
            "channel": "C12345",
            "ts": "1234567890.123456"
        }

        # Test mention handler
        # ... test implementation

def test_message_splitting():
    slack = Slack(
        bot_token="xoxb-test",
        app_token="xapp-test"
    )

    long_message = "a" * 5000
    chunks = slack._split_message(long_message, 3000)

    assert len(chunks) == 2
    assert len(chunks[0]) <= 3000
```

**Signal Tests** (`tests/test_signal_client.py`):
```python
import pytest
from unittest.mock import Mock, patch
from amibot.community.signal_client import Signal

def test_signal_initialization():
    signal = Signal(phone_number="+1234567890")
    assert signal.platform == "Signal"
    assert signal._phone_number == "+1234567890"

@patch('subprocess.run')
def test_signal_cli_command(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout="test output")

    signal = Signal(phone_number="+1234567890")
    result = signal._run_signal_command(["test"])

    assert result == "test output"
    mock_run.assert_called_once()

def test_message_parsing():
    # Test JSON message parsing
    pass

def test_contact_name_resolution():
    # Test contact lookup
    pass
```

### Integration Tests

**Slack Integration** (`tests/integration/test_slack_integration.py`):
```bash
# Requires actual Slack workspace and tokens
# Set environment variables:
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."

pytest tests/integration/test_slack_integration.py
```

**Signal Integration** (`tests/integration/test_signal_integration.py`):
```bash
# Requires signal-cli installed and configured
# Set environment variable:
export SIGNAL_PHONE="+1234567890"

pytest tests/integration/test_signal_integration.py
```

### Manual Testing Checklist

**Slack**:
- [ ] Bot responds to @mentions in channels
- [ ] Bot responds to DMs
- [ ] Bot maintains thread context
- [ ] Bot handles long messages (chunking)
- [ ] Bot shows in App Home
- [ ] Bot handles rate limits gracefully
- [ ] Bot works with Slack formatting (bold, italic, code)

**Signal**:
- [ ] Bot receives individual messages
- [ ] Bot receives group messages
- [ ] Bot sends individual replies
- [ ] Bot sends group replies
- [ ] Bot handles long messages (chunking)
- [ ] Bot resolves contact names
- [ ] Bot handles reconnection after signal-cli restart

**Multi-Platform**:
- [ ] Discord + Slack work simultaneously
- [ ] Discord + Signal work simultaneously
- [ ] All three platforms work together
- [ ] Health checks report all platforms
- [ ] Each platform maintains independent context
- [ ] No message cross-contamination

---

## Migration Path

### For Existing Deployments

**No Breaking Changes**:
- Existing Discord deployment continues to work
- No changes to current configuration required
- New platforms are opt-in
- Can be added incrementally

**Migration Steps**:

1. **Add Platform Dependencies**:
   ```bash
   pip install slack-bolt>=1.18.0  # For Slack
   # Signal requires system package (signal-cli)
   ```

2. **Update Configuration** (optional):
   ```yaml
   # Add new platform sections
   slack:
     enabled: true
     bot_token: "xoxb-..."
     # ...

   signal:
     enabled: true
     phone_number: "+1234567890"
     # ...
   ```

3. **Test New Platform**:
   ```bash
   python -m amibot -c configs/multi-platform.conf
   ```

4. **Deploy**:
   - Update Docker image with new dependencies
   - Update Kubernetes ConfigMap
   - Update ECS task definition
   - Add required secrets/tokens

### Backward Compatibility

- ✅ Existing Discord-only deployments work unchanged
- ✅ No changes to Community base class interface
- ✅ No changes to Bot integration
- ✅ Configuration is additive, not breaking
- ✅ Health checks remain compatible

---

## Benefits and Use Cases

### Slack Benefits

**Enterprise Adoption**:
- 💼 Deploy in corporate workspaces
- 💼 Integrate with enterprise workflows
- 💼 Support department-specific bots
- 💼 Leverage Slack's security and compliance

**User Experience**:
- 📱 Rich message formatting
- 📱 Thread-based conversations
- 📱 App Home for help and info
- 📱 Integration with Slack ecosystem

**Business Value**:
- 📊 Reach enterprise customers
- 📊 Potential for Slack App Directory listing
- 📊 Monetization opportunities
- 📊 Professional credibility

### Signal Benefits

**Privacy & Security**:
- 🔒 End-to-end encryption by default
- 🔒 No metadata collection
- 🔒 Open-source protocol
- 🔒 Compliance-friendly (GDPR, HIPAA)

**Use Cases**:
- 🩺 Healthcare conversations
- ⚖️ Legal communications
- 📰 Journalist support
- 🔐 Security-conscious users

**Differentiation**:
- 🌟 First major AI bot with Signal support
- 🌟 Privacy-first positioning
- 🌟 Unique market segment

### Multi-Platform Benefits

**Flexibility**:
- 🌐 Serve users where they are
- 🌐 Platform-agnostic architecture
- 🌐 Easy to add more platforms
- 🌐 Single bot, multiple interfaces

**Resilience**:
- 🛡️ Platform outage redundancy
- 🛡️ Diversified user base
- 🛡️ Reduced platform lock-in

### Use Cases

**Enterprise IT Support**:
- Deploy same bot in Slack (employees) and Discord (customers)
- Centralized AI assistant across communication channels
- Consistent experience regardless of platform

**Healthcare AI Assistant**:
- Use Signal for patient communication (HIPAA-compliant)
- Use Slack for internal staff collaboration
- Same AI model, platform-appropriate security

**Community Management**:
- Discord for gaming/hobby communities
- Slack for professional groups
- Same bot personality, different audiences

**Personal Assistant**:
- Signal for private/family use
- Slack for work use
- Context isolation per platform

---

## Risks and Mitigation

### Technical Risks

**Risk**: Slack API complexity and rate limits
- **Mitigation**: Use Slack Bolt framework (handles complexity)
- **Mitigation**: Implement exponential backoff
- **Mitigation**: Monitor rate limit headers

**Risk**: signal-cli stability and maintenance
- **Mitigation**: Document alternative libraries (pysignal)
- **Mitigation**: Implement health checks
- **Mitigation**: Add automatic restart on failure

**Risk**: Resource usage with multiple platforms
- **Mitigation**: Async I/O for all platforms
- **Mitigation**: Configure resource limits
- **Mitigation**: Monitor memory/CPU usage

**Risk**: Message context confusion across platforms
- **Mitigation**: Platform-specific user namespacing
- **Mitigation**: Store platform ID with conversation
- **Mitigation**: Clear separation in bot.chat_completion()

### Security Risks

**Risk**: Token/credential exposure
- **Mitigation**: Use environment variables
- **Mitigation**: Kubernetes Secrets for deployment
- **Mitigation**: Never log sensitive data

**Risk**: Signal phone number security
- **Mitigation**: Use dedicated number for bot
- **Mitigation**: Document security best practices
- **Mitigation**: Implement access controls

**Risk**: Cross-platform data leakage
- **Mitigation**: Isolated conversation contexts
- **Mitigation**: Platform-specific configuration
- **Mitigation**: Security audit before release

### Operational Risks

**Risk**: Increased support complexity
- **Mitigation**: Comprehensive platform-specific docs
- **Mitigation**: Troubleshooting guides
- **Mitigation**: Clear error messages

**Risk**: Platform API changes
- **Mitigation**: Use stable SDK versions
- **Mitigation**: Monitor platform changelogs
- **Mitigation**: Automated testing

**Risk**: Onboarding complexity
- **Mitigation**: Step-by-step setup guides
- **Mitigation**: Configuration validation
- **Mitigation**: Health check endpoints

---

## Future Enhancements

### Phase 2 Platforms

**Telegram**:
- [ ] Massive user base (800M+ users)
- [ ] Bot API well-documented
- [ ] Rich features (inline keyboards, payments)
- [ ] python-telegram-bot library

**Microsoft Teams**:
- [ ] Enterprise market (280M+ users)
- [ ] Azure integration
- [ ] Office 365 ecosystem
- [ ] Bot Framework SDK

**Matrix**:
- [ ] Open protocol, federated
- [ ] End-to-end encryption
- [ ] Self-hosted options
- [ ] matrix-nio Python library

**WhatsApp Business**:
- [ ] Largest user base (2B+ users)
- [ ] Business API available
- [ ] Meta platform
- [ ] Enterprise messaging

### Advanced Features

**Per-Platform Customization**:
- [ ] Different bots per platform
- [ ] Platform-specific system roles
- [ ] Custom token limits per platform
- [ ] Platform-specific LLM models

**Cross-Platform Features**:
- [ ] Message forwarding between platforms
- [ ] Unified conversation history
- [ ] Cross-platform mentions
- [ ] Multi-platform analytics

**Enhanced Integrations**:
- [ ] Slack slash commands
- [ ] Slack workflow integration
- [ ] Signal group admin features
- [ ] Platform-specific rich media

**Management Tools**:
- [ ] Admin dashboard for multi-platform
- [ ] Platform usage analytics
- [ ] Cost tracking per platform
- [ ] A/B testing framework

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
requests>=2.31.0

# NEW for Slack
slack-bolt~=1.18.0
slack-sdk~=3.23.0

# NEW for Signal (external)
# signal-cli (install via system package manager or from GitHub releases)
```

### B. Platform Comparison Matrix

| Feature | Discord | Slack | Signal | Telegram | Teams |
|---------|---------|-------|--------|----------|-------|
| **Users** | 150M+ | 20M+ | 40M+ | 800M+ | 280M+ |
| **Market** | Gaming/Communities | Enterprise | Privacy | General | Enterprise |
| **Pricing** | Free/Nitro | Free/Paid tiers | Free | Free | Microsoft 365 |
| **Bot API** | ✅ Excellent | ✅ Excellent | ⚠️ CLI-based | ✅ Excellent | ✅ Good |
| **Encryption** | ❌ No E2E | ❌ No E2E | ✅ E2E default | ⚠️ Secret chats | ✅ E2E available |
| **Rich Formatting** | ✅ | ✅ | ⚠️ Limited | ✅ | ✅ |
| **Self-Hosting** | ❌ | ❌ | ✅ | ❌ | ⚠️ Hybrid |
| **Implementation** | ✅ Done | 📋 Proposed | 📋 Proposed | ⏳ Future | ⏳ Future |

### C. Setup Guides

**Slack App Creation**:
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "AmiBot", select workspace
4. Add Bot Token Scopes (see requirements above)
5. Enable Socket Mode, generate App Token
6. Install to workspace
7. Copy Bot Token and App Token to config

**Signal Registration**:
1. Install signal-cli (see requirements)
2. Register: `signal-cli -u +1234567890 register`
3. Verify: `signal-cli -u +1234567890 verify CODE`
4. Test: `signal-cli -u +1234567890 send +1234567890 -m "test"`
5. Copy phone number to config

### D. Troubleshooting

**Slack Issues**:
```bash
# Test Slack tokens
curl -H "Authorization: Bearer xoxb-..." https://slack.com/api/auth.test

# Check Socket Mode connection
# Look for "Connected to Slack" in logs

# Common errors:
# - "not_allowed_token_type": Use Bot Token (xoxb-), not User Token
# - "invalid_auth": Check token validity
# - "missing_scope": Add required OAuth scopes
```

**Signal Issues**:
```bash
# Test signal-cli
signal-cli -u +1234567890 --version

# Test sending
signal-cli -u +1234567890 send +1234567890 -m "test"

# Test receiving (daemon mode)
signal-cli -u +1234567890 daemon --json

# Common errors:
# - "Not registered": Run register and verify steps
# - "Connection timeout": Check internet connection
# - "Invalid number format": Use international format (+1...)
```

---

## Approval and Sign-off

This proposal requires review and approval from:

- [ ] Technical Lead - Architecture review
- [ ] Security Team - Multi-platform security assessment
- [ ] DevOps Team - Deployment and scaling considerations
- [ ] Product Owner - Business value and market fit
- [ ] Platform Experts - Slack and Signal implementation review

**Estimated Effort**: 6 weeks (1 developer)
**Target Release**: v0.2.0
**Risk Level**: Medium

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Next Review**: After Phase 1 completion
