---
sidebar_position: 21
---

# Integrating goose as an Agent Framework

This guide explains how to integrate goose into your business systems using the HTTP API, allowing your applications to leverage goose's AI agent capabilities.

## Overview

goose provides a comprehensive HTTP API through `goose-server` that allows you to:

- Start and manage AI agent sessions
- Send messages and receive streaming responses
- Add and remove extensions dynamically
- Configure providers and models
- Manage session history and context
- Schedule automated tasks

## Getting Started

### 1. Start the goose Server

First, start the goose server:

```bash
cargo run -p goose-server -- agent
```

By default, the server runs on `http://localhost:3001`.

### 2. Set Authentication

The server uses a secret key for authentication. Set it via environment variable:

```bash
export GOOSE_SERVER__SECRET_KEY="your-secret-key"
```

For development, the default is `"test"`.

### 3. Include Authentication Header

All API requests must include the secret key in the `X-Secret-Key` header:

```
X-Secret-Key: your-secret-key
```

## Core API Endpoints

### Agent Management

#### Start Agent Session

```http
POST /agent/start
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "provider": "openai",
  "model": "gpt-4",
  "working_dir": "/path/to/workspace"
}
```

#### Resume Existing Session

```http
POST /agent/resume
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "session_id": "session-uuid"
}
```

### Messaging

#### Send Message and Get Response

The `/reply` endpoint accepts messages and returns a streaming response:

```http
POST /reply
Content-Type: application/json
Accept: text/event-stream
X-Secret-Key: your-secret-key

{
  "messages": [
    {
      "role": "user",
      "created": 1702345678,
      "content": [
        {
          "type": "text",
          "text": "Write a hello world program in Python"
        }
      ]
    }
  ],
  "session_id": "session-uuid",
  "session_working_dir": "/path/to/workspace"
}
```

The response is a Server-Sent Events (SSE) stream with events like:

- `Thinking` - Agent reasoning
- `ToolRequest` - Agent requesting to use a tool
- `ToolResponse` - Tool execution result
- `Text` - Agent text response
- `Finish` - Response complete

### Extension Management

#### List Available Extensions

```http
GET /config/extensions
X-Secret-Key: your-secret-key
```

#### Add Extension to Agent

```http
POST /agent/add_extension
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "fetch",
  "type": "stdio",
  "cmd": "uvx",
  "args": ["mcp-server-fetch"],
  "timeout": 300
}
```

#### Remove Extension

```http
POST /agent/remove_extension
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "fetch"
}
```

### Session Management

#### List Sessions

```http
GET /sessions
X-Secret-Key: your-secret-key
```

#### Get Session Details

```http
GET /sessions/{session_id}
X-Secret-Key: your-secret-key
```

#### Update Session Name

```http
POST /sessions/{session_id}/name
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "My Project Analysis"
}
```

#### Delete Session

```http
DELETE /sessions/{session_id}
X-Secret-Key: your-secret-key
```

## Integration Examples

### Python Integration

Here's a complete Python example using `httpx`:

```python
import asyncio
import httpx
import json
from datetime import datetime

GOOSE_URL = "http://localhost:3001"
SECRET_KEY = "your-secret-key"

async def start_agent():
    """Initialize the agent."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GOOSE_URL}/agent/start",
            json={
                "provider": "openai",
                "model": "gpt-4"
            },
            headers={"X-Secret-Key": SECRET_KEY}
        )
        response.raise_for_status()
        return response.json()

async def send_message(session_id: str, message: str):
    """Send a message and process the streaming response."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "messages": [{
                "role": "user",
                "created": int(datetime.now().timestamp()),
                "content": [{"type": "text", "text": message}]
            }],
            "session_id": session_id,
            "session_working_dir": "."
        }
        
        async with client.stream(
            "POST",
            f"{GOOSE_URL}/reply",
            json=payload,
            headers={
                "X-Secret-Key": SECRET_KEY,
                "Accept": "text/event-stream"
            }
        ) as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data["type"] == "Finish":
                        break
                    yield data

async def main():
    # Start agent
    agent = await start_agent()
    
    # Send message
    async for event in send_message("my-session", "Hello, goose!"):
        print(f"Event: {event['type']}")
        if event.get("message"):
            print(f"Content: {event['message']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/TypeScript Integration

```typescript
const GOOSE_URL = 'http://localhost:3001';
const SECRET_KEY = 'your-secret-key';

interface Message {
  role: string;
  created: number;
  content: Array<{ type: string; text: string }>;
}

async function startAgent(): Promise<void> {
  const response = await fetch(`${GOOSE_URL}/agent/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Secret-Key': SECRET_KEY,
    },
    body: JSON.stringify({
      provider: 'openai',
      model: 'gpt-4',
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to start agent: ${response.statusText}`);
  }
}

async function* sendMessage(
  sessionId: string,
  message: string
): AsyncGenerator<any> {
  const payload = {
    messages: [{
      role: 'user',
      created: Math.floor(Date.now() / 1000),
      content: [{ type: 'text', text: message }],
    }],
    session_id: sessionId,
    session_working_dir: '.',
  };

  const response = await fetch(`${GOOSE_URL}/reply`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'X-Secret-Key': SECRET_KEY,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'Finish') {
          return;
        }
        yield data;
      }
    }
  }
}

// Usage
async function main() {
  await startAgent();
  
  for await (const event of sendMessage('my-session', 'Hello, goose!')) {
    console.log('Event:', event.type);
    if (event.message) {
      console.log('Content:', event.message);
    }
  }
}

main().catch(console.error);
```

### Java Integration

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Instant;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class GooseClient {
    private static final String GOOSE_URL = "http://localhost:3001";
    private static final String SECRET_KEY = "your-secret-key";
    private final HttpClient client;
    private final Gson gson;

    public GooseClient() {
        this.client = HttpClient.newHttpClient();
        this.gson = new Gson();
    }

    public void startAgent(String provider, String model) throws Exception {
        JsonObject payload = new JsonObject();
        payload.addProperty("provider", provider);
        payload.addProperty("model", model);

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(GOOSE_URL + "/agent/start"))
            .header("Content-Type", "application/json")
            .header("X-Secret-Key", SECRET_KEY)
            .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(payload)))
            .build();

        HttpResponse<String> response = client.send(
            request,
            HttpResponse.BodyHandlers.ofString()
        );

        if (response.statusCode() != 200) {
            throw new RuntimeException("Failed to start agent: " + response.body());
        }
    }

    public void sendMessage(String sessionId, String message) throws Exception {
        JsonObject content = new JsonObject();
        content.addProperty("type", "text");
        content.addProperty("text", message);

        JsonObject msg = new JsonObject();
        msg.addProperty("role", "user");
        msg.addProperty("created", Instant.now().getEpochSecond());
        msg.add("content", gson.toJsonTree(new JsonObject[]{ content }));

        JsonObject payload = new JsonObject();
        payload.add("messages", gson.toJsonTree(new JsonObject[]{ msg }));
        payload.addProperty("session_id", sessionId);
        payload.addProperty("session_working_dir", ".");

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(GOOSE_URL + "/reply"))
            .header("Content-Type", "application/json")
            .header("Accept", "text/event-stream")
            .header("X-Secret-Key", SECRET_KEY)
            .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(payload)))
            .build();

        // Process streaming response
        client.send(request, HttpResponse.BodyHandlers.ofLines())
            .body()
            .forEach(line -> {
                if (line.startsWith("data: ")) {
                    JsonObject data = gson.fromJson(line.substring(6), JsonObject.class);
                    String type = data.get("type").getAsString();
                    System.out.println("Event type: " + type);
                    
                    if (type.equals("Finish")) {
                        return;
                    }
                }
            });
    }

    public static void main(String[] args) throws Exception {
        GooseClient client = new GooseClient();
        client.startAgent("openai", "gpt-4");
        client.sendMessage("my-session", "Hello, goose!");
    }
}
```

## Advanced Features

### Frontend Tools

You can define custom tools that are executed by your application. When the agent needs to use these tools, it will request them via the API, and your application executes them and returns results.

See [examples/frontend_tools.py](https://github.com/block/goose/blob/main/examples/frontend_tools.py) for a complete example.

### Scheduled Tasks

Schedule recurring tasks using the scheduling API:

```http
POST /schedule/create
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "Daily Report",
  "cron_schedule": "0 9 * * *",
  "recipe_name": "generate_report",
  "enabled": true
}
```

### Session Insights

Get analytics about token usage and costs:

```http
GET /sessions/insights
X-Secret-Key: your-secret-key
```

## API Reference

For complete API documentation, see the OpenAPI specification:

- **Development**: `http://localhost:3001/` (when server is running)
- **Source**: [`ui/desktop/openapi.json`](https://github.com/block/goose/blob/main/ui/desktop/openapi.json)

## Best Practices

### 1. Session Management

- Reuse sessions for related tasks to maintain context
- Use descriptive session names for easy tracking
- Clean up old sessions periodically

### 2. Error Handling

Always handle errors appropriately:

```python
try:
    response = await client.post(url, json=payload, headers=headers)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        print("Authentication failed")
    elif e.response.status_code == 424:
        print("Agent not initialized")
    else:
        print(f"Request failed: {e}")
```

### 3. Streaming Response Handling

Always consume the entire streaming response to avoid connection issues:

```python
async for event in stream:
    # Process event
    if event["type"] == "Finish":
        break
```

### 4. Timeout Configuration

Set appropriate timeouts for long-running operations:

```python
async with httpx.AsyncClient(timeout=300.0) as client:
    # Your API calls
```

### 5. Extension Lifecycle

- Add extensions before starting complex tasks
- Remove extensions when no longer needed to reduce overhead
- Use extension timeout settings to prevent hanging operations

## Security Considerations

1. **Keep Secret Keys Secure**: Never commit secret keys to version control
2. **Use HTTPS in Production**: Always use TLS/SSL for production deployments
3. **Validate Input**: Sanitize all user input before sending to the agent
4. **Monitor Usage**: Track API usage and set up alerts for unusual patterns
5. **Restrict Access**: Use firewall rules to limit access to the API server
6. **Session Isolation**: Ensure proper isolation between different users' sessions

## Troubleshooting

### Connection Refused

Ensure the server is running:
```bash
cargo run -p goose-server -- agent
```

### 401 Unauthorized

Check that the `X-Secret-Key` header matches the server configuration.

### 424 Agent Not Initialized

Call `/agent/start` or `/agent/resume` before sending messages.

### Streaming Response Issues

Ensure you're properly handling SSE format and consuming the full stream.

## Examples Repository

For more integration examples, see:

- [examples/frontend_tools.py](https://github.com/block/goose/blob/main/examples/frontend_tools.py) - Python client with custom tools
- [test_acp_client.py](https://github.com/block/goose/blob/main/test_acp_client.py) - ACP protocol client

## Additional Resources

- [OpenAPI Specification](https://github.com/block/goose/blob/main/ui/desktop/openapi.json)
- [goose Documentation](https://block.github.io/goose/)
- [Extension Development Guide](./managing-tools/creating-extensions.md)
- [Configuration Guide](./config-files.md)
