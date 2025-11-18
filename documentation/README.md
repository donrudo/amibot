# AmiBot Documentation

This directory contains comprehensive technical documentation for the AmiBot project.

## Contents

### [TECHNICAL_DIAGRAMS.md](TECHNICAL_DIAGRAMS.md)

Complete set of technical diagrams documenting the system architecture, data flows, and operational patterns.

**Includes:**

- **Class Diagrams**: Full inheritance hierarchy and relationships
- **Sequence Diagrams**:
  - Application startup sequence
  - Message handling flow
  - Progressive token strategy
  - Configuration loading
  - Health check endpoints
- **State Diagrams**: Bot and Discord client lifecycles
- **Data Flow Diagrams**: Conversation context and message routing
- **Deployment Architecture**: Kubernetes and AWS ECS deployments
- **Component Interaction**: System-wide component communication
- **Error Handling Patterns**: Resilience and recovery strategies

All diagrams are created using Mermaid format for easy rendering in GitHub/GitLab.

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
