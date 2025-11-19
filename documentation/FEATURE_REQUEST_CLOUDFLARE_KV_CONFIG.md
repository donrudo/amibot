# Feature Request: Cloudflare KV Configuration Source

**Status**: Proposed
**Priority**: Medium
**Created**: 2025-11-19
**Author**: AI Assistant
**Related Issues**: N/A

---

## Table of Contents
1. [Overview](#overview)
2. [Motivation](#motivation)
3. [Architecture](#architecture)
4. [Implementation Steps](#implementation-steps)
5. [Source Code Changes](#source-code-changes)
6. [Configuration Schema](#configuration-schema)
7. [Dependencies](#dependencies)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Considerations](#deployment-considerations)
10. [Security Considerations](#security-considerations)
11. [Migration Path](#migration-path)
12. [Future Enhancements](#future-enhancements)

---

## Overview

Add support for loading AmiBot configuration from Cloudflare Workers KV (Key-Value) storage, enabling configuration management through Cloudflare's global edge network.

### What is Cloudflare KV?

Cloudflare Workers KV is a global, low-latency key-value data store accessible from Cloudflare's edge network. It provides:
- Global distribution across 300+ data centers
- Eventually consistent reads
- Strong consistency for writes
- REST API and Workers API access
- Low latency reads (<50ms globally)

### Proposed Feature

Extend the existing `ConfigLoader` pattern to support configuration retrieval from Cloudflare KV namespaces using the Cloudflare API.

**Protocol Format**:
```bash
# Using KV namespace ID and key
python -m amibot -c "kv://<account_id>/<namespace_id>/<key>"

# Using named namespace (requires environment variable mapping)
python -m amibot -c "kv://amibot-config/production"
```

---

## Motivation

### Why Cloudflare KV?

1. **Edge Performance**: Configuration loaded from nearest edge location (lower latency than S3)
2. **Cloudflare Integration**: Ideal for deployments on Cloudflare Workers or Pages
3. **Cost Efficiency**:
   - First 100K reads/day free
   - $0.50 per million reads thereafter
   - Cheaper than S3 for read-heavy workloads
4. **Global Availability**: Automatic replication across Cloudflare's network
5. **Simple API**: RESTful API easier than AWS SDK setup
6. **Multi-Environment Support**: Easy namespace-based configuration separation (dev/staging/prod)

### Use Cases

- **Cloudflare Workers Deployment**: Natural fit for Workers-based bot deployments
- **Multi-Region Deployments**: Low-latency config access from any region
- **Dynamic Configuration**: Update config globally without redeploying
- **A/B Testing**: Multiple config versions in different namespaces
- **Cost Optimization**: Reduce AWS dependencies for non-AWS deployments

---

## Architecture

### Class Hierarchy (Updated)

```python
ConfigLoader (base)
  ├── FromFile (extends ConfigLoader)
  ├── FromS3 (extends ConfigLoader)
  └── FromCloudflareKV (extends ConfigLoader)  # NEW
```

### Configuration Loading Flow

```
User Input: -c kv://account/namespace/key
    │
    ▼
Protocol Detection (__main__.py:119-130)
    │
    ├─ file: → FromFile
    ├─ s3:   → FromS3
    └─ kv:   → FromCloudflareKV  # NEW
    │
    ▼
FromCloudflareKV.__init__(uri)
    │
    ├─ Parse URI (account_id, namespace_id, key)
    ├─ Load credentials (env vars or config)
    └─ Validate authentication
    │
    ▼
FromCloudflareKV.configuration
    │
    ├─ Build API URL
    ├─ Make HTTP GET request with auth
    ├─ Parse JSON/YAML response
    ├─ Validate configuration schema
    └─ Return config dict
```

### API Interaction Diagram

```
┌─────────────┐                    ┌──────────────────────┐
│   AmiBot    │                    │  Cloudflare KV API   │
│  __main__.py│                    │  (Global Edge)       │
└──────┬──────┘                    └──────────┬───────────┘
       │                                      │
       │ 1. Initialize FromCloudflareKV       │
       │────────────────────────────────────> │
       │                                      │
       │ 2. GET /accounts/{id}/storage/kv/   │
       │    namespaces/{ns}/values/{key}     │
       │    Header: Authorization: Bearer ... │
       │────────────────────────────────────> │
       │                                      │
       │ 3. Return YAML/JSON config           │
       │ <──────────────────────────────────  │
       │                                      │
       │ 4. Parse and validate                │
       │ ────┐                                │
       │     │                                │
       │ <───┘                                │
       │                                      │
       │ 5. Return config dict                │
       │ ────┐                                │
       │     │                                │
       │ <───┘                                │
       │                                      │
```

---

## Implementation Steps

### Step 1: Create FromCloudflareKV Class

**File**: `amibot/configloader/FromCloudflareKV.py` (NEW)

**Tasks**:
1. Create new file extending `ConfigLoader`
2. Implement URI parsing (account_id, namespace_id, key)
3. Implement Cloudflare API authentication
4. Implement HTTP GET request to KV API
5. Parse YAML/JSON response
6. Implement error handling and retries
7. Add logging

### Step 2: Update Protocol Detection

**File**: `amibot/__main__.py`

**Tasks**:
1. Add `kv:` case to protocol detection match statement (line 119-130)
2. Import `FromCloudflareKV` class
3. Add environment variable validation for KV credentials

### Step 3: Add Dependencies

**File**: `requirements.txt`

**Tasks**:
1. Add `requests` library (for HTTP requests)
2. Consider adding `pyyaml` if not already present
3. Add `python-dotenv` for credential management (optional)

### Step 4: Update Configuration Examples

**Files**: `configs/amibot_example.conf`, `README.md`, `CLAUDE.md`

**Tasks**:
1. Add KV configuration examples
2. Document environment variables
3. Update deployment guides

### Step 5: Add Error Handling

**File**: `amibot/configloader/FromCloudflareKV.py`

**Tasks**:
1. Handle authentication errors (401, 403)
2. Handle network errors (timeouts, connection failures)
3. Handle malformed configuration (YAML parsing errors)
4. Implement retry logic with exponential backoff

### Step 6: Add Documentation

**Files**: `CLAUDE.md`, `README.md`

**Tasks**:
1. Update architecture diagrams
2. Add KV configuration section
3. Add troubleshooting guide
4. Update deployment instructions

---

## Source Code Changes

### 1. Create `amibot/configloader/FromCloudflareKV.py`

```python
"""
Cloudflare KV Configuration Loader

Loads configuration from Cloudflare Workers KV storage using the REST API.

Protocol format: kv://<account_id>/<namespace_id>/<key>

Environment variables required:
- CLOUDFLARE_API_TOKEN: API token with KV read permissions
  OR
- CLOUDFLARE_API_KEY: Global API key
- CLOUDFLARE_EMAIL: Account email (when using API key)

Example usage:
    load = FromCloudflareKV("kv://abc123/ns-123/amibot-prod")
    config = load.configuration
"""

import os
import yaml
import json
import time
import logging
from urllib.parse import urlparse
from typing import Optional, Dict, Any
import requests

from configloader import ConfigLoader

logger = logging.getLogger(__name__)


class FromCloudflareKV(ConfigLoader):
    """Load configuration from Cloudflare Workers KV storage."""

    # Cloudflare API base URL
    API_BASE = "https://api.cloudflare.com/client/v4"

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    RETRY_BACKOFF = 2  # exponential backoff multiplier

    def __init__(self, uri: str):
        """
        Initialize Cloudflare KV loader.

        Args:
            uri: KV URI in format kv://<account_id>/<namespace_id>/<key>

        Raises:
            ValueError: If URI format is invalid or credentials are missing
        """
        super().__init__(uri)
        self._uri = uri
        self._config = None

        # Parse URI
        self._account_id, self._namespace_id, self._key = self._parse_uri(uri)

        # Load credentials
        self._api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        self._api_key = os.getenv('CLOUDFLARE_API_KEY')
        self._email = os.getenv('CLOUDFLARE_EMAIL')

        # Validate credentials
        if not self._api_token and not (self._api_key and self._email):
            raise ValueError(
                "Missing Cloudflare credentials. Set either:\n"
                "  - CLOUDFLARE_API_TOKEN (recommended)\n"
                "  OR\n"
                "  - CLOUDFLARE_API_KEY and CLOUDFLARE_EMAIL"
            )

        logger.info(f"Initialized Cloudflare KV loader: {self._account_id}/{self._namespace_id}/{self._key}")

    def _parse_uri(self, uri: str) -> tuple[str, str, str]:
        """
        Parse KV URI into components.

        Args:
            uri: URI in format kv://<account_id>/<namespace_id>/<key>

        Returns:
            Tuple of (account_id, namespace_id, key)

        Raises:
            ValueError: If URI format is invalid
        """
        parsed = urlparse(uri)

        if parsed.scheme != 'kv':
            raise ValueError(f"Invalid URI scheme: {parsed.scheme} (expected 'kv')")

        # Extract components from path
        # Format: kv://<account_id>/<namespace_id>/<key>
        # parsed.netloc = account_id
        # parsed.path = /<namespace_id>/<key>

        account_id = parsed.netloc
        path_parts = parsed.path.strip('/').split('/')

        if not account_id:
            raise ValueError("Missing account_id in URI")

        if len(path_parts) < 2:
            raise ValueError(
                f"Invalid URI format: {uri}\n"
                "Expected: kv://<account_id>/<namespace_id>/<key>"
            )

        namespace_id = path_parts[0]
        key = '/'.join(path_parts[1:])  # Support keys with slashes

        return account_id, namespace_id, key

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Build authentication headers for Cloudflare API.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'Content-Type': 'application/json'
        }

        if self._api_token:
            # Preferred: API token authentication
            headers['Authorization'] = f'Bearer {self._api_token}'
        else:
            # Legacy: API key + email authentication
            headers['X-Auth-Key'] = self._api_key
            headers['X-Auth-Email'] = self._email

        return headers

    def _build_api_url(self) -> str:
        """
        Build Cloudflare KV API URL.

        Returns:
            Full API URL for the KV key
        """
        return (
            f"{self.API_BASE}/accounts/{self._account_id}"
            f"/storage/kv/namespaces/{self._namespace_id}"
            f"/values/{self._key}"
        )

    def _fetch_from_kv(self) -> Optional[str]:
        """
        Fetch configuration value from Cloudflare KV with retries.

        Returns:
            Configuration content as string, or None on failure

        Raises:
            requests.exceptions.RequestException: On unrecoverable HTTP errors
        """
        url = self._build_api_url()
        headers = self._get_auth_headers()

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Fetching from Cloudflare KV (attempt {attempt + 1}/{self.MAX_RETRIES})")

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=10  # 10 second timeout
                )

                # Handle HTTP errors
                if response.status_code == 200:
                    logger.info("Successfully fetched configuration from Cloudflare KV")
                    return response.text

                elif response.status_code == 404:
                    logger.error(f"Configuration key not found: {self._key}")
                    logger.error(f"Namespace: {self._namespace_id}, Account: {self._account_id}")
                    return None

                elif response.status_code in [401, 403]:
                    logger.error(f"Authentication failed (HTTP {response.status_code})")
                    logger.error("Check your CLOUDFLARE_API_TOKEN or CLOUDFLARE_API_KEY/EMAIL")
                    return None

                elif response.status_code == 429:
                    # Rate limited - retry with backoff
                    retry_after = int(response.headers.get('Retry-After', self.RETRY_DELAY))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                else:
                    logger.error(f"HTTP error {response.status_code}: {response.text}")
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                        logger.info(f"Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.MAX_RETRIES})")
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    time.sleep(delay)
                    continue
                logger.error("Max retries exceeded due to timeouts")
                return None

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    time.sleep(delay)
                    continue
                logger.error("Max retries exceeded due to connection errors")
                return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                return None

        return None

    def _parse_configuration(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse configuration content (YAML or JSON).

        Args:
            content: Raw configuration string

        Returns:
            Parsed configuration dictionary, or None on error
        """
        if not content:
            return None

        # Try YAML first (supports JSON too)
        try:
            config = yaml.safe_load(content)
            logger.info("Successfully parsed configuration as YAML")
            return config
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")

        # Try JSON as fallback
        try:
            config = json.loads(content)
            logger.info("Successfully parsed configuration as JSON")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")

        logger.error("Configuration is neither valid YAML nor JSON")
        return None

    def _validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.

        Args:
            config: Parsed configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        required_sections = ['amibot', 'llm']

        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required configuration section: {section}")
                return False

        # Validate amibot section
        if 'username' not in config['amibot']:
            logger.error("Missing 'amibot.username' in configuration")
            return False

        if 'system_role' not in config['amibot']:
            logger.error("Missing 'amibot.system_role' in configuration")
            return False

        # Validate llm section
        required_llm_fields = ['provider', 'enabled', 'model', 'key', 'tokens_range']
        for field in required_llm_fields:
            if field not in config['llm']:
                logger.error(f"Missing 'llm.{field}' in configuration")
                return False

        logger.info("Configuration validation passed")
        return True

    @property
    def configuration(self) -> Optional[Dict[str, Any]]:
        """
        Load and return configuration from Cloudflare KV.

        Returns:
            Configuration dictionary, or None on error
        """
        # Return cached config if already loaded
        if self._config is not None:
            return self._config

        # Fetch from KV
        content = self._fetch_from_kv()
        if not content:
            logger.error("Failed to fetch configuration from Cloudflare KV")
            return None

        # Parse configuration
        config = self._parse_configuration(content)
        if not config:
            logger.error("Failed to parse configuration")
            return None

        # Validate configuration
        if not self._validate_configuration(config):
            logger.error("Configuration validation failed")
            return None

        # Cache and return
        self._config = config
        logger.info("Configuration loaded successfully from Cloudflare KV")
        return self._config
```

### 2. Update `amibot/__main__.py`

**Change 1: Add import** (after line 19):
```python
from configloader.FromCloudflareKV import FromCloudflareKV
```

**Change 2: Update protocol detection** (replace lines 119-130):
```python
# ConfigLoader factory pattern
if args.config:
    location = args.config.split(':')

    match location[0]:
        case 'file':
            # Explicit file protocol: file:/path/to/config
            load = FromFile(location[1])

        case 's3':
            # S3 protocol: s3://bucket/key
            load = FromS3(args.config)

        case 'https':
            # Assume S3 HTTPS URL
            load = FromS3(args.config)

        case 'kv':
            # Cloudflare KV protocol: kv://account/namespace/key
            load = FromCloudflareKV(args.config)

        case _:
            # Default to file
            load = FromFile(args.config)
else:
    # No config specified
    print("Error: Configuration file required (-c/--config)")
    exit(1)
```

**Change 3: Add environment variable validation** (after line 136):
```python
# Validate configuration was loaded
if not load.configuration:
    print("Error: Failed to load configuration")
    print("Check your configuration source and credentials")
    exit(1)

configuration = load.configuration
```

### 3. Update `requirements.txt`

**Add after existing dependencies**:
```txt
# HTTP client for Cloudflare API
requests>=2.31.0,<3.0.0

# Environment variable management (optional)
python-dotenv>=1.0.0,<2.0.0
```

### 4. Create Example Environment File

**File**: `.env.example` (NEW)

```bash
# Cloudflare KV Configuration
# Choose ONE authentication method:

# Method 1: API Token (Recommended)
# Create at: https://dash.cloudflare.com/profile/api-tokens
# Required permissions: Account > Workers KV Storage > Read
CLOUDFLARE_API_TOKEN=your_api_token_here

# Method 2: Global API Key (Legacy)
# CLOUDFLARE_API_KEY=your_global_api_key
# CLOUDFLARE_EMAIL=your_cloudflare_email@example.com

# KV Configuration URI Format:
# kv://<account_id>/<namespace_id>/<key>
#
# Example:
# python -m amibot -c "kv://abc123def456/9a7b8c6d5e4f3g2h/amibot-production"
```

### 5. Update `configs/amibot_example.conf`

**Add comment at top**:
```yaml
# AmiBot Configuration File
#
# This file can be loaded from multiple sources:
#
# 1. Local file:
#    python -m amibot -c /path/to/config.yaml
#
# 2. AWS S3:
#    python -m amibot -c s3://bucket-name/path/to/config.yaml
#
# 3. Cloudflare KV:
#    python -m amibot -c kv://<account_id>/<namespace_id>/<key>
#    Requires: CLOUDFLARE_API_TOKEN environment variable
#
# For Cloudflare KV setup:
# 1. Create KV namespace: wrangler kv:namespace create "amibot-config"
# 2. Upload config: wrangler kv:key put --namespace-id=<id> "production" config.yaml
# 3. Get account ID from Cloudflare dashboard
# 4. Set CLOUDFLARE_API_TOKEN in environment
# 5. Run: python -m amibot -c "kv://<account>/<namespace>/production"

# ... rest of existing config ...
```

### 6. Update Deployment Scripts

**File**: `scripts/start.sh`

**Add environment variable passthrough** (after line 10):
```bash
#!/usr/bin/env bash

# Container startup script for AmiBot
# Usage: ./start.sh <config_location>

set -e

CONFIG_LOCATION=${1:-"file:/nonexistent/configs/amibot.conf"}

echo "AmiBot Container Starting..."
echo "Configuration: $CONFIG_LOCATION"

# Detect configuration source
if [[ $CONFIG_LOCATION == kv://* ]]; then
    echo "Using Cloudflare KV configuration"

    # Validate required environment variables
    if [ -z "$CLOUDFLARE_API_TOKEN" ] && [ -z "$CLOUDFLARE_API_KEY" ]; then
        echo "ERROR: Cloudflare credentials not found!"
        echo "Set CLOUDFLARE_API_TOKEN or (CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL)"
        exit 1
    fi

    echo "Cloudflare credentials detected"
fi

# Start AmiBot
exec python -m amibot -c "$CONFIG_LOCATION"
```

### 7. Update Kubernetes Deployment

**File**: `deployment/kubernetes/release.yaml`

**Add environment variables for KV**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: amibot
  namespace: development
  labels:
    app: amibot
spec:
  containers:
  - name: amibot
    image: registry.gitlab.com/donrudo/amibot:0.0.6.0
    imagePullPolicy: Always

    # Environment variables for Cloudflare KV
    env:
    - name: CLOUDFLARE_API_TOKEN
      valueFrom:
        secretKeyRef:
          name: cloudflare-credentials
          key: api-token
          optional: true

    # Command with KV config (example)
    # Uncomment and modify for KV usage
    # command: ["python", "-m", "amibot"]
    # args: ["-c", "kv://$(ACCOUNT_ID)/$(NAMESPACE_ID)/production"]

    # For file-based config (existing behavior)
    volumeMounts:
    - name: config
      mountPath: /nonexistent/configs
      readOnly: true

    ports:
    - containerPort: 23459
      name: health
      protocol: TCP

    livenessProbe:
      httpGet:
        path: /liveness
        port: 23459
      initialDelaySeconds: 30
      periodSeconds: 10

    readinessProbe:
      httpGet:
        path: /readiness
        port: 23459
      initialDelaySeconds: 5
      periodSeconds: 5

  # File-based config volume (existing)
  volumes:
  - name: config
    configMap:
      name: amibot-config

  dnsPolicy: ClusterFirstWithHostNet
  restartPolicy: Always
```

**Create Secret for Cloudflare credentials**:

**File**: `deployment/kubernetes/cloudflare-secret.yaml.example` (NEW)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-credentials
  namespace: development
type: Opaque
stringData:
  api-token: "your_cloudflare_api_token_here"
  # Optional: for legacy API key auth
  # api-key: "your_api_key"
  # email: "your_email@example.com"
```

### 8. Update AWS ECS Deployment

**File**: `deployment/cloud/aws/ecs.tf`

**Add environment variables to task definition** (in `container_definitions`):
```hcl
container_definitions = jsonencode([
  {
    name      = var.ecs_service
    image     = "${var.image}:${var.image_version}"
    essential = true

    # Add Cloudflare KV environment variables
    environment = [
      {
        name  = "CLOUDFLARE_ACCOUNT_ID"
        value = var.cloudflare_account_id  # Add to variables.tf
      },
      {
        name  = "CLOUDFLARE_NAMESPACE_ID"
        value = var.cloudflare_namespace_id  # Add to variables.tf
      }
    ]

    # Add secret for API token (stored in AWS Secrets Manager)
    secrets = [
      {
        name      = "CLOUDFLARE_API_TOKEN"
        valueFrom = aws_secretsmanager_secret.cloudflare_token.arn
      }
    ]

    # ... rest of existing config ...
  }
])
```

**Add Secrets Manager resource**:
```hcl
# Cloudflare API Token secret
resource "aws_secretsmanager_secret" "cloudflare_token" {
  name        = "${var.ecs_service}-cloudflare-token-${var.env}"
  description = "Cloudflare API token for KV access"
}

resource "aws_secretsmanager_secret_version" "cloudflare_token" {
  secret_id     = aws_secretsmanager_secret.cloudflare_token.id
  secret_string = var.cloudflare_api_token
}
```

**File**: `deployment/cloud/aws/variables.tf`

**Add new variables**:
```hcl
variable "cloudflare_account_id" {
  description = "Cloudflare account ID for KV access"
  type        = string
  default     = ""
}

variable "cloudflare_namespace_id" {
  description = "Cloudflare KV namespace ID"
  type        = string
  default     = ""
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token (stored in Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}
```

**File**: `deployment/cloud/aws/iam.tf`

**Add Secrets Manager permissions**:
```hcl
# Update task execution role policy
resource "aws_iam_role_policy" "task_execution" {
  name = "${var.ecs_service}-task-execution-${var.env}"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ... existing S3 permissions ...

      # Add Secrets Manager permissions
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.cloudflare_token.arn
        ]
      }
    ]
  })
}
```

---

## Configuration Schema

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CLOUDFLARE_API_TOKEN` | Yes* | API token with KV read permissions | `v1.0-abc123...` |
| `CLOUDFLARE_API_KEY` | Yes** | Global API key (legacy) | `abc123def456...` |
| `CLOUDFLARE_EMAIL` | Yes** | Account email (legacy) | `user@example.com` |

*Required if not using API key authentication
**Required if not using API token authentication

### URI Format

```
kv://<account_id>/<namespace_id>/<key>
```

**Components**:
- `account_id`: Cloudflare account ID (from dashboard)
- `namespace_id`: KV namespace ID (from `wrangler kv:namespace list`)
- `key`: Key name in KV storage (can contain slashes)

**Examples**:
```bash
# Production config
kv://abc123def456/9a7b8c6d5e4f/production

# Development config
kv://abc123def456/1a2b3c4d5e6f/development

# Key with slashes
kv://abc123def456/9a7b8c6d5e4f/configs/amibot/prod
```

### Configuration Content Format

The value stored in Cloudflare KV must be valid YAML or JSON matching the existing AmiBot configuration schema:

**YAML Example** (stored in KV):
```yaml
amibot:
  username: "amigo"
  system_role: |
    You are a helpful assistant.

discord:
  enabled: true
  application_id: "1234567890"
  public_key: "abc123..."
  token: "Bot xyz789..."

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

**JSON Example** (stored in KV):
```json
{
  "amibot": {
    "username": "amigo",
    "system_role": "You are a helpful assistant."
  },
  "discord": {
    "enabled": true,
    "application_id": "1234567890",
    "public_key": "abc123...",
    "token": "Bot xyz789..."
  },
  "llm": {
    "provider": "anthropic",
    "enabled": true,
    "model": "claude-3-5-sonnet-20240620",
    "key": "sk-ant-...",
    "tokens_range": {
      "from": 256,
      "until": 4096,
      "increment": 256
    }
  }
}
```

---

## Dependencies

### New Python Packages

**Add to `requirements.txt`**:
```txt
requests>=2.31.0,<3.0.0
python-dotenv>=1.0.0,<2.0.0  # Optional, for .env file support
```

### Cloudflare Setup

**Prerequisites**:
1. Cloudflare account
2. KV namespace created
3. API token with permissions:
   - Account > Workers KV Storage > Read

**Creating API Token** (Recommended):
```bash
# Via Cloudflare Dashboard:
# 1. Go to: https://dash.cloudflare.com/profile/api-tokens
# 2. Click "Create Token"
# 3. Use "Edit Cloudflare Workers" template
# 4. Modify permissions to "Account > Workers KV Storage > Read"
# 5. Set account and namespace restrictions
# 6. Create token and save securely
```

**Using Global API Key** (Legacy):
```bash
# Via Cloudflare Dashboard:
# 1. Go to: https://dash.cloudflare.com/profile/api-tokens
# 2. Scroll to "API Keys" section
# 3. View "Global API Key"
# 4. Use with your account email
```

### Wrangler CLI (Optional)

For managing KV namespaces:

```bash
# Install Wrangler
npm install -g wrangler

# Authenticate
wrangler login

# Create namespace
wrangler kv:namespace create "amibot-config"

# List namespaces
wrangler kv:namespace list

# Upload configuration
wrangler kv:key put \
  --namespace-id=<namespace_id> \
  "production" \
  --path=configs/amibot.conf

# Get configuration
wrangler kv:key get \
  --namespace-id=<namespace_id> \
  "production"

# Delete key
wrangler kv:key delete \
  --namespace-id=<namespace_id> \
  "production"
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_configloader_cloudflare_kv.py` (NEW)

```python
import unittest
from unittest.mock import patch, Mock
import os
import yaml

from amibot.configloader.FromCloudflareKV import FromCloudflareKV


class TestFromCloudflareKV(unittest.TestCase):
    """Test cases for Cloudflare KV configuration loader."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_uri = "kv://abc123/ns-456/production"
        self.test_config = {
            'amibot': {
                'username': 'testbot',
                'system_role': 'Test role'
            },
            'llm': {
                'provider': 'openai',
                'enabled': True,
                'model': 'gpt-4',
                'key': 'sk-test',
                'tokens_range': {
                    'from': 256,
                    'until': 4096,
                    'increment': 256
                }
            }
        }

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    def test_uri_parsing(self):
        """Test URI parsing logic."""
        loader = FromCloudflareKV(self.valid_uri)

        self.assertEqual(loader._account_id, 'abc123')
        self.assertEqual(loader._namespace_id, 'ns-456')
        self.assertEqual(loader._key, 'production')

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    def test_uri_with_slash_in_key(self):
        """Test URI with slashes in key name."""
        uri = "kv://abc123/ns-456/configs/prod/v1"
        loader = FromCloudflareKV(uri)

        self.assertEqual(loader._key, 'configs/prod/v1')

    def test_missing_credentials(self):
        """Test error when credentials are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                FromCloudflareKV(self.valid_uri)

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    def test_invalid_uri_scheme(self):
        """Test error on invalid URI scheme."""
        with self.assertRaises(ValueError):
            FromCloudflareKV("s3://bucket/key")

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    def test_invalid_uri_format(self):
        """Test error on malformed URI."""
        with self.assertRaises(ValueError):
            FromCloudflareKV("kv://abc123/missing-key")

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    @patch('amibot.configloader.FromCloudflareKV.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful configuration fetch."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = yaml.dump(self.test_config)
        mock_get.return_value = mock_response

        loader = FromCloudflareKV(self.valid_uri)
        config = loader.configuration

        self.assertIsNotNone(config)
        self.assertEqual(config['amibot']['username'], 'testbot')

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    @patch('amibot.configloader.FromCloudflareKV.requests.get')
    def test_404_not_found(self, mock_get):
        """Test handling of missing key."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        loader = FromCloudflareKV(self.valid_uri)
        config = loader.configuration

        self.assertIsNone(config)

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    @patch('amibot.configloader.FromCloudflareKV.requests.get')
    def test_authentication_failure(self, mock_get):
        """Test handling of auth errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        loader = FromCloudflareKV(self.valid_uri)
        config = loader.configuration

        self.assertIsNone(config)

    @patch.dict(os.environ, {'CLOUDFLARE_API_TOKEN': 'test-token'})
    @patch('amibot.configloader.FromCloudflareKV.requests.get')
    def test_retry_on_timeout(self, mock_get):
        """Test retry logic on timeout."""
        # First two calls timeout, third succeeds
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            Mock(status_code=200, text=yaml.dump(self.test_config))
        ]

        loader = FromCloudflareKV(self.valid_uri)
        config = loader.configuration

        self.assertIsNotNone(config)
        self.assertEqual(mock_get.call_count, 3)


if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

**Manual Testing Checklist**:

- [ ] Create Cloudflare KV namespace
- [ ] Upload test configuration to KV
- [ ] Set CLOUDFLARE_API_TOKEN environment variable
- [ ] Run: `python -m amibot -c "kv://<account>/<namespace>/test"`
- [ ] Verify bot starts successfully
- [ ] Verify configuration loaded correctly (check logs)
- [ ] Test with invalid credentials (should fail gracefully)
- [ ] Test with non-existent key (should fail gracefully)
- [ ] Test with malformed config (should fail gracefully)
- [ ] Test with network connectivity issues

### Load Testing

**Test Cloudflare KV Rate Limits**:

```bash
# Simulate 100 concurrent config loads
for i in {1..100}; do
  python -m amibot -c "kv://account/namespace/test" &
done
wait
```

**Expected Behavior**:
- All requests should succeed (KV has high rate limits)
- Response time should be <100ms for most requests
- No 429 rate limit errors

---

## Deployment Considerations

### Environment Variable Management

**Local Development**:
```bash
# Use .env file
cp .env.example .env
# Edit .env with your credentials
source .env
python -m amibot -c "kv://..."
```

**Docker**:
```bash
docker run -d \
  --name amibot \
  -e CLOUDFLARE_API_TOKEN="your_token" \
  -p 23459:23459 \
  amibot:latest \
  -c "kv://account/namespace/production"
```

**Docker Compose**:
```yaml
version: '3.8'
services:
  amibot:
    image: registry.gitlab.com/donrudo/amibot:0.0.7
    environment:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
    command: ["-c", "kv://account/namespace/production"]
    ports:
      - "23459:23459"
    restart: unless-stopped
```

**Kubernetes**:
```bash
# Create secret
kubectl create secret generic cloudflare-credentials \
  -n development \
  --from-literal=api-token="your_token"

# Update deployment to use KV
kubectl set env deployment/amibot \
  -n development \
  CLOUDFLARE_API_TOKEN="secretKeyRef:cloudflare-credentials:api-token"

# Update args
kubectl patch deployment amibot -n development \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": ["-c", "kv://account/namespace/production"]}]'
```

**AWS ECS**:
- Store API token in AWS Secrets Manager
- Reference in task definition (see source code changes above)
- Pass account ID and namespace ID as environment variables

### Multi-Environment Strategy

**Namespace Separation**:
```bash
# Create environment-specific namespaces
wrangler kv:namespace create "amibot-dev"
wrangler kv:namespace create "amibot-staging"
wrangler kv:namespace create "amibot-prod"

# Upload configs
wrangler kv:key put --namespace-id=<dev-id> "config" --path=configs/dev.yaml
wrangler kv:key put --namespace-id=<staging-id> "config" --path=configs/staging.yaml
wrangler kv:key put --namespace-id=<prod-id> "config" --path=configs/prod.yaml
```

**Environment-Specific Tokens**:
```bash
# Create separate API tokens per environment
# Dev: Read access to dev namespace only
# Staging: Read access to staging namespace only
# Prod: Read access to prod namespace only
```

### Configuration Updates

**Zero-Downtime Updates**:

1. **Update config in KV**:
   ```bash
   wrangler kv:key put \
     --namespace-id=<id> \
     "production" \
     --path=configs/new-config.yaml
   ```

2. **Restart bot** (config is cached, requires restart):
   ```bash
   # Kubernetes
   kubectl rollout restart deployment/amibot -n development

   # Docker
   docker restart amibot

   # ECS
   aws ecs update-service \
     --cluster botfarm \
     --service amibot \
     --force-new-deployment
   ```

**Configuration Versioning**:

```bash
# Use versioned keys
wrangler kv:key put --namespace-id=<id> "config-v1" --path=v1.yaml
wrangler kv:key put --namespace-id=<id> "config-v2" --path=v2.yaml

# Deploy with specific version
python -m amibot -c "kv://account/namespace/config-v2"

# Rollback if needed
python -m amibot -c "kv://account/namespace/config-v1"
```

### Monitoring

**Cloudflare Analytics**:
- View KV request metrics in Cloudflare dashboard
- Monitor read/write operations
- Track storage usage

**Application Logging**:
```python
# Add metrics logging in FromCloudflareKV
import time

start = time.time()
content = self._fetch_from_kv()
duration = time.time() - start

logger.info(f"KV fetch took {duration:.2f}s")
```

**Health Check Implications**:
- Health checks still work (don't depend on config source)
- `/readiness` verifies bot is ready regardless of config source
- No changes needed to health check endpoints

---

## Security Considerations

### Authentication

**API Token Best Practices**:
1. **Use API Tokens** (not Global API Key)
2. **Minimum Permissions**: Account > Workers KV Storage > Read
3. **Scope to Specific Namespaces**: Limit access in token settings
4. **Rotate Regularly**: Set expiration, rotate every 90 days
5. **Never Commit**: Add to .gitignore, use secret management

**Token Scoping Example**:
```
Token Name: amibot-kv-read-production
Permissions:
  Account > Workers KV Storage > Read
Resources:
  Account: <your-account>
  Include: <production-namespace-id>
TTL: 90 days
```

### Data Security

**Configuration Encryption**:
- **At Rest**: Cloudflare encrypts KV data at rest
- **In Transit**: All API calls use HTTPS
- **In Memory**: Configuration cached in bot memory (ephemeral)

**Secrets Management**:
```yaml
# DON'T store directly in KV:
llm:
  key: "sk-ant-actual-secret-key"

# DO store reference to secret:
llm:
  key: "${AWS_SECRETS_MANAGER:amibot/llm/key}"
  # OR
  key: "${VAULT:secret/data/amibot/llm/key}"
```

**Future Enhancement**: Add secret reference resolution in ConfigLoader.

### Access Control

**Namespace Isolation**:
- Separate namespaces per environment
- Use different API tokens per environment
- Restrict token permissions to specific namespaces

**Audit Logging**:
```python
# Log all config access
logger.info(f"Configuration accessed by {os.getenv('USER')} from {socket.gethostname()}")
logger.info(f"KV: account={account_id}, namespace={namespace_id}, key={key}")
```

### Network Security

**Firewall Rules**:
- Allow outbound HTTPS to `api.cloudflare.com`
- No inbound rules needed (bot initiates request)

**VPC Considerations** (AWS):
- VPC endpoint not available for Cloudflare API
- Requires NAT Gateway or Internet Gateway
- Security group: Allow outbound HTTPS (443)

**mTLS** (Future Enhancement):
- Cloudflare supports client certificates
- Add client cert validation in `_get_auth_headers()`

---

## Migration Path

### From File-Based Configuration

**Current**:
```bash
python -m amibot -c /path/to/config.yaml
```

**Migration Steps**:

1. **Create KV Namespace**:
   ```bash
   wrangler kv:namespace create "amibot-config"
   # Output: { id: "abc123...", title: "amibot-config" }
   ```

2. **Upload Configuration**:
   ```bash
   wrangler kv:key put \
     --namespace-id=abc123 \
     "production" \
     --path=/path/to/config.yaml
   ```

3. **Get Account ID**:
   - Login to Cloudflare Dashboard
   - Navigate to Workers & Pages
   - Copy Account ID from URL or sidebar

4. **Create API Token**:
   - Dashboard → Profile → API Tokens
   - Create Token → Custom Token
   - Permissions: Account > Workers KV Storage > Read
   - Save token securely

5. **Test Locally**:
   ```bash
   export CLOUDFLARE_API_TOKEN="your_token"
   python -m amibot -c "kv://account_id/abc123/production"
   ```

6. **Update Deployment**:
   - Add token to deployment secrets
   - Update start command to use KV URI
   - Deploy and verify

### From S3 Configuration

**Current**:
```bash
python -m amibot -c s3://bucket/path/to/config.yaml
```

**Why Migrate to KV?**
- **Lower Latency**: 10-50ms vs 50-200ms for S3
- **Lower Cost**: $0.50/million reads vs $0.40/million for S3
- **Global Distribution**: Edge network vs regional S3 buckets
- **Simpler Auth**: Token vs AWS credentials + IAM roles

**Migration Steps**:

1. **Download from S3**:
   ```bash
   aws s3 cp s3://bucket/path/to/config.yaml ./config.yaml
   ```

2. **Upload to KV**:
   ```bash
   wrangler kv:key put \
     --namespace-id=abc123 \
     "production" \
     --path=./config.yaml
   ```

3. **Update Deployment**:
   ```bash
   # Old
   python -m amibot -c "s3://bucket/path/to/config.yaml"

   # New
   python -m amibot -c "kv://account/namespace/production"
   ```

4. **Update IAM/Secrets**:
   - Remove S3 IAM permissions
   - Add Cloudflare token to secrets
   - Update environment variables

### Gradual Rollout

**Blue-Green Deployment**:

1. **Deploy KV version** (green) alongside existing (blue)
2. **Test KV version** with canary traffic (10%)
3. **Increase KV traffic** gradually (25%, 50%, 75%)
4. **Switch fully to KV** (100%)
5. **Deprecate old version** after monitoring period

**Kubernetes Example**:
```bash
# Deploy KV version with different label
kubectl apply -f deployment-kv.yaml  # app=amibot-kv

# Route 10% traffic to KV version
kubectl apply -f service-canary.yaml

# Monitor logs and metrics
kubectl logs -l app=amibot-kv --tail=100 -f

# Increase traffic over time
kubectl patch service amibot --type='json' -p='...'

# Full cutover
kubectl delete deployment amibot  # old version
kubectl label deployment amibot-kv app=amibot  # rename
```

---

## Future Enhancements

### 1. Configuration Caching with TTL

**Problem**: Every bot restart fetches from KV.

**Solution**: Add TTL-based caching with background refresh.

```python
class FromCloudflareKV(ConfigLoader):
    def __init__(self, uri: str, cache_ttl: int = 300):
        # ...
        self._cache_ttl = cache_ttl
        self._last_fetch = None
        self._cache_task = None

    async def _refresh_cache(self):
        """Background task to refresh config every TTL seconds."""
        while True:
            await asyncio.sleep(self._cache_ttl)
            logger.info("Refreshing configuration from KV")
            self._config = None  # Invalidate cache
            self.configuration  # Re-fetch
```

### 2. Secret Reference Resolution

**Problem**: API keys stored in plaintext in config.

**Solution**: Support secret references.

```yaml
# Config in KV
llm:
  key: "${AWS_SECRETS_MANAGER:amibot/llm/key}"
  # or
  key: "${CLOUDFLARE_SECRETS:llm-api-key}"
```

```python
def _resolve_secrets(self, config: dict) -> dict:
    """Recursively resolve secret references in config."""
    import re

    secret_pattern = r'\$\{(\w+):(.+)\}'

    def resolve_value(value):
        if isinstance(value, str):
            match = re.match(secret_pattern, value)
            if match:
                provider, key = match.groups()
                return self._fetch_secret(provider, key)
        return value

    # Recursively process dict
    # ...
```

### 3. Configuration Validation Schema

**Problem**: No schema enforcement for config structure.

**Solution**: Add JSON Schema validation.

```python
import jsonschema

CONFIG_SCHEMA = {
    "type": "object",
    "required": ["amibot", "llm"],
    "properties": {
        "amibot": {
            "type": "object",
            "required": ["username", "system_role"],
            "properties": {
                "username": {"type": "string"},
                "system_role": {"type": "string"}
            }
        },
        # ...
    }
}

def _validate_configuration(self, config: dict) -> bool:
    try:
        jsonschema.validate(config, CONFIG_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False
```

### 4. Multi-Key Configuration

**Problem**: Large configs hit KV value size limit (25MB, but 10MB recommended).

**Solution**: Split config across multiple keys.

```yaml
# Key: production/amibot
amibot:
  username: "amigo"
  system_role: "..."

# Key: production/llm
llm:
  provider: "anthropic"
  # ...

# Key: production/discord
discord:
  enabled: true
  # ...
```

```python
def _fetch_multi_key_config(self, base_key: str) -> dict:
    """Fetch and merge config from multiple keys."""
    keys = ['amibot', 'llm', 'discord']
    config = {}

    for key in keys:
        full_key = f"{base_key}/{key}"
        value = self._fetch_from_kv(full_key)
        section = yaml.safe_load(value)
        config.update(section)

    return config
```

### 5. Configuration Change Notifications

**Problem**: Bot doesn't know when config changes.

**Solution**: Use Cloudflare Workers + Queues for change notifications.

```javascript
// Cloudflare Worker on config update
addEventListener('kv:put', event => {
  // Publish to queue
  await env.CONFIG_CHANGES.send({
    namespace: event.namespace,
    key: event.key,
    timestamp: Date.now()
  });
});
```

```python
# Bot subscribes to change notifications
async def watch_config_changes(self):
    """Poll for config change notifications."""
    while True:
        changes = await self._poll_queue()
        if changes:
            logger.info("Configuration changed, reloading...")
            self._config = None
            self.configuration
```

### 6. Configuration Versioning and Rollback

**Problem**: No rollback mechanism for bad configs.

**Solution**: Store config history with metadata.

```python
def put_config_with_version(config: dict, metadata: dict):
    """Store config with version metadata."""
    version = metadata['version']
    timestamp = time.time()

    # Store config
    kv.put(f"config/{version}", yaml.dump(config))

    # Store metadata
    kv.put(f"config/{version}/meta", json.dumps({
        'version': version,
        'timestamp': timestamp,
        'author': metadata['author'],
        'description': metadata['description']
    }))

    # Update 'latest' pointer
    kv.put("config/latest", version)

def rollback_config(to_version: str):
    """Rollback to previous config version."""
    kv.put("config/latest", to_version)
```

---

## Acceptance Criteria

This feature will be considered complete when:

- [ ] `FromCloudflareKV` class implemented with full error handling
- [ ] Protocol detection updated in `__main__.py`
- [ ] Dependencies added to `requirements.txt`
- [ ] Unit tests written with >80% coverage
- [ ] Integration tests pass
- [ ] Documentation updated (CLAUDE.md, README.md)
- [ ] Example configurations provided
- [ ] Kubernetes deployment examples updated
- [ ] AWS ECS deployment examples updated
- [ ] Security review completed
- [ ] Migration guide written
- [ ] Successfully tested in:
  - [ ] Local development
  - [ ] Docker container
  - [ ] Kubernetes cluster
  - [ ] AWS ECS (optional)

---

## References

### Cloudflare Documentation
- [Workers KV API Reference](https://developers.cloudflare.com/api/operations/workers-kv-namespace-read-key-value-pair)
- [Workers KV Limits](https://developers.cloudflare.com/workers/platform/limits/#kv-limits)
- [API Token Permissions](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)

### AmiBot Documentation
- [CLAUDE.md](../CLAUDE.md) - Complete codebase guide
- [README.md](../README.md) - User documentation
- [TECHNICAL_DIAGRAMS.md](TECHNICAL_DIAGRAMS.md) - Architecture diagrams

### Related Projects
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)
- [requests library](https://requests.readthedocs.io/)
- [PyYAML](https://pyyaml.org/)

---

## Appendix: Complete Example

### End-to-End Setup Example

```bash
# 1. Create KV namespace
wrangler kv:namespace create "amibot-prod"
# Output: { id: "abc123def456", title: "amibot-prod" }

# 2. Prepare configuration
cat > prod-config.yaml <<EOF
amibot:
  username: "amigo"
  system_role: |
    You are a helpful AI assistant.

discord:
  enabled: true
  application_id: "1234567890"
  public_key: "abc123..."
  token: "Bot xyz789..."

llm:
  provider: "anthropic"
  enabled: true
  model: "claude-3-5-sonnet-20240620"
  key: "sk-ant-..."
  tokens_range:
    from: 256
    until: 4096
    increment: 256
EOF

# 3. Upload to KV
wrangler kv:key put \
  --namespace-id=abc123def456 \
  "production" \
  --path=prod-config.yaml

# 4. Create API token (via dashboard)
# Save as: CLOUDFLARE_API_TOKEN=abc123...

# 5. Test locally
export CLOUDFLARE_API_TOKEN="abc123..."
python -m amibot -c "kv://your-account-id/abc123def456/production"

# 6. Deploy to Kubernetes
kubectl create secret generic cloudflare-credentials \
  -n development \
  --from-literal=api-token="abc123..."

kubectl set env deployment/amibot \
  -n development \
  CLOUDFLARE_API_TOKEN="secretKeyRef:cloudflare-credentials:api-token"

kubectl set image deployment/amibot \
  -n development \
  amibot=registry.gitlab.com/donrudo/amibot:0.0.7

kubectl patch deployment amibot \
  -n development \
  --type='json' \
  -p='[{
    "op": "add",
    "path": "/spec/template/spec/containers/0/args",
    "value": ["-c", "kv://your-account-id/abc123def456/production"]
  }]'

kubectl rollout status deployment/amibot -n development

# 7. Verify
kubectl logs -n development -l app=amibot --tail=50
curl http://amibot.development.svc.cluster.local:23459/readiness
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Status**: Ready for Review
