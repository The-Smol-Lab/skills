---
name: chatgpt-apps-architect
description: Architect and build ChatGPT Apps using the OpenAI Apps SDK and MCP protocol. Use when creating interactive widgets, tools, or full applications for the chatgpt.com platform. Covers --> (1) Architecture design for MCP servers, (2) Widget/UI component development, (3) Tool definition and state management, (4) Cloud deployment patterns (Cloud Run, Fly.io, etc.), (5) Planning new ChatGPT app features. Triggers on requests to build ChatGPT apps, connectors, widgets, or MCP-based integrations.
---

# ChatGPT Apps Architect

Build production-grade ChatGPT Apps using the OpenAI Apps SDK and Model Context Protocol (MCP).

## Quick Reference

**Official Documentation**: https://developers.openai.com/apps-sdk
**Examples Repository**: https://github.com/openai/openai-apps-sdk-examples
**MCP Specification**: https://modelcontextprotocol.io/specification

## Architecture Overview

ChatGPT Apps have three components that must stay in sync:

```
User prompt
   |
ChatGPT model --> MCP tool call --> Your server --> Tool response
   |                                                   |
   +---- renders narration <-- widget iframe <---------+
                           (HTML + window.openai)
```

1. **MCP Server**: Defines tools, handles auth, returns structured data, points to UI bundles
2. **Widget/UI Bundle**: React or vanilla JS rendered in ChatGPT's iframe via `window.openai`
3. **The Model**: Decides when to call tools based on your metadata

## Project Structure Pattern

```
your-chatgpt-app/
├── src/
│   ├── mcp/
│   │   └── server.ts              # MCP server entry point
│   ├── resources/
│   │   ├── {name}-resource.tsx    # React widget component
│   │   └── {name}-resource.json   # Resource metadata
│   ├── simulations/
│   │   └── {name}-simulation.ts   # Dev simulator mock data
│   ├── components/
│   │   ├── {feature}/             # Feature-specific components
│   │   └── ui/                    # Shared UI primitives
│   ├── lib/
│   │   ├── openai-hooks.ts        # window.openai React adapters
│   │   └── utils.ts               # Utilities
│   └── styles/
│       └── globals.css            # CSS variables, Tailwind config
├── Dockerfile                     # Container for Cloud Run/Fly.io
├── deploy-cloud-run.sh            # Deployment script
└── package.json
```

## Core Implementation Steps

### 1. Define Tools

Tools are the contract the model reasons about. Each tool needs:

```typescript
{
  name: 'tool-name',                    // kebab-case, unique
  title: 'Human-readable Title',
  description: 'Detailed description for LLM with examples',
  inputSchema: {
    type: 'object',
    properties: { /* JSON Schema */ },
    required: ['field'],
    additionalProperties: false,        // Keep schemas closed
  },
  annotations: {
    idempotentHint: true,               // Safe to retry
    readOnlyHint: false,                // Mutates state?
    destructiveHint: false,             // Deletes data?
  },
  _meta: {
    'openai/outputTemplate': 'ui://widget/{name}.html',
    'openai/widgetAccessible': true,    // Widget can call this tool
    'openai/toolInvocation/invoking': 'Loading...',
    'openai/toolInvocation/invoked': 'Done.',
  },
}
```

### 2. Return Structured Responses

Every tool response includes three payloads:

```typescript
return {
  // Model reads this - keep concise (<4k tokens)
  structuredContent: { items: [...], title: '...' },
  
  // Optional narration text for the model
  content: [{ type: 'text', text: 'Human-readable result' }],
  
  // Widget-only data (large/sensitive) - model never sees this
  _meta: { detailedData: {...}, lastSyncedAt: '...' },
};
```

### 3. Register Resources (Widget Templates)

```typescript
server.registerResource(
  'widget-name',
  'ui://widget/name.html',
  {},
  async () => ({
    contents: [{
      uri: 'ui://widget/name.html',
      mimeType: 'text/html+skybridge',  // Required for widget runtime
      text: `<div id="root"></div><script type="module">${JS}</script>`,
      _meta: {
        'openai/widgetPrefersBorder': true,
        'openai/widgetDomain': 'https://chatgpt.com',
        'openai/widgetCSP': {
          connect_domains: ['https://api.example.com'],
          resource_domains: ['https://*.oaistatic.com'],
        },
      },
    }],
  })
);
```

### 4. Widget Integration (window.openai)

**Read data:**
- `window.openai.toolOutput` - Your `structuredContent`
- `window.openai.toolResponseMetadata` - Your `_meta` (widget-only)
- `window.openai.widgetState` - Persisted UI state

**Write state:**
- `window.openai.setWidgetState(state)` - Persist UI state (sync call)

**Actions:**
- `window.openai.callTool(name, args)` - Invoke MCP tools from widget
- `window.openai.sendFollowUpMessage({ prompt })` - Send user message
- `window.openai.requestDisplayMode({ mode })` - Request fullscreen/PiP

**React Hook Pattern:**
```typescript
function useWidgetState<T>(initial: T | (() => T)) {
  const external = useOpenAiGlobal('widgetState') as T;
  const [state, _setState] = useState(() => external ?? (
    typeof initial === 'function' ? initial() : initial
  ));
  
  useEffect(() => { if (external) _setState(external); }, [external]);
  
  const setState = useCallback((next) => {
    _setState(prev => {
      const value = typeof next === 'function' ? next(prev) : next;
      window.openai?.setWidgetState(value);
      return value;
    });
  }, []);
  
  return [state, setState] as const;
}
```

## State Management

| Type | Owner | Lifetime | Storage |
|------|-------|----------|---------|
| Business data | MCP server/backend | Long-lived | Database |
| UI state | Widget instance | Per-message | `window.openai.widgetState` |
| Cross-session | Your backend | Persistent | Your storage layer |

**Key principle**: Widget state is scoped to a specific message. New messages = fresh widget state.

## Deployment

### Local Development
```bash
pnpm dev                  # Sunpeak simulator at localhost:6767
pnpm build && pnpm mcp:custom  # MCP server at localhost:6766
ngrok http 6766           # Expose for ChatGPT testing
```

### Production (Cloud Run)
```bash
PROJECT_ID=your-project bash deploy-cloud-run.sh
```

**With Redis for multi-instance scaling:**
```bash
PROJECT_ID=your-project REDIS_URL=rediss://... bash deploy-cloud-run.sh
```

## Before Implementation

Read these reference docs based on your needs:
- **Full patterns and code examples**: See [references/implementation-patterns.md](references/implementation-patterns.md)
- **MCP server deep dive**: https://developers.openai.com/apps-sdk/build/mcp-server
- **Widget UI guide**: https://developers.openai.com/apps-sdk/build/chatgpt-ui
- **State management**: https://developers.openai.com/apps-sdk/build/state-management
- **Authentication**: https://developers.openai.com/apps-sdk/build/auth

## Checklist for New Apps

1. [ ] Define use case and user intent triggers
2. [ ] Design tool schemas (inputs, outputs, annotations)
3. [ ] Plan widget layout and interactions
4. [ ] Implement MCP server with tools and resources
5. [ ] Build React/vanilla widget with window.openai integration
6. [ ] Create simulations for dev testing
7. [ ] Test locally with Sunpeak simulator
8. [ ] Test in ChatGPT via ngrok tunnel
9. [ ] Deploy to Cloud Run/Fly.io with HTTPS
10. [ ] Configure Redis for multi-instance (if needed)
