# AmiBot Documentation

This directory contains comprehensive technical documentation for the AmiBot project.

## Contents

### [TECHNICAL_DIAGRAMS.md](TECHNICAL_DIAGRAMS.md)

Complete set of technical diagrams documenting the system architecture, data flows, and operational patterns.

### [FEATURE_PROPOSAL_AGENT_MCP.md](FEATURE_PROPOSAL_AGENT_MCP.md)

Comprehensive feature proposal for adding custom agent and MCP bot integration capabilities.

**Includes:**

- **Class Diagrams**: Full inheritance hierarchy and relationships (including proposed AgentBot and MCPBot)
- **Sequence Diagrams**:
  - Application startup sequence
  - Message handling flow
  - Progressive token strategy
  - Configuration loading
  - Health check endpoints
  - AgentBot request/response flow (proposed)
  - MCPBot tool calling flow (proposed)
- **State Diagrams**: Bot and Discord client lifecycles
- **Data Flow Diagrams**: Conversation context and message routing
- **Deployment Architecture**: Kubernetes and AWS ECS deployments
- **Component Interaction**: System-wide component communication
- **Error Handling Patterns**: Resilience and recovery strategies
- **Proposed Features**: AgentBot and MCPBot integration diagrams

All diagrams are created using Mermaid format for easy rendering in GitHub/GitLab.

**Feature Proposal Includes:**

- **Executive Summary**: Overview of custom agent and MCP bot capabilities
- **Technical Specifications**: Detailed implementation plans for bot_agent.py and bot_mcp.py
- **Architecture Design**: How new bots integrate with existing framework
- **Configuration Schema**: Complete YAML configuration examples
- **Implementation Roadmap**: 6-week development plan
- **Use Cases**: Real-world applications and benefits
- **Testing Strategy**: Unit, integration, and manual testing approaches
- **Migration Path**: Backward compatibility and deployment guides

### [FEATURE_PROPOSAL_SLACK_SIGNAL.md](FEATURE_PROPOSAL_SLACK_SIGNAL.md)

Comprehensive feature proposal for adding Slack and Signal community platform integrations.

**Includes:**

- **Class Diagrams**: Extended Community hierarchy with Slack and Signal implementations
- **Sequence Diagrams**:
  - Slack integration message flow
  - Signal integration message flow
  - Multi-platform deployment architecture
  - Platform message flow comparison
  - Slack app configuration sequence
  - Signal setup and registration flow
- **Platform Comparisons**: Feature matrices and capability analysis
- **Configuration Patterns**: Multi-platform configuration support

**Feature Proposal Includes:**

- **Executive Summary**: Overview of multi-platform community support
- **Technical Specifications**: Complete implementation for slack_client.py and signal_client.py
- **Platform Requirements**:
  - Slack: OAuth scopes, Socket Mode, event subscriptions
  - Signal: signal-cli installation, daemon mode, registration
- **Configuration Schema**: Multi-platform YAML configurations
- **Implementation Roadmap**: 6-week development plan
- **Use Cases**: Enterprise (Slack) and privacy-focused (Signal) scenarios
- **Testing Strategy**: Unit and integration testing for both platforms
- **Setup Guides**: Platform-specific installation and configuration

## For AI Assistants

When working on AmiBot, refer to:
- **[../CLAUDE.md](../CLAUDE.md)** - Main AI assistant guide with development guidelines
- **[TECHNICAL_DIAGRAMS.md](TECHNICAL_DIAGRAMS.md)** - Visual architecture and flow diagrams

## Usage

These diagrams help with:
- Understanding system architecture
- Onboarding new contributors
- Planning new features
- Debugging issues
- Code reviews
- Documentation maintenance

## Rendering

Mermaid diagrams automatically render on:
- GitHub
- GitLab
- VS Code (with Mermaid extension)
- Many other Markdown viewers

## Maintenance

When making significant architectural changes:
1. Update the relevant diagrams in TECHNICAL_DIAGRAMS.md
2. Update code references in ../CLAUDE.md
3. Commit diagram changes alongside code changes
