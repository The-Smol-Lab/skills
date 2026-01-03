# AgentCore Runtime Deployment Guide

Complete reference for deploying and managing agents in AgentCore Runtime.

## Deployment Requirements

Before deploying to AgentCore Runtime, your agent code must follow this structure:

### Required Code Pattern

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

### Required Files

- Agent file (e.g., `agent.py`) with BedrockAgentCoreApp wrapper
- `requirements.txt` with all dependencies

### Key Patterns

- Import `BedrockAgentCoreApp` from `bedrock_agentcore.runtime`
- Initialize with `app = BedrockAgentCoreApp()`
- Use `@app.entrypoint` decorator on invoke function
- Call `app.run()` to let AgentCore control execution

## Pre-Deployment Validation Checklist

**Required checks:**
- [ ] Python file imports `BedrockAgentCoreApp`: `from bedrock_agentcore import BedrockAgentCoreApp`
- [ ] App is initialized: `app = BedrockAgentCoreApp()`
- [ ] Entrypoint function has `@app.entrypoint` decorator
- [ ] App runs at the end: `if __name__ == "__main__": app.run()`
- [ ] `requirements.txt` exists and includes:
  - `bedrock-agentcore` (REQUIRED)
  - Your agent framework (e.g., `strands-agents`)
  - All other dependencies (e.g., `strands-agents-tools`)

**Common mistakes:**
- Missing `BedrockAgentCoreApp` import
- Missing `@app.entrypoint` decorator
- Missing `app.run()` call
- `requirements.txt` missing `bedrock-agentcore`
- Using `strands-tools` instead of `strands-agents-tools`
- Using `strands` instead of `strands-agents`

## CLI Command Reference

### Install CLI

```bash
pip install bedrock-agentcore-starter-toolkit
```

### Configure Agent

```bash
agentcore configure --entrypoint agent.py --non-interactive
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--entrypoint, -e TEXT` | Python file of agent (required) |
| `--name, -n TEXT` | Agent name (defaults to Python file name) |
| `--execution-role, -er TEXT` | IAM execution role ARN |
| `--code-build-execution-role, -cber TEXT` | CodeBuild execution role ARN |
| `--ecr, -ecr TEXT` | ECR repository name (use "auto" for automatic creation) |
| `--container-runtime, -ctr TEXT` | Container runtime (container deployment only) |
| `--deployment-type, -dt TEXT` | `direct_code_deploy` or `container` |
| `--runtime, -rt TEXT` | Python version (PYTHON_3_10 to PYTHON_3_13) |
| `--requirements-file, -rf TEXT` | Path to requirements file |
| `--disable-otel, -do` | Disable OpenTelemetry |
| `--disable-memory, -dm` | Disable memory (skip memory setup) |
| `--authorizer-config, -ac TEXT` | OAuth authorizer configuration as JSON |
| `--request-header-allowlist, -rha TEXT` | Comma-separated allowed request headers |
| `--vpc` | Enable VPC networking (requires subnets and security-groups) |
| `--subnets TEXT` | Comma-separated subnet IDs |
| `--security-groups TEXT` | Comma-separated security group IDs |
| `--idle-timeout, -it INTEGER` | Seconds before idle session terminates (60-28800) |
| `--max-lifetime, -ml INTEGER` | Maximum instance lifetime in seconds (60-28800) |
| `--verbose, -v` | Enable verbose output |
| `--region, -r TEXT` | AWS region |
| `--protocol, -p TEXT` | Agent server protocol (HTTP, MCP, or A2A) |
| `--non-interactive, -ni` | Skip prompts; use defaults |

### Deploy to AWS

```bash
agentcore launch
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--agent, -a TEXT` | Agent name |
| `--local, -l` | Build and run locally (requires Docker) |
| `--local-build, -lb` | Build locally, deploy to cloud |
| `--auto-update-on-conflict, -auc` | Update existing agent instead of failing |
| `--env, -env TEXT` | Environment variables (format: KEY=VALUE) |

### Test Deployed Agent

```bash
agentcore invoke '{"prompt": "Hello world!"}'
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--agent, -a TEXT` | Agent name |
| `--session-id, -s TEXT` | Session ID |
| `--bearer-token, -bt TEXT` | Bearer token for OAuth |
| `--local, -l` | Send request to running local agent |
| `--user-id, -u TEXT` | User ID for authorization flows |
| `--headers TEXT` | Custom headers (format: 'Header1:value,Header2:value2') |

### Check Status

```bash
agentcore status
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--agent, -a TEXT` | Agent name |
| `--verbose, -v` | Verbose JSON output |

### Manage Sessions

```bash
agentcore stop-session
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--session-id, -s TEXT` | Specific session ID to stop |
| `--agent, -a TEXT` | Agent name |

### Clean Up

```bash
agentcore destroy
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--agent, -a TEXT` | Agent name |
| `--dry-run` | Show what would be destroyed |
| `--force` | Skip confirmation prompts |
| `--delete-ecr-repo` | Also delete ECR repository |

### Additional Commands

```bash
agentcore configure list              # List all configured agents
agentcore configure set-default <name> # Set default agent
```

## Key Points

- Default deployment uses `direct_code_deploy` (no Docker required locally)
- CodeBuild handles container builds automatically in the cloud
- Memory is opt-in; configure during setup or use `--disable-memory`
- Region defaults to `us-west-2`; specify with `--region` flag
- ARM64 architecture required (handled automatically by CodeBuild)
- Configuration stored in `.bedrock_agentcore.yaml`
