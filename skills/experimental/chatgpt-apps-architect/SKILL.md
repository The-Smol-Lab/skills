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

## Sunpeak Framework

Sunpeak provides development tooling for ChatGPT Apps. Use it for:
- **Local simulator**: `sunpeak dev` replicates the ChatGPT widget environment
- **Build system**: `sunpeak build` bundles widgets
- **UI utilities**: `useMaxHeight()` and `useSafeArea()` for responsive layouts

Documentation:
- https://docs.sunpeak.ai/quickstart
- https://docs.sunpeak.ai/library/chatgpt-simulator
- https://docs.sunpeak.ai/library/mcp-server
- https://docs.sunpeak.ai/library/runtime-apis
- https://docs.sunpeak.ai/template/project-scaffold
- https://docs.sunpeak.ai/template/ui-components
- https://docs.sunpeak.ai/guides/testing
- https://docs.sunpeak.ai/guides/deployment

Note: For complex interactive widgets, use the custom hook patterns in this skill (polling + grace period). Sunpeak's simpler hooks are fine for read-only widgets.

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

**React Hook Pattern (read-only widgets):**
Use this simpler pattern only when the widget does not accept user edits. For interactive widgets, use the polling + grace period hooks in `references/implementation-patterns.md`.

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

## State Synchronization

### The Problem
When a widget accepts user edits and also receives server updates:
1. User edits widget and local state updates immediately.
2. The server responds with older data.
3. The old data overwrites the user's edit.

### The Solution: Grace Period Pattern
After any local update, ignore external state changes for 2 seconds.

```typescript
const LOCAL_UPDATE_GRACE_PERIOD_MS = 2000;
const lastLocalUpdateRef = useRef(0);

// Before updating local state
lastLocalUpdateRef.current = Date.now();

// When receiving external state
if (Date.now() - lastLocalUpdateRef.current < LOCAL_UPDATE_GRACE_PERIOD_MS) {
  return; // Skip, user just made a local change
}
```

### When to Use Each Pattern

| Widget Type | Recommended Hooks | Reason |
|:------------|:------------------|:-------|
| Read-only display | Sunpeak `useWidgetGlobal` | Simpler, event-based. |
| Interactive with edits | Polling + grace period | Prevents race conditions. |
| Persistent state needed | Polling + localStorage | Survives page reloads. |

### localStorage Fallback

Use localStorage when state must persist across page reloads:

```typescript
const cached = localStorage.getItem(`app-state:${conversationId}`);
const initial = widgetState ?? (cached ? JSON.parse(cached) : defaultState);

window.openai.setWidgetState(newState);
localStorage.setItem(`app-state:${conversationId}`, JSON.stringify(newState));
```

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
- **Complete working example**: https://github.com/krittaprot/decision-roulette/blob/main/docs/guides/master_guide.md

## Troubleshooting

### Widget does not update after tool calls
- Verify `structuredContent` is returned from the tool.
- Confirm polling is running (500ms interval recommended).
- Check that `window.openai.toolOutput` is being read.

### UI edits revert after server response
- Implement the grace period pattern (2 seconds).
- Set `lastLocalUpdateRef.current = Date.now()` before any local edit.
- Skip external state sync during the grace period.

### State lost on page reload
- Implement localStorage fallback with conversation-scoped keys.
- Use `extractConversationId()` from URL/referrer for key suffix.
- Restore from localStorage when `widgetState` is undefined.

### Tool calls from widget don't persist state
- Pass `clientKey` in tool arguments for Streamable HTTP.
- Generate a stable clientKey per conversation (stored in localStorage).
- Server should use clientKey to look up/persist state.

### Server returns stale data
- Implement fallback client key discovery on the server.
- When no clientKey provided, find most recently active non-empty state.
- Use Redis sorted sets to track activity timestamps.

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
11. [ ] Implement grace period for interactive widgets
12. [ ] Add localStorage fallback if state must persist
13. [ ] Pass clientKey for Streamable HTTP state continuity
