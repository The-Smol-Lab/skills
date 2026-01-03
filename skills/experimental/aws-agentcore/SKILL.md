---
name: aws-agentcore
description: Guide for developing, deploying, and managing AI agents on Amazon Bedrock AgentCore. Use this skill when working with AgentCore services including Runtime (deploying agents), Memory (persistent knowledge storage), Gateway (MCP endpoints), Code Interpreter, Browser, Observability, or Identity. Triggers on questions about deploying agents to AWS, agent lifecycle management, memory integration, MCP gateways, or the agentcore CLI.
---

# AWS Bedrock AgentCore

This skill provides comprehensive guidance for building and deploying AI agents on Amazon Bedrock AgentCore - AWS's managed platform for serverless agent deployment.

## Overview

Amazon Bedrock AgentCore provides:
- **Runtime**: Serverless deployment and scaling of agents
- **Memory**: Persistent knowledge with event (STM) and semantic (LTM) memory
- **Gateway**: Transform APIs into MCP-compatible agent tools
- **Code Interpreter**: Secure code execution in isolated sandboxes
- **Browser**: Cloud-based browser for web interactions
- **Observability**: Real-time monitoring and tracing
- **Identity**: Secure authentication and access management

## Quick Start

### 1. Install the CLI

```bash
pip install bedrock-agentcore-starter-toolkit
```

### 2. Create Agent Code

Your agent must use the `BedrockAgentCoreApp` wrapper:

```python
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent  # or your framework

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload, context):
    user_message = payload.get("prompt", "Hello!")
    # Your agent logic here
    return {"result": result}

if __name__ == "__main__":
    app.run()
```

### 3. Configure and Deploy

```bash
agentcore configure --entrypoint agent.py --non-interactive
agentcore launch
agentcore invoke '{"prompt": "Hello!"}'
```

## Workflow Decision Tree

Determine the workflow based on the task:

**Deploying an agent?** → See [references/runtime-guide.md](references/runtime-guide.md)
**Setting up memory?** → See [references/memory-guide.md](references/memory-guide.md)
**Creating MCP Gateway?** → See [references/gateway-guide.md](references/gateway-guide.md)
**Need documentation lookup?** → Run `scripts/search_docs.py` or `scripts/fetch_doc.py`

## Agent Deployment Workflow

### Step 1: Validate Code Structure

Before deploying, verify your agent code:

**Required checks:**
- Python file imports `BedrockAgentCoreApp`
- App initialized: `app = BedrockAgentCoreApp()`
- Entrypoint has `@app.entrypoint` decorator
- App runs: `if __name__ == "__main__": app.run()`
- `requirements.txt` includes `bedrock-agentcore`

**Common package mistakes:**
- Use `strands-agents` not `strands`
- Use `strands-agents-tools` not `strands-tools`

### Step 2: Configure Agent

```bash
agentcore configure --entrypoint agent.py --non-interactive
```

Key options:
- `--name`: Agent name (defaults to filename)
- `--runtime`: Python version (PYTHON_3_10 to PYTHON_3_13)
- `--deployment-type`: `direct_code_deploy` (default) or `container`
- `--disable-memory`: Skip memory setup
- `--protocol`: HTTP, MCP, or A2A

### Step 3: Deploy

```bash
agentcore launch
```

Options:
- `--local`: Build and run locally (requires Docker)
- `--local-build`: Build locally, deploy to cloud
- `--auto-update-on-conflict`: Update existing agent

### Step 4: Test

```bash
agentcore invoke '{"prompt": "Test message"}'
```

### Step 5: Monitor and Manage

```bash
agentcore status              # Check deployment status
agentcore stop-session        # Stop active sessions
agentcore destroy             # Clean up resources
```

## Documentation Lookup

When you need up-to-date AgentCore documentation, use the provided scripts:

### Search Documentation

```bash
python scripts/search_docs.py "memory integration" --k 5
```

Returns ranked results with titles, URLs, scores, and snippets.

### Fetch Full Document

```bash
python scripts/fetch_doc.py "https://aws.github.io/bedrock-agentcore-starter-toolkit/..."
```

Returns complete document content.

## Resources

- **Runtime deployment**: See [references/runtime-guide.md](references/runtime-guide.md)
- **Memory management**: See [references/memory-guide.md](references/memory-guide.md)
- **Gateway setup**: See [references/gateway-guide.md](references/gateway-guide.md)
- **Live docs search**: Run `scripts/search_docs.py`
- **Document fetching**: Run `scripts/fetch_doc.py`

## Allowed Documentation Domains

The documentation tools only fetch from trusted AWS sources:
- `https://aws.github.io/bedrock-agentcore-starter-toolkit`
- `https://strandsagents.com/`
- `https://docs.aws.amazon.com/`
- `https://boto3.amazonaws.com/v1/documentation/`
