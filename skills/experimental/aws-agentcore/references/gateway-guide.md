# AgentCore Gateway Deployment Guide

Complete reference for deploying and managing MCP Gateways in AgentCore.

## Overview

MCP Gateways provide a managed endpoint for Model Context Protocol (MCP) servers, enabling:
- Centralized access to multiple MCP targets (Lambda functions, OpenAPI services, Smithy models)
- Built-in authentication and authorization
- Semantic search capabilities
- Automatic scaling and management

## CLI Deployment Workflow

### Step 1: Install CLI

```bash
pip install bedrock-agentcore-starter-toolkit
```

### Step 2: Create MCP Gateway

```bash
agentcore gateway create-mcp-gateway
```

**Available flags:**

| Flag | Description |
|------|-------------|
| `--region TEXT` | AWS region (defaults to us-west-2) |
| `--name TEXT` | Name of the gateway (defaults to TestGateway) |
| `--role-arn TEXT` | IAM role ARN (creates one if not provided) |
| `--authorizer-config TEXT` | Serialized authorizer config JSON |
| `--enable_semantic_search` | Enable semantic search tool (default: True) |
| `-sem` | Short flag for --enable_semantic_search |

**Example:**

```bash
agentcore gateway create-mcp-gateway --name MyGateway --region us-east-1
```

### Step 3: Add Gateway Targets

Create targets to connect your gateway to actual services.

#### A. Lambda Target (Default)

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn arn:aws:bedrock-agentcore:region:account:gateway/gateway-id \
    --gateway-url https://gateway-url \
    --role-arn arn:aws:iam::account:role/role-name \
    --name MyLambdaTarget \
    --target-type lambda
```

#### B. OpenAPI Schema Target

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn arn:aws:bedrock-agentcore:region:account:gateway/gateway-id \
    --gateway-url https://gateway-url \
    --role-arn arn:aws:iam::account:role/role-name \
    --name MyAPITarget \
    --target-type openApiSchema \
    --target-payload '{"openApiSchema": {"uri": "https://api.example.com/openapi.json"}}' \
    --credentials '{"api_key": "your-api-key", "credential_location": "header", "credential_parameter_name": "X-API-Key"}'
```

#### C. Smithy Model Target

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn arn:aws:bedrock-agentcore:region:account:gateway/gateway-id \
    --gateway-url https://gateway-url \
    --role-arn arn:aws:iam::account:role/role-name \
    --name MySmithyTarget \
    --target-type smithyModel
```

**Available flags for create-mcp-gateway-target:**

| Flag | Description |
|------|-------------|
| `--gateway-arn TEXT` | ARN of the created gateway (required) |
| `--gateway-url TEXT` | URL of the created gateway (required) |
| `--role-arn TEXT` | IAM role ARN of the gateway (required) |
| `--region TEXT` | AWS region (defaults to us-west-2) |
| `--name TEXT` | Name of the target (defaults to TestGatewayTarget) |
| `--target-type TEXT` | Type: 'lambda', 'openApiSchema', 'mcpServer', or 'smithyModel' |
| `--target-payload TEXT` | Target specification JSON (required for openApiSchema) |
| `--credentials TEXT` | Credentials JSON for target access |

## Management Commands

### List Gateways

```bash
agentcore gateway list-mcp-gateways
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--region TEXT` | AWS region |
| `--name TEXT` | Filter by gateway name |
| `--max-results INTEGER` | Maximum results (default: 50, max: 1000) |

### Get Gateway Details

```bash
agentcore gateway get-mcp-gateway --name MyGateway
# OR
agentcore gateway get-mcp-gateway --id gateway-id
# OR
agentcore gateway get-mcp-gateway --arn arn:aws:bedrock-agentcore:...
```

### List Gateway Targets

```bash
agentcore gateway list-mcp-gateway-targets --name MyGateway
```

### Get Target Details

```bash
agentcore gateway get-mcp-gateway-target --name MyGateway --target-name MyTarget
```

## Cleanup Commands

### Delete Gateway Target

```bash
agentcore gateway delete-mcp-gateway-target --name MyGateway --target-name MyTarget
```

### Delete Gateway

```bash
agentcore gateway delete-mcp-gateway --name MyGateway
```

**Note:** Gateway must have zero targets before deletion, unless `--force` is used.

**Flags:**

| Flag | Description |
|------|-------------|
| `--region TEXT` | AWS region |
| `--id TEXT` | Gateway ID to delete |
| `--name TEXT` | Gateway name to delete |
| `--arn TEXT` | Gateway ARN to delete |
| `--force` | Delete all targets before deleting the gateway |

## Authentication & Authorization

### Automatic Setup

- CLI automatically creates Cognito User Pool and OAuth2 configuration
- Uses client credentials flow for machine-to-machine authentication
- Creates resource server with 'invoke' scope

### Manual Configuration

Provide `--authorizer-config` with custom JWT authorizer configuration:

```json
{
  "customJWTAuthorizer": {
    "allowedClients": ["client-id"],
    "discoveryUrl": "https://..."
  }
}
```

## Credential Providers for OpenAPI Targets

### API Key Authentication

```json
{
  "api_key": "your-api-key",
  "credential_location": "header",
  "credential_parameter_name": "X-API-Key"
}
```

### OAuth2 Authentication (Custom)

```json
{
  "oauth2_provider_config": {
    "customOauth2ProviderConfig": {
      "oauthDiscovery": {
        "discoveryUrl": "https://auth.example.com/.well-known/openid-configuration"
      },
      "clientId": "your-client-id",
      "clientSecret": "your-client-secret"
    }
  },
  "scopes": ["read", "write"]
}
```

### OAuth2 Authentication (Google)

```json
{
  "oauth2_provider_config": {
    "googleOauth2ProviderConfig": {
      "clientId": "your-google-client-id",
      "clientSecret": "your-google-client-secret"
    }
  },
  "scopes": ["https://www.googleapis.com/auth/userinfo.email"]
}
```

## Target Types

### Lambda Target

- Automatically creates test Lambda function if no target payload provided
- Requires Lambda invoke permissions on gateway execution role
- Supports custom Lambda ARN and tool schema configuration

### OpenAPI Schema Target

- Requires target payload with OpenAPI specification URI
- Supports API key and OAuth2 authentication
- Automatically creates credential providers

### MCP Server Target

- Connects to existing MCP servers
- Enables integration with external MCP-compatible services
- Requires appropriate authentication configuration

### Smithy Model Target

- Uses pre-configured Smithy models (e.g., DynamoDB)
- Automatically selects appropriate model for region
- No additional configuration required

## Common Patterns

### Complete Gateway Setup

```bash
# 1. Create gateway
agentcore gateway create-mcp-gateway --name ProductionGateway --region us-east-1

# 2. Add Lambda target
agentcore gateway create-mcp-gateway-target \
    --gateway-arn <gateway-arn> \
    --gateway-url <gateway-url> \
    --role-arn <role-arn> \
    --name LambdaProcessor \
    --target-type lambda

# 3. Add API target
agentcore gateway create-mcp-gateway-target \
    --gateway-arn <gateway-arn> \
    --gateway-url <gateway-url> \
    --role-arn <role-arn> \
    --name ExternalAPI \
    --target-type openApiSchema \
    --target-payload '{"openApiSchema": {"uri": "https://api.example.com/openapi.json"}}' \
    --credentials '{"api_key": "key123", "credential_location": "header", "credential_parameter_name": "Authorization"}'
```

### Gateway Cleanup

```bash
# Option 1: Delete targets individually, then gateway
agentcore gateway list-mcp-gateway-targets --name ProductionGateway
agentcore gateway delete-mcp-gateway-target --name ProductionGateway --target-name LambdaProcessor
agentcore gateway delete-mcp-gateway-target --name ProductionGateway --target-name ExternalAPI
agentcore gateway delete-mcp-gateway --name ProductionGateway

# Option 2: Force delete gateway and all targets at once
agentcore gateway delete-mcp-gateway --name ProductionGateway --force
```

## Key Points

- Gateways provide centralized MCP endpoint management
- Multiple target types supported (Lambda, OpenAPI, Smithy)
- Automatic authentication setup with Cognito
- Semantic search enabled by default
- Region defaults to us-west-2
- Gateway must be empty (no targets) before deletion unless --force
- IAM roles and Cognito resources created automatically if not provided
