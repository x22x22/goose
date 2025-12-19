# goose SDK Examples

This directory contains SDK examples for integrating goose AI agent into your applications using various programming languages.

## Available SDKs

### Python SDK (`goose_sdk.py`)

A comprehensive Python SDK for interacting with the goose HTTP API.

**Installation:**

```bash
pip install httpx
```

**Usage:**

```python
from goose_sdk import GooseClient

async with GooseClient("http://localhost:3001", "your-secret-key") as client:
    # Start agent
    await client.start_agent(provider="openai", model="gpt-4")
    
    # Send message and get streaming response
    async for event in client.send_message("my-session", "Hello, goose!"):
        if event.message:
            for content in event.message.content:
                if content.type == "text":
                    print(content.text)
```

**Features:**
- Agent management (start, resume, update)
- Message streaming with SSE support
- Extension management (add, remove, list)
- Session management (list, get, update, delete)
- Configuration management
- Full type hints and documentation

### TypeScript/JavaScript SDK (`goose-sdk.ts`)

A TypeScript SDK that works with both Node.js and browser environments.

**Installation:**

No external dependencies required (uses native `fetch` API).

**Usage:**

```typescript
import { GooseClient } from './goose-sdk';

const client = new GooseClient('http://localhost:3001', 'your-secret-key');

// Start agent
await client.startAgent({ provider: 'openai', model: 'gpt-4' });

// Send message and get streaming response
for await (const event of client.sendMessage('my-session', 'Hello, goose!')) {
  if (event.message) {
    for (const content of event.message.content) {
      if (content.type === 'text') {
        console.log(content.text);
      }
    }
  }
}
```

**Features:**
- Agent management (start, resume, update)
- Message streaming with async generators
- Extension management (add, remove, list)
- Session management (list, get, update, delete)
- Configuration management
- Full TypeScript type definitions

## Prerequisites

Before using these SDKs, you need to:

1. **Start the goose server:**

```bash
cargo run -p goose-server -- agent
```

The server will start on `http://localhost:3001` by default.

2. **Set the authentication secret:**

```bash
export GOOSE_SERVER__SECRET_KEY="your-secret-key"
```

For development, the default is `"test"`.

## Common Use Cases

### 1. Basic Chat Session

```python
# Python
async with GooseClient() as client:
    await client.start_agent(provider="openai", model="gpt-4")
    
    async for event in client.send_message("chat-1", "Explain async/await"):
        if event.message:
            print(event.message.content[0].text)
```

```typescript
// TypeScript
const client = new GooseClient();
await client.startAgent({ provider: 'openai', model: 'gpt-4' });

for await (const event of client.sendMessage('chat-1', 'Explain async/await')) {
  if (event.message) {
    console.log(event.message.content[0].text);
  }
}
```

### 2. Managing Extensions

```python
# Python
async with GooseClient() as client:
    # Add an extension
    await client.add_extension(Extension(
        name="fetch",
        type="stdio",
        cmd="uvx",
        args=["mcp-server-fetch"],
        timeout=300
    ))
    
    # List tools
    tools = await client.get_tools()
    print(f"Available tools: {len(tools)}")
    
    # Remove extension
    await client.remove_extension("fetch")
```

```typescript
// TypeScript
const client = new GooseClient();

// Add an extension
await client.addExtension({
  name: 'fetch',
  type: 'stdio',
  cmd: 'uvx',
  args: ['mcp-server-fetch'],
  timeout: 300,
});

// List tools
const tools = await client.getTools();
console.log(`Available tools: ${tools.length}`);

// Remove extension
await client.removeExtension('fetch');
```

### 3. Session Management

```python
# Python
async with GooseClient() as client:
    # List all sessions
    sessions = await client.list_sessions()
    for session in sessions:
        print(f"Session: {session.id} - {session.name}")
    
    # Get session details
    details = await client.get_session("session-id")
    
    # Update session name
    await client.update_session_name("session-id", "New Name")
    
    # Export session
    data = await client.export_session("session-id")
    
    # Delete session
    await client.delete_session("session-id")
```

```typescript
// TypeScript
const client = new GooseClient();

// List all sessions
const sessions = await client.listSessions();
for (const session of sessions) {
  console.log(`Session: ${session.id} - ${session.name}`);
}

// Get session details
const details = await client.getSession('session-id');

// Update session name
await client.updateSessionName('session-id', 'New Name');

// Export session
const data = await client.exportSession('session-id');

// Delete session
await client.deleteSession('session-id');
```

### 4. Provider Configuration

```python
# Python
async with GooseClient() as client:
    # List available providers
    providers = await client.get_providers()
    
    # Get models for a provider
    models = await client.get_provider_models("openai")
    
    # Update agent provider
    await client.update_agent_provider("anthropic", "claude-3-opus")
```

```typescript
// TypeScript
const client = new GooseClient();

// List available providers
const providers = await client.getProviders();

// Get models for a provider
const models = await client.getProviderModels('openai');

// Update agent provider
await client.updateAgentProvider('anthropic', 'claude-3-opus');
```

## Advanced Usage

### Custom Frontend Tools

You can define custom tools that are executed by your application. See the [frontend_tools.py](../frontend_tools.py) example for a complete implementation.

### Error Handling

```python
# Python
from httpx import HTTPStatusError

async with GooseClient() as client:
    try:
        await client.start_agent()
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Authentication failed")
        elif e.response.status_code == 424:
            print("Agent not initialized")
        else:
            print(f"Request failed: {e}")
```

```typescript
// TypeScript
const client = new GooseClient();

try {
  await client.startAgent();
} catch (error) {
  if (error instanceof Error) {
    console.error('Request failed:', error.message);
  }
}
```

### Timeout Configuration

```python
# Python - Custom timeout
client = GooseClient(timeout=120.0)  # 120 seconds
```

```typescript
// TypeScript - Custom timeout
const client = new GooseClient(
  'http://localhost:3001',
  'your-secret-key',
  120000  // 120 seconds in milliseconds
);
```

## API Reference

For complete API documentation, see:

- [Integration Guide](../../documentation/docs/guides/integration-api.md)
- [OpenAPI Specification](../../ui/desktop/openapi.json)

## Contributing

To add support for additional languages:

1. Create a new SDK file (e.g., `goose_sdk.go`, `goose_sdk.rb`)
2. Implement the core API methods:
   - Agent management
   - Messaging with streaming support
   - Extension management
   - Session management
3. Add usage examples to this README
4. Submit a pull request

## License

Apache-2.0
