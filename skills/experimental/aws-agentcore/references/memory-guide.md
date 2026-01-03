# AgentCore Memory CLI Guide

Complete reference for managing AgentCore Memory resources.

## Overview

AgentCore Memory provides persistent knowledge storage with:
- **Short-term memory (STM)**: Conversation events with automatic expiry
- **Long-term memory (LTM)**: Semantic memory strategies for facts and knowledge

## Memory Concepts

### Memory Resource

- Container for all memory data
- Has unique ID and name
- Configurable event retention (default: 90 days)
- Supports multiple memory strategies

### Memory Strategies

- **Semantic Memory**: Store and retrieve facts using vector search
- Each strategy has a name and namespace
- Example: "Facts" strategy for user preferences

## CLI Command Reference

### Create Memory Resource

```bash
agentcore memory create <name> [OPTIONS]
```

Create a new memory resource with optional LTM strategies.

**Arguments:**
- `name`: Name for the memory resource (required)

**Options:**

| Flag | Description |
|------|-------------|
| `--region, -r TEXT` | AWS region (default: session region) |
| `--description, -d TEXT` | Description for the memory |
| `--event-expiry-days, -e INT` | Event retention in days (default: 90) |
| `--strategies, -s TEXT` | JSON string of memory strategies |
| `--role-arn TEXT` | IAM role ARN for memory execution |
| `--encryption-key-arn TEXT` | KMS key ARN for encryption |
| `--wait/--no-wait` | Wait for memory to become ACTIVE (default: --wait) |
| `--max-wait INT` | Maximum wait time in seconds (default: 300) |

**Examples:**

```bash
# Create basic memory (STM only)
agentcore memory create my_agent_memory

# Create with LTM semantic strategy
agentcore memory create my_memory \
    --strategies '[{"semanticMemoryStrategy": {"name": "Facts"}}]' \
    --wait

# Create with custom retention
agentcore memory create my_memory \
    --event-expiry-days 30 \
    --description "Customer support memory"
```

**Strategy JSON Format:**

```json
[
  {
    "semanticMemoryStrategy": {
      "name": "Facts"
    }
  }
]
```

### Get Memory Details

```bash
agentcore memory get <memory_id> [OPTIONS]
```

Retrieve detailed information about a memory resource.

**Arguments:**
- `memory_id`: Memory resource ID (required)

**Options:**
- `--region, -r TEXT`: AWS region

**Output includes:**
- Memory ID and name
- Status (CREATING, ACTIVE, DELETING, etc.)
- Description and event expiry settings
- Configured strategies

### List Memory Resources

```bash
agentcore memory list [OPTIONS]
```

List all memory resources in your account.

**Options:**

| Flag | Description |
|------|-------------|
| `--region, -r TEXT` | AWS region |
| `--max-results, -n INT` | Maximum number of results (default: 100) |

**Output:** Table showing ID, Name, Status, and Strategy count

### Delete Memory Resource

```bash
agentcore memory delete <memory_id> [OPTIONS]
```

Delete a memory resource and all associated data.

**Arguments:**
- `memory_id`: Memory resource ID to delete (required)

**Options:**

| Flag | Description |
|------|-------------|
| `--region, -r TEXT` | AWS region |
| `--wait` | Wait for deletion to complete |
| `--max-wait INT` | Maximum wait time in seconds (default: 300) |

**Warning:** This permanently deletes all events and semantic memories.

### Check Memory Status

```bash
agentcore memory status <memory_id> [OPTIONS]
```

Get the current provisioning status of a memory resource.

**Arguments:**
- `memory_id`: Memory resource ID (required)

**Options:**
- `--region, -r TEXT`: AWS region

**Possible Status Values:**
- `CREATING`: Memory is being provisioned
- `ACTIVE`: Memory is ready for use
- `UPDATING`: Memory is being modified
- `DELETING`: Memory is being deleted
- `FAILED`: Memory creation/update failed

## Common Workflows

### Basic Memory Setup

```bash
agentcore memory create my_memory
```

### Memory with Semantic Search

```bash
agentcore memory create my_memory \
    --strategies '[{"semanticMemoryStrategy": {"name": "Facts"}}]' \
    --wait
```

### Check Memory Status

```bash
agentcore memory status my_memory
agentcore memory get my_memory
```

## Key Points

- Memory resources must be ACTIVE before use
- Events automatically expire based on retention policy
- Semantic strategies enable vector search capabilities
- Use `--wait` flag to ensure resources are ready before proceeding
