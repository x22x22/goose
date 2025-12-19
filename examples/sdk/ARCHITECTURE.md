# goose Integration Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your Business System                        │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Python     │  │  TypeScript  │  │     Java     │          │
│  │ Application  │  │  Application │  │  Application │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         │                 │                  │                   │
│  ┌──────▼─────────────────▼──────────────────▼───────┐          │
│  │            SDK Layer (Your Choice)                 │          │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐   │          │
│  │  │ Python SDK │  │ TypeScript │  │ Raw HTTP │   │          │
│  │  │            │  │    SDK     │  │  Calls   │   │          │
│  │  └────────────┘  └────────────┘  └──────────┘   │          │
│  └────────────────────────────────────────────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/REST + SSE
                            │ (localhost:3001)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       goose-server                               │
│                    (HTTP API Server)                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ API Endpoints                                               │ │
│  │  • /agent/start - Start new agent                          │ │
│  │  • /agent/resume - Resume session                          │ │
│  │  • /reply - Send message (SSE streaming)                   │ │
│  │  • /agent/add_extension - Add MCP extension                │ │
│  │  • /sessions - Session management                          │ │
│  │  • /config - Configuration                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            │                                      │
│  ┌────────────────────────▼──────────────────────────────────┐  │
│  │                    Agent Core                              │  │
│  │  • LLM Provider Management (OpenAI, Anthropic, etc.)      │  │
│  │  • Extension System (MCP Servers)                         │  │
│  │  • Session & Context Management                           │  │
│  │  • Tool Execution                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼──────┐                       ┌────────▼─────┐
│  LLM APIs    │                       │ MCP Servers  │
│              │                       │              │
│ • OpenAI     │                       │ • fetch      │
│ • Anthropic  │                       │ • github     │
│ • Databricks │                       │ • memory     │
│ • etc.       │                       │ • custom     │
└──────────────┘                       └──────────────┘
```

## Integration Flow

### 1. Start Agent Session

```
Business App → SDK → HTTP POST /agent/start → goose-server
                                               │
                                               ▼
                                        Initialize Agent
                                               │
                                               ▼
                                         200 OK ← ─ ─ ─ ─ ─ ─ ─ ─ ─
```

### 2. Send Message with Streaming Response

```
Business App → SDK → HTTP POST /reply → goose-server
                     (SSE stream)          │
                          ▲                 ▼
                          │          Process Message
                          │                 │
                          │                 ▼
                          │          Call LLM API
                          │                 │
                          │                 ▼
                          │         Execute Tools
                          │                 │
                          └─────────────────┘
                     Stream events back:
                     - Thinking
                     - ToolRequest
                     - ToolResponse
                     - Text
                     - Finish
```

### 3. Add Extension

```
Business App → SDK → HTTP POST /agent/add_extension → goose-server
                                                          │
                                                          ▼
                                                  Start MCP Server
                                                          │
                                                          ▼
                                                   Register Tools
                                                          │
                                                          ▼
                                                    200 OK ← ─ ─ ─
```

## Data Flow

### Request Example

```json
POST /reply
{
  "messages": [{
    "role": "user",
    "created": 1702345678,
    "content": [{
      "type": "text",
      "text": "Analyze this code"
    }]
  }],
  "session_id": "my-session",
  "session_working_dir": "/path/to/project"
}
```

### Streaming Response Example

```
data: {"type":"Thinking","message":{"content":[{"type":"text","text":"Let me analyze..."}]}}

data: {"type":"ToolRequest","message":{"content":[{"type":"toolRequest","name":"read_file"}]}}

data: {"type":"ToolResponse","message":{"content":[{"type":"toolResponse","content":"..."}]}}

data: {"type":"Text","message":{"content":[{"type":"text","text":"The code does..."}]}}

data: {"type":"Finish"}
```

## Authentication Flow

```
┌─────────────┐
│ Your App    │
└──────┬──────┘
       │
       │ 1. Include X-Secret-Key header
       │
┌──────▼──────┐
│ HTTP Request│
└──────┬──────┘
       │
       │ 2. Validate secret key
       │
┌──────▼──────┐
│ goose-server│
└──────┬──────┘
       │
       ├─── Valid: Process request
       │
       └─── Invalid: 401 Unauthorized
```

## Extension System

```
┌──────────────────────────────────────────────────────────┐
│                    goose Agent                            │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Built-in │  │  MCP     │  │ Frontend │              │
│  │  Tools   │  │Extension │  │  Tools   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │              │                     │
│       └─────────────┴──────────────┘                     │
│                     │                                    │
│              Available to Agent                          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ Tool Call
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐           ┌──────▼──────┐
    │ Execute │           │   Execute   │
    │Locally  │           │   via SDK   │
    └─────────┘           │(Your App)   │
                          └─────────────┘
```

## Session Management

```
┌─────────────────────────────────────────────────────────┐
│               Session Lifecycle                          │
│                                                          │
│  ┌──────┐   start   ┌────────┐   messages   ┌────────┐│
│  │ None │ ────────▶ │ Active │ ───────────▶ │ Active ││
│  └──────┘           └───┬────┘              └───┬────┘│
│                         │                        │     │
│                         │ pause                  │     │
│                         ▼                        │     │
│                    ┌────────┐                    │     │
│                    │ Paused │                    │     │
│                    └───┬────┘                    │     │
│                         │                        │     │
│                         │ resume                 │     │
│                         └────────────────────────┘     │
│                                                         │
│                         delete                          │
│                           │                             │
│                           ▼                             │
│                      ┌─────────┐                        │
│                      │ Deleted │                        │
│                      └─────────┘                        │
└─────────────────────────────────────────────────────────┘
```

## Multi-Language Integration

```
┌─────────────────────────────────────────────────────────┐
│             Your Infrastructure                          │
│                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│  │ Python  │    │ Node.js │    │  Java   │            │
│  │ Service │    │ Service │    │ Service │            │
│  └────┬────┘    └────┬────┘    └────┬────┘            │
│       │              │              │                   │
│       │   Python SDK │  TS SDK     │  HTTP Client      │
│       └──────────────┴──────────────┘                   │
│                      │                                   │
│                      │                                   │
│         All communicate with same goose-server          │
│                      │                                   │
└──────────────────────┼───────────────────────────────────┘
                       │
                       ▼
               ┌────────────────┐
               │  goose-server  │
               │  (Port 3001)   │
               └────────────────┘
                       │
                       ▼
          Shared sessions & context
          maintained across all services
```

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                Security Architecture                     │
│                                                          │
│  Layer 1: Network                                        │
│  ┌────────────────────────────────────────────────┐    │
│  │ • HTTPS/TLS                                     │    │
│  │ • Firewall rules                                │    │
│  │ • Rate limiting                                 │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Layer 2: Authentication                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │ • X-Secret-Key header validation                │    │
│  │ • Key rotation support                          │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Layer 3: Authorization                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Permission system                             │    │
│  │ • Tool approval workflow                        │    │
│  │ • Session isolation                             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Layer 4: Input Validation                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Request validation                            │    │
│  │ • Content sanitization                          │    │
│  │ • Type checking                                 │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Deployment Options

### Option 1: Embedded Server

```
┌────────────────────────────────────┐
│      Your Application              │
│                                    │
│  ┌──────────────────────────────┐ │
│  │  Business Logic              │ │
│  └───────────┬──────────────────┘ │
│              │                     │
│  ┌───────────▼──────────────────┐ │
│  │  SDK Client                  │ │
│  └───────────┬──────────────────┘ │
│              │ localhost          │
│  ┌───────────▼──────────────────┐ │
│  │  goose-server (embedded)     │ │
│  └──────────────────────────────┘ │
└────────────────────────────────────┘
```

### Option 2: Separate Service

```
┌────────────────┐         ┌────────────────┐
│  Your App 1    │         │  Your App 2    │
│  (Python)      │         │  (Node.js)     │
└───────┬────────┘         └───────┬────────┘
        │                          │
        │   HTTP                   │
        └──────────┬───────────────┘
                   │
           ┌───────▼────────┐
           │ goose-server   │
           │ (Shared)       │
           └────────────────┘
```

### Option 3: Distributed Deployment

```
┌────────┐  ┌────────┐  ┌────────┐
│  App 1 │  │  App 2 │  │  App N │
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
    └───────────┴───────────┘
                │
        ┌───────▼────────┐
        │  Load Balancer │
        └───────┬────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼────┐             ┌────▼───┐
│goose-  │             │goose-  │
│server 1│             │server 2│
└────────┘             └────────┘
```

## Performance Considerations

```
┌─────────────────────────────────────────────────────────┐
│              Performance Optimization                    │
│                                                          │
│  1. Connection Pooling                                   │
│     • SDK maintains persistent connections              │
│     • Reduces connection overhead                       │
│                                                          │
│  2. Streaming Responses                                  │
│     • Server-Sent Events (SSE)                          │
│     • Real-time updates without polling                 │
│                                                          │
│  3. Session Caching                                      │
│     • Context maintained in memory                      │
│     • Faster subsequent requests                        │
│                                                          │
│  4. Async Processing                                     │
│     • Non-blocking I/O                                  │
│     • Concurrent request handling                       │
│                                                          │
│  5. Resource Management                                  │
│     • Extension lifecycle management                    │
│     • Automatic cleanup                                 │
└─────────────────────────────────────────────────────────┘
```

---

**中文说明**

## 系统架构

goose 提供完整的 HTTP API 服务器，支持通过 SDK 或直接 HTTP 调用集成到业务系统中。主要组件包括：

1. **goose-server**: HTTP API 服务器，提供 REST 端点和 SSE 流式响应
2. **SDK 层**: Python 和 TypeScript SDK 封装，简化集成
3. **Agent 核心**: 管理 LLM 提供商、扩展系统和会话
4. **扩展系统**: 支持 MCP 服务器和自定义前端工具

## 集成方式

- **Python**: 使用 `goose_sdk.py` 异步客户端
- **TypeScript/JavaScript**: 使用 `goose-sdk.ts` 现代化客户端
- **其他语言**: 直接使用 HTTP REST API

详细文档请参阅 `integration-api-zh.md`。
