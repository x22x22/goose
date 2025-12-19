# goose SDK and HTTP API Integration Summary

## Overview

This document summarizes the SDK and HTTP API integration capabilities added to goose, enabling developers to integrate goose as an AI agent framework into their business systems.

## What Was Added

### 1. Documentation

#### English Documentation
- **File**: `documentation/docs/guides/integration-api.md`
- **Content**: Comprehensive guide covering:
  - HTTP API overview and core endpoints
  - Agent management (start, resume, update)
  - Messaging with streaming support
  - Extension management
  - Session management
  - Integration examples for Python, TypeScript, and Java
  - Best practices and troubleshooting
  - Security considerations

#### Chinese Documentation (中文文档)
- **File**: `documentation/docs/guides/integration-api-zh.md`
- **Content**: Complete Chinese translation of the integration guide
- **Purpose**: Make goose accessible to Chinese-speaking developers

### 2. SDK Implementations

#### Python SDK
- **File**: `examples/sdk/goose_sdk.py`
- **Features**:
  - Async/await support with httpx
  - Full API coverage (agent, messages, extensions, sessions, config)
  - Type hints throughout
  - Streaming response handling with Server-Sent Events (SSE)
  - Comprehensive docstrings
  - Context manager support
- **Dependencies**: httpx>=0.25.0

#### TypeScript SDK
- **File**: `examples/sdk/goose-sdk.ts`
- **Features**:
  - Modern TypeScript with full type definitions
  - Async generators for streaming
  - Browser and Node.js compatible
  - No external dependencies (uses native fetch)
  - Type-safe API methods
- **Build**: TypeScript 5.0+

### 3. Supporting Files

- **`examples/sdk/README.md`**: Comprehensive usage guide with examples
- **`examples/sdk/requirements.txt`**: Python dependencies
- **`examples/sdk/package.json`**: NPM package configuration
- **`examples/sdk/tsconfig.json`**: TypeScript compiler configuration
- **`examples/sdk/test_sdk.py`**: Test script to verify SDK functionality
- **`examples/sdk/INTEGRATION_SUMMARY.md`**: This file

### 4. Updated Files

- **`README.md`**: Added links to integration guide and SDK examples in Quick Links section

## How to Use

### Quick Start

1. **Start the goose server:**
   ```bash
   cargo run -p goose-server -- agent
   ```

2. **Set authentication (optional):**
   ```bash
   export GOOSE_SERVER__SECRET_KEY="your-secret-key"
   ```
   (Default is "test" for development)

3. **Test the SDK:**
   ```bash
   cd examples/sdk
   pip install httpx
   python3 test_sdk.py
   ```

### Python Integration Example

```python
from goose_sdk import GooseClient

async with GooseClient() as client:
    # Start agent
    await client.start_agent(provider="openai", model="gpt-4")
    
    # Send message and get streaming response
    async for event in client.send_message("session-1", "Analyze this codebase"):
        if event.message:
            for content in event.message.content:
                if content.type == "text":
                    print(content.text)
```

### TypeScript Integration Example

```typescript
import { GooseClient } from './goose-sdk';

const client = new GooseClient();
await client.startAgent({ provider: 'openai', model: 'gpt-4' });

for await (const event of client.sendMessage('session-1', 'Analyze this codebase')) {
  if (event.message) {
    for (const content of event.message.content) {
      if (content.type === 'text') {
        console.log(content.text);
      }
    }
  }
}
```

## Key Features

### 1. HTTP API Server
- **Location**: `goose-server` crate
- **Default Port**: 3001
- **Protocol**: REST with SSE for streaming
- **Authentication**: Secret key via `X-Secret-Key` header
- **Documentation**: OpenAPI 3.0 spec at `ui/desktop/openapi.json`

### 2. Core Capabilities
- **Agent Management**: Start, resume, and update AI agents
- **Message Streaming**: Real-time streaming responses with SSE
- **Extension System**: Add/remove MCP extensions dynamically
- **Session Management**: Create, list, update, and delete sessions
- **Configuration**: Manage providers, models, and permissions
- **Scheduling**: Create recurring tasks with cron schedules

### 3. Security Features
- Secret key authentication
- HTTPS support (recommended for production)
- Session isolation
- Input validation
- Rate limiting (server-side)

## API Endpoints Summary

### Agent Endpoints
- `POST /agent/start` - Start new agent
- `POST /agent/resume` - Resume existing session
- `POST /agent/update_provider` - Change LLM provider/model
- `POST /agent/add_extension` - Add extension
- `POST /agent/remove_extension` - Remove extension
- `GET /agent/tools` - List available tools

### Message Endpoints
- `POST /reply` - Send message (SSE streaming response)

### Session Endpoints
- `GET /sessions` - List sessions
- `GET /sessions/{id}` - Get session details
- `POST /sessions/{id}/name` - Update session name
- `DELETE /sessions/{id}` - Delete session
- `GET /sessions/{id}/export` - Export session
- `GET /sessions/insights` - Get usage analytics

### Configuration Endpoints
- `GET /config/providers` - List providers
- `GET /config/providers/{name}/models` - Get provider models
- `GET /config/extensions` - List extensions
- `GET /status` - Server status

## Testing

### Automated Tests
- Python SDK: Syntax validated with `python3 -m py_compile`
- TypeScript SDK: Type checked with `tsc --noEmit`
- Security: Scanned with CodeQL (0 vulnerabilities)

### Manual Testing
Use the test script to verify functionality:
```bash
cd examples/sdk
python3 test_sdk.py
```

The test script checks:
- Server connectivity
- Available providers
- Available extensions
- Existing sessions

## Documentation Links

- **Integration Guide (English)**: `documentation/docs/guides/integration-api.md`
- **Integration Guide (中文)**: `documentation/docs/guides/integration-api-zh.md`
- **SDK Examples**: `examples/sdk/README.md`
- **OpenAPI Spec**: `ui/desktop/openapi.json`
- **Main README**: Updated with integration links

## Use Cases

### 1. Business System Integration
Integrate goose into existing business applications to add AI agent capabilities:
- Customer support automation
- Code review and analysis
- Documentation generation
- Data analysis and reporting

### 2. Custom Workflows
Build custom workflows using goose as the AI engine:
- CI/CD pipeline automation
- Scheduled maintenance tasks
- Automated code refactoring
- Test generation

### 3. Multi-Language Applications
The HTTP API allows integration from any programming language:
- Python web services
- Node.js applications
- Java enterprise systems
- Go microservices
- .NET applications

### 4. Frontend Applications
Use the TypeScript SDK to integrate goose into web applications:
- Developer tools and IDEs
- Documentation platforms
- Code collaboration tools
- AI-assisted development environments

## Best Practices

1. **Session Management**: Reuse sessions for related tasks to maintain context
2. **Error Handling**: Always handle errors appropriately and check status codes
3. **Streaming**: Consume entire streaming responses to avoid connection issues
4. **Timeouts**: Set appropriate timeouts for long-running operations
5. **Security**: Never commit secret keys, use HTTPS in production
6. **Extension Lifecycle**: Add extensions before tasks, remove when done

## Future Enhancements

Potential areas for improvement:
- Additional language SDKs (Go, Ruby, Java, C#)
- WebSocket support for bidirectional streaming
- Batch API for processing multiple requests
- SDK publishing to package registries (PyPI, NPM)
- GraphQL API option
- Rate limiting and quota management
- Enhanced authentication (OAuth, JWT)

## Contributing

To add support for additional languages:
1. Create a new SDK file in `examples/sdk/`
2. Implement the core API methods
3. Add usage examples to the README
4. Submit a pull request

## Support

- **Documentation**: https://block.github.io/goose/
- **Issues**: https://github.com/block/goose/issues
- **Discord**: https://discord.gg/goose-oss

## License

Apache-2.0

---

**问题解答 (Answer to the Original Question)**

是的，本项目现在提供了完整的 SDK 和 HTTP API 调用方式，可以将 goose 作为 agent 框架集成到业务系统中：

1. **HTTP API**: 通过 `goose-server` 提供 REST API，运行在 localhost:3001
2. **Python SDK**: 提供了完整的 Python 客户端库（`examples/sdk/goose_sdk.py`）
3. **TypeScript SDK**: 提供了 TypeScript/JavaScript 客户端库（`examples/sdk/goose-sdk.ts`）
4. **详细文档**: 包含中英文集成指南和使用示例

您现在可以使用这些 SDK 将 goose 的 AI agent 能力集成到任何业务系统中！
