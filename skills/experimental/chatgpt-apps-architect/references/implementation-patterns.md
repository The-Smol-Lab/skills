# ChatGPT Apps Implementation Patterns

Detailed implementation patterns and code examples for building ChatGPT Apps.

## Sunpeak Utilities

### Responsive Layout Hooks

```typescript
import { useMaxHeight, useSafeArea } from 'sunpeak';

export function MyWidget() {
  const maxHeight = useMaxHeight();
  const safeArea = useSafeArea();

  return (
    <div
      style={{
        maxHeight: maxHeight ?? undefined,
        paddingTop: (safeArea?.insets?.top ?? 0) + 24,
        paddingBottom: (safeArea?.insets?.bottom ?? 0) + 24,
      }}
    >
      {/* content */}
    </div>
  );
}
```

### When to Use Sunpeak vs Custom Hooks

| Hook | Sunpeak | Custom (this skill) | Use When |
|:-----|:--------|:--------------------|:---------|
| Widget state | `useWidgetState` | `useWidgetState` (polling) | Custom for interactive widgets. |
| Tool output | `useWidgetGlobal('toolOutput')` | `useToolOutput` (polling) | Custom for dynamic updates. |
| Safe area | `useSafeArea` | - | Always use Sunpeak. |
| Max height | `useMaxHeight` | - | Always use Sunpeak. |
| Call tools | `useWidgetAPI().callTool` | `useToolCall` | Either works. |

## MCP Server Implementation

### Complete Server Template (TypeScript)

```typescript
import { createServer } from 'node:http';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const RESOURCE_URI = 'ui://widget/your-app';
const MCP_PATH = '/mcp';
const PORT = Number(process.env.PORT ?? 6766);

// State storage (replace with Redis for multi-instance)
const stateByClient = new Map<string, AppState>();

function getClientKey(headers: Record<string, string | undefined>): string {
  return headers['x-openai-conversation-id'] 
    ?? headers['openai-session-id']
    ?? headers['mcp-session-id']
    ?? 'default';
}

function createAppServer() {
  const server = new McpServer({ name: 'your-app', version: '1.0.0' });

  // List resources
  server.setRequestHandler(ListResourcesRequestSchema, async () => ({
    resources: [{
      uri: RESOURCE_URI,
      name: 'your-widget',
      title: 'Your Widget Title',
      description: 'Description for the model',
      mimeType: 'text/html+skybridge',
      _meta: { 'openai/widgetDomain': 'https://chatgpt.com' },
    }],
  }));

  // Read resource (return widget HTML)
  server.setRequestHandler(ReadResourceRequestSchema, async () => ({
    contents: [{
      uri: RESOURCE_URI,
      mimeType: 'text/html+skybridge',
      text: widgetHtml, // Your bundled HTML/JS/CSS
      _meta: {
        'openai/widgetPrefersBorder': true,
        'openai/widgetCSP': {
          connect_domains: ['https://your-api.com'],
          resource_domains: ['https://*.oaistatic.com'],
        },
      },
    }],
  }));

  // List tools
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: 'show-widget',
        title: 'Show Widget',
        description: 'Display the interactive widget with provided items.',
        inputSchema: {
          type: 'object',
          properties: {
            items: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of items to display',
            },
            title: { type: 'string', description: 'Widget title' },
          },
          required: ['items'],
          additionalProperties: false,
        },
        annotations: { readOnlyHint: true, idempotentHint: true },
        _meta: {
          'openai/outputTemplate': RESOURCE_URI,
          'openai/widgetAccessible': true,
          'openai/resultCanProduceWidget': true,
        },
      },
      // Add more tools...
    ],
  }));

  // Call tools
  server.setRequestHandler(CallToolRequestSchema, async (req, extra) => {
    const { name, arguments: args } = req.params;
    const clientKey = getClientKey(extra?.requestMeta ?? {});
    
    switch (name) {
      case 'show-widget': {
        const state = stateByClient.get(clientKey) ?? { items: [], title: '' };
        state.items = args.items ?? state.items;
        state.title = args.title ?? state.title;
        stateByClient.set(clientKey, state);
        
        return {
          content: [{ type: 'text', text: `Showing ${state.items.length} items` }],
          structuredContent: { items: state.items, title: state.title },
          _meta: {
            'openai/outputTemplate': RESOURCE_URI,
            'openai/widgetAccessible': true,
          },
        };
      }
      default:
        return { content: [{ type: 'text', text: `Unknown tool: ${name}` }] };
    }
  });

  return server;
}

// HTTP server setup
const httpServer = createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://${req.headers.host}`);

  // CORS preflight
  if (req.method === 'OPTIONS' && url.pathname === MCP_PATH) {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'content-type, mcp-session-id',
      'Access-Control-Expose-Headers': 'Mcp-Session-Id',
    });
    return res.end();
  }

  // Health check
  if (req.method === 'GET' && url.pathname === '/') {
    return res.writeHead(200).end('MCP Server OK');
  }

  // MCP endpoint
  if (url.pathname === MCP_PATH && ['POST', 'GET', 'DELETE'].includes(req.method!)) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Expose-Headers', 'Mcp-Session-Id');

    const server = createAppServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // stateless
      enableJsonResponse: true,
    });

    res.on('close', () => { transport.close(); server.close(); });

    await server.connect(transport);
    await transport.handleRequest(req, res);
    return;
  }

  res.writeHead(404).end('Not Found');
});

httpServer.listen(PORT, () => {
  console.log(`MCP server at http://localhost:${PORT}${MCP_PATH}`);
});
```

### Redis State Storage (Multi-Instance)

```typescript
import { createClient, RedisClientType } from 'redis';

let redis: RedisClientType | null = null;

async function getRedis(): Promise<RedisClientType | null> {
  if (!process.env.REDIS_URL) return null;
  if (redis) return redis;
  
  redis = createClient({ url: process.env.REDIS_URL });
  await redis.connect();
  return redis;
}

const PREFIX = process.env.REDIS_PREFIX ?? 'your-app';
const TTL = Number(process.env.REDIS_STATE_TTL_SECONDS ?? 7200);

async function getState<T>(key: string): Promise<T | null> {
  const client = await getRedis();
  if (!client) return stateByClient.get(key) ?? null;
  
  const data = await client.get(`${PREFIX}:${key}`);
  return data ? JSON.parse(data) : null;
}

async function setState<T>(key: string, state: T): Promise<void> {
  const client = await getRedis();
  if (!client) {
    stateByClient.set(key, state);
    return;
  }
  await client.setEx(`${PREFIX}:${key}`, TTL, JSON.stringify(state));
}
```

### Fallback Client Key Discovery (Server-Side)

When Streamable HTTP requests arrive without a clientKey, find the most recently active state.

```typescript
async function findFallbackClientKey(): Promise<string> {
  if (redis) {
    const keys = await redis.zRange(`${PREFIX}:active`, -1, -1);
    for (const key of keys.reverse()) {
      const state = await getState(key);
      if (state && state.items?.length > 0) return key;
    }
  }

  let newest = { key: 'default', time: 0 };
  for (const [key, state] of stateByClient.entries()) {
    if (state.items?.length > 0 && state.lastSeen > newest.time) {
      newest = { key, time: state.lastSeen };
    }
  }

  return newest.key;
}
```

## Widget Implementation

### React Widget with Hooks

```typescript
// src/lib/openai-hooks.ts
import { useCallback, useEffect, useRef, useState, type SetStateAction } from 'react';

const LOCAL_UPDATE_GRACE_PERIOD_MS = 2000;
const POLL_INTERVAL_MS = 500;

export function readOpenAiWidgetState<T>(): T | null {
  if (typeof window === 'undefined') return null;

  const state = window.openai?.widgetState;
  if (!state || typeof state !== 'object') return null;

  return state as T;
}

/**
 * Tool output hook with polling.
 * Use this for interactive widgets. For read-only widgets, Sunpeak's
 * useWidgetGlobal('toolOutput') is simpler.
 */
export function useToolOutput<T>(): T | null {
  const [toolOutput, setToolOutput] = useState<T | null>(() => {
    if (typeof window === 'undefined') return null;
    return (window.openai?.toolOutput as T) ?? null;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const interval = setInterval(() => {
      const currentOutput = (window.openai?.toolOutput as T) ?? null;
      if (JSON.stringify(currentOutput) !== JSON.stringify(toolOutput)) {
        setToolOutput(currentOutput);
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [toolOutput]);

  return toolOutput;
}

/**
 * Widget state hook with polling and a grace period.
 * Use this for interactive widgets to prevent race conditions.
 */
export function useWidgetState<T extends Record<string, unknown>>(
  initialState: T | (() => T)
): [T, (state: SetStateAction<T>) => void] {
  const [state, setState] = useState<T>(() =>
    typeof initialState === 'function'
      ? (initialState as () => T)()
      : initialState
  );

  const lastLocalUpdateRef = useRef<number>(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const interval = setInterval(() => {
      const timeSinceLocalUpdate = Date.now() - lastLocalUpdateRef.current;
      if (timeSinceLocalUpdate < LOCAL_UPDATE_GRACE_PERIOD_MS) {
        return;
      }

      const externalState = window.openai?.widgetState as T | undefined;
      if (externalState && JSON.stringify(externalState) !== JSON.stringify(state)) {
        setState(externalState);
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [state]);

  const setWidgetState = useCallback((nextState: SetStateAction<T>) => {
    lastLocalUpdateRef.current = Date.now();

    setState((prevState) => {
      const resolved = typeof nextState === 'function'
        ? (nextState as (prev: T) => T)(prevState)
        : nextState;

      if (typeof window !== 'undefined' && window.openai?.setWidgetState) {
        window.openai.setWidgetState(resolved);
      }

      return resolved;
    });
  }, []);

  return [state, setWidgetState];
}

export function useToolCall() {
  return useCallback(async (name: string, args: Record<string, unknown>) => {
    if (typeof window === 'undefined' || !window.openai?.callTool) {
      return null;
    }

    return window.openai.callTool(name, args);
  }, []);
}
```

## localStorage Fallback Pattern

Use localStorage when widget state must persist across page reloads.

```typescript
function extractConversationId(value: string | null): string | null {
  if (!value) return null;
  const match = value.match(/\/c\/([a-zA-Z0-9-]+)/);
  return match?.[1] ?? null;
}

function getStorageKeys() {
  const conversationId = extractConversationId(document.referrer)
    ?? extractConversationId(window.location.href);
  const suffix = conversationId ? `:${conversationId}` : '';

  return {
    clientKey: `app-client-key${suffix}`,
    state: `app-state${suffix}`,
  };
}

function initializeState<T>(defaultState: T): T {
  const widgetState = window.openai?.widgetState as T | undefined;
  if (widgetState) return widgetState;

  const keys = getStorageKeys();
  const cached = localStorage.getItem(keys.state);
  if (cached) {
    try {
      return JSON.parse(cached) as T;
    } catch {
      return defaultState;
    }
  }

  return defaultState;
}

function persistState<T>(state: T) {
  window.openai?.setWidgetState?.(state as Record<string, unknown>);

  const keys = getStorageKeys();
  localStorage.setItem(keys.state, JSON.stringify(state));
}
```

### Resource Component Pattern

```typescript
// src/resources/your-resource.tsx
import { forwardRef, useEffect } from 'react';
import { useToolOutput, useWidgetState, useToolCall } from '../lib/openai-hooks';

interface AppState {
  items: string[];
  title: string;
}

interface WidgetState {
  selectedIndex: number | null;
}

export const YourResource = forwardRef<HTMLDivElement>((_, ref) => {
  const data = useToolOutput<AppState>();
  const [widgetState, setWidgetState] = useWidgetState<WidgetState>({
    selectedIndex: null,
  });
  const callTool = useToolCall();

  const handleSelect = (index: number) => {
    setWidgetState(prev => ({ ...prev, selectedIndex: index }));
  };

  const handleRefresh = async () => {
    await callTool('refresh-items', {});
  };

  if (!data) return <div>Loading...</div>;

  return (
    <div ref={ref} className="your-widget">
      <h2>{data.title}</h2>
      <ul>
        {data.items.map((item, i) => (
          <li
            key={i}
            data-selected={widgetState.selectedIndex === i}
            onClick={() => handleSelect(i)}
          >
            {item}
          </li>
        ))}
      </ul>
      <button onClick={handleRefresh}>Refresh</button>
    </div>
  );
});
```

## Tool Aliases Pattern

Accept plural or singular variations for better LLM compatibility.

```typescript
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  switch (name) {
    case 'add-option':
    case 'add-options': {
      const items = Array.isArray(args.items) ? args.items : [args.item];
      state.items = [...state.items, ...items];
      break;
    }
    case 'remove-option':
    case 'remove-options': {
      const targets = Array.isArray(args.items) ? args.items : [args.item];
      state.items = state.items.filter((item) =>
        !targets.some((target) => target.toLowerCase() === item.toLowerCase())
      );
      break;
    }
    case 'get-option':
    case 'get-options': {
      // Read-only
      break;
    }
    default:
      break;
  }
});
```

## Removal Matching Algorithm

Use two-tier matching to handle case and whitespace differences.

```typescript
function normalizeMatchKey(value: string) {
  return value.trim().toLowerCase();
}

function normalizeLooseKey(value: string) {
  return value.replace(/\s+/g, '').toLowerCase();
}

function removeItems(items: string[], targets: string[]): string[] {
  const strictTargets = new Set(targets.map(normalizeMatchKey));
  const looseTargets = new Set(targets.map(normalizeLooseKey));

  return items.filter((item) => {
    const strictKey = normalizeMatchKey(item);
    const looseKey = normalizeLooseKey(item);
    return !strictTargets.has(strictKey) && !looseTargets.has(looseKey);
  });
}
```

## UI Component Patterns

### Button with Loading State

```typescript
function ActionButton({ onClick, children }: { onClick: () => Promise<void>; children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      await onClick();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      style={{ opacity: isLoading ? 0.6 : 1 }}
    >
      {isLoading ? 'Loading...' : children}
    </button>
  );
}
```

### Input with Widget Styling

```typescript
<input
  type="text"
  value={value}
  onChange={(e) => setValue(e.target.value)}
  style={{
    background: 'var(--widget-input-bg, #f5f5f5)',
    border: '1px solid var(--widget-border, #e0e0e0)',
    borderRadius: '8px',
    padding: '8px 12px',
    color: 'var(--widget-text, #333)',
  }}
/>
```

### Fullscreen-Aware Containers

```typescript
const containerRef = useRef<HTMLDivElement>(null);
const isFullscreen = !!document.fullscreenElement;
const effectContainer = isFullscreen ? containerRef.current : null;

triggerConfetti({ container: effectContainer });
```

### Resource Metadata

```json
// src/resources/your-resource.json
{
  "name": "your-widget",
  "title": "Your Widget Title",
  "description": "Interactive widget for your app",
  "mimeType": "text/html+skybridge",
  "_meta": {
    "openai/widgetDomain": "https://chatgpt.com"
  }
}
```

## Simulations (Dev Testing)

```typescript
// src/simulations/your-simulation.ts
import resourceMeta from '../resources/your-resource.json';

export const yourSimulation = {
  userMessage: 'Show me the widget with some example items',
  
  tool: {
    name: 'show-widget',
    title: 'Show Widget',
    description: 'Display the interactive widget',
    inputSchema: {
      type: 'object',
      properties: {
        items: { type: 'array', items: { type: 'string' } },
        title: { type: 'string' },
      },
      required: ['items'],
    },
    annotations: { readOnlyHint: true },
    _meta: {
      'openai/outputTemplate': 'ui://widget/your-widget',
      'openai/widgetAccessible': true,
    },
  },

  resource: resourceMeta,

  toolCall: {
    structuredContent: {
      items: ['Item 1', 'Item 2', 'Item 3'],
      title: 'Example Widget',
    },
    _meta: {},
  },
};
```

## Error Handling Patterns

### Tool Call Failures

```typescript
return {
  content: [{ type: 'text', text: 'Failed to update options', isError: true }],
  structuredContent: { items: state.items, title: state.title },
};
```

### Widget Error Display

```typescript
if (error) {
  return <div role="alert">{error}</div>;
}
```

## Deployment

### Dockerfile

```dockerfile
FROM node:20-slim AS base
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080

CMD ["pnpm", "mcp:custom"]
```

### Cloud Run Deploy Script

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?PROJECT_ID required}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-your-app}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID"

ARGS=(
  --image "$IMAGE"
  --platform managed
  --region "$REGION"
  --allow-unauthenticated
  --set-env-vars "MCP_TRANSPORT=streamable"
)

# Optional Redis
if [[ -n "${REDIS_URL:-}" ]]; then
  ARGS+=(--set-env-vars "REDIS_URL=${REDIS_URL}")
fi

gcloud run deploy "$SERVICE_NAME" "${ARGS[@]}" --project "$PROJECT_ID"

URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" \
  --format 'value(status.url)')

echo "Deployed: ${URL}/mcp"
```

## Tool Metadata Reference

### Annotations

| Annotation | Purpose |
|------------|---------|
| `idempotentHint` | Safe to retry without side effects |
| `readOnlyHint` | Does not modify state |
| `destructiveHint` | Permanently deletes data |
| `openWorldHint` | Schema allows additional properties |

### _meta Fields

| Field | Purpose |
|-------|---------|
| `openai/outputTemplate` | URI of widget to render |
| `openai/widgetAccessible` | Widget can call this tool |
| `openai/visibility` | `"public"` (default) or `"private"` |
| `openai/toolInvocation/invoking` | Loading message |
| `openai/toolInvocation/invoked` | Completion message |
| `openai/resultCanProduceWidget` | Tool produces widget output |
| `openai/fileParams` | Array of field names for file inputs |

### Widget CSP

```typescript
'openai/widgetCSP': {
  connect_domains: ['https://api.example.com'],  // fetch() allowed
  resource_domains: ['https://cdn.example.com'], // static assets
  redirect_domains: ['https://checkout.example.com'], // openExternal
  frame_domains: ['https://*.embed.com'], // iframes (discouraged)
}
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | Server port | `6766` |
| `MCP_TRANSPORT` | `streamable` or `sse` | `streamable` |
| `REDIS_URL` | Redis connection for multi-instance | - |
| `REDIS_PREFIX` | Key prefix | app name |
| `REDIS_STATE_TTL_SECONDS` | State expiry | `7200` |

## Testing Workflow

1. **Simulator**: `pnpm dev` - Sunpeak at localhost:6767
2. **MCP Inspector**: `npx @modelcontextprotocol/inspector http://localhost:6766/mcp`
3. **ChatGPT (dev mode)**:
   - Enable developer mode in Settings > Apps & Connectors > Advanced
   - Create connector with ngrok URL (`https://xxx.ngrok.app/mcp`)
   - Add connector to conversation via More menu

---

## Future Consideration

The production patterns in this skill (grace period sync, localStorage fallback, client key discovery) could be contributed back to Sunpeak as optional utilities for complex interactive widgets. Reference implementation:

- https://github.com/krittaprot/decision-roulette/blob/main/docs/guides/master_guide.md
