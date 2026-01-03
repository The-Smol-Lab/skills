# ChatGPT Apps Implementation Patterns

Detailed implementation patterns and code examples for building ChatGPT Apps.

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

## Widget Implementation

### React Widget with Hooks

```typescript
// src/lib/openai-hooks.ts
import { useState, useEffect, useCallback, useSyncExternalStore } from 'react';

type SetGlobalsEvent = CustomEvent<{ globals: Partial<Window['openai']> }>;

export function useOpenAiGlobal<K extends keyof NonNullable<Window['openai']>>(
  key: K
): NonNullable<Window['openai']>[K] | undefined {
  return useSyncExternalStore(
    (onChange) => {
      const handler = (e: SetGlobalsEvent) => {
        if (e.detail.globals[key] !== undefined) onChange();
      };
      window.addEventListener('openai:set_globals', handler as EventListener);
      return () => window.removeEventListener('openai:set_globals', handler as EventListener);
    },
    () => window.openai?.[key]
  );
}

export function useToolOutput<T>(): T | null {
  return useOpenAiGlobal('toolOutput') as T | null;
}

export function useWidgetState<T>(
  initial: T | (() => T)
): readonly [T, (next: T | ((prev: T) => T)) => void] {
  const external = useOpenAiGlobal('widgetState') as T | undefined;
  
  const [state, _setState] = useState<T>(() => 
    external ?? (typeof initial === 'function' ? (initial as () => T)() : initial)
  );

  useEffect(() => {
    if (external !== undefined) _setState(external);
  }, [external]);

  const setState = useCallback((next: T | ((prev: T) => T)) => {
    _setState(prev => {
      const value = typeof next === 'function' ? (next as (p: T) => T)(prev) : next;
      window.openai?.setWidgetState?.(value as Record<string, unknown>);
      return value;
    });
  }, []);

  return [state, setState] as const;
}

export function useToolCall() {
  return useCallback(
    (name: string, args: Record<string, unknown>) => 
      window.openai?.callTool?.(name, args),
    []
  );
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
