---
sidebar_position: 22
---

# 将 goose 集成为 Agent 框架

本指南说明如何使用 HTTP API 将 goose 集成到您的业务系统中，使您的应用程序能够利用 goose 的 AI agent 能力。

## 概述

goose 通过 `goose-server` 提供全面的 HTTP API，允许您：

- 启动和管理 AI agent 会话
- 发送消息并接收流式响应
- 动态添加和删除扩展
- 配置提供商和模型
- 管理会话历史和上下文
- 调度自动化任务

## 快速开始

### 1. 启动 goose 服务器

首先，启动 goose 服务器：

```bash
cargo run -p goose-server -- agent
```

默认情况下，服务器运行在 `http://localhost:3001`。

### 2. 设置身份验证

服务器使用密钥进行身份验证。通过环境变量设置：

```bash
export GOOSE_SERVER__SECRET_KEY="your-secret-key"
```

开发环境下，默认值为 `"test"`。

### 3. 包含身份验证头

所有 API 请求必须在 `X-Secret-Key` 头中包含密钥：

```
X-Secret-Key: your-secret-key
```

## 核心 API 端点

### Agent 管理

#### 启动 Agent 会话

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

#### 恢复现有会话

```http
POST /agent/resume
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "session_id": "session-uuid"
}
```

### 消息传递

#### 发送消息并获取响应

`/reply` 端点接受消息并返回流式响应：

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
          "text": "用 Python 写一个 hello world 程序"
        }
      ]
    }
  ],
  "session_id": "session-uuid",
  "session_working_dir": "/path/to/workspace"
}
```

响应是一个服务器发送事件（SSE）流，包含以下事件：

- `Thinking` - Agent 推理过程
- `ToolRequest` - Agent 请求使用工具
- `ToolResponse` - 工具执行结果
- `Text` - Agent 文本响应
- `Finish` - 响应完成

### 扩展管理

#### 列出可用扩展

```http
GET /config/extensions
X-Secret-Key: your-secret-key
```

#### 向 Agent 添加扩展

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

#### 删除扩展

```http
POST /agent/remove_extension
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "fetch"
}
```

### 会话管理

#### 列出会话

```http
GET /sessions
X-Secret-Key: your-secret-key
```

#### 获取会话详情

```http
GET /sessions/{session_id}
X-Secret-Key: your-secret-key
```

#### 更新会话名称

```http
POST /sessions/{session_id}/name
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "我的项目分析"
}
```

#### 删除会话

```http
DELETE /sessions/{session_id}
X-Secret-Key: your-secret-key
```

## 集成示例

### Python 集成

使用 `httpx` 的完整 Python 示例：

```python
import asyncio
import httpx
import json
from datetime import datetime

GOOSE_URL = "http://localhost:3001"
SECRET_KEY = "your-secret-key"

async def start_agent():
    """初始化 agent"""
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
    """发送消息并处理流式响应"""
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
    # 启动 agent
    agent = await start_agent()
    
    # 发送消息
    async for event in send_message("my-session", "你好，goose！"):
        print(f"事件: {event['type']}")
        if event.get("message"):
            print(f"内容: {event['message']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/TypeScript 集成

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
    throw new Error(`启动 agent 失败: ${response.statusText}`);
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
    throw new Error(`发送消息失败: ${response.statusText}`);
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

// 使用示例
async function main() {
  await startAgent();
  
  for await (const event of sendMessage('my-session', '你好，goose！')) {
    console.log('事件:', event.type);
    if (event.message) {
      console.log('内容:', event.message);
    }
  }
}

main().catch(console.error);
```

### Java 集成

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
            throw new RuntimeException("启动 agent 失败: " + response.body());
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

        // 处理流式响应
        client.send(request, HttpResponse.BodyHandlers.ofLines())
            .body()
            .forEach(line -> {
                if (line.startsWith("data: ")) {
                    JsonObject data = gson.fromJson(line.substring(6), JsonObject.class);
                    String type = data.get("type").getAsString();
                    System.out.println("事件类型: " + type);
                    
                    if (type.equals("Finish")) {
                        return;
                    }
                }
            });
    }

    public static void main(String[] args) throws Exception {
        GooseClient client = new GooseClient();
        client.startAgent("openai", "gpt-4");
        client.sendMessage("my-session", "你好，goose！");
    }
}
```

## SDK 封装

我们提供了现成的 SDK 封装，可以更方便地集成：

### Python SDK

位置：`examples/sdk/goose_sdk.py`

```python
from goose_sdk import GooseClient

async with GooseClient() as client:
    # 启动 agent
    await client.start_agent(provider="openai", model="gpt-4")
    
    # 发送消息
    async for event in client.send_message("session-1", "分析这个代码库"):
        if event.message:
            print(event.message.content[0].text)
```

### TypeScript SDK

位置：`examples/sdk/goose-sdk.ts`

```typescript
import { GooseClient } from './goose-sdk';

const client = new GooseClient();
await client.startAgent({ provider: 'openai', model: 'gpt-4' });

for await (const event of client.sendMessage('session-1', '分析这个代码库')) {
  if (event.message) {
    console.log(event.message.content[0].text);
  }
}
```

更多详情请参阅 [SDK 示例文档](https://github.com/block/goose/tree/main/examples/sdk)。

## 高级功能

### 前端工具

您可以定义由应用程序执行的自定义工具。当 agent 需要使用这些工具时，它会通过 API 请求它们，您的应用程序执行它们并返回结果。

完整示例请参见 [examples/frontend_tools.py](https://github.com/block/goose/blob/main/examples/frontend_tools.py)。

### 定时任务

使用调度 API 安排定期任务：

```http
POST /schedule/create
Content-Type: application/json
X-Secret-Key: your-secret-key

{
  "name": "每日报告",
  "cron_schedule": "0 9 * * *",
  "recipe_name": "generate_report",
  "enabled": true
}
```

### 会话洞察

获取有关令牌使用和成本的分析：

```http
GET /sessions/insights
X-Secret-Key: your-secret-key
```

## API 参考

完整的 API 文档，请参阅 OpenAPI 规范：

- **开发环境**：`http://localhost:3001/`（当服务器运行时）
- **源文件**：[`ui/desktop/openapi.json`](https://github.com/block/goose/blob/main/ui/desktop/openapi.json)

## 最佳实践

### 1. 会话管理

- 为相关任务重用会话以保持上下文
- 使用描述性会话名称便于跟踪
- 定期清理旧会话

### 2. 错误处理

始终适当处理错误：

```python
try:
    response = await client.post(url, json=payload, headers=headers)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        print("身份验证失败")
    elif e.response.status_code == 424:
        print("Agent 未初始化")
    else:
        print(f"请求失败: {e}")
```

### 3. 流式响应处理

始终消费整个流式响应以避免连接问题：

```python
async for event in stream:
    # 处理事件
    if event["type"] == "Finish":
        break
```

### 4. 超时配置

为长时间运行的操作设置适当的超时：

```python
async with httpx.AsyncClient(timeout=300.0) as client:
    # 您的 API 调用
```

### 5. 扩展生命周期

- 在开始复杂任务之前添加扩展
- 不再需要时删除扩展以减少开销
- 使用扩展超时设置防止挂起操作

## 安全考虑

1. **保护密钥安全**：永远不要将密钥提交到版本控制
2. **生产环境使用 HTTPS**：生产部署始终使用 TLS/SSL
3. **验证输入**：在发送到 agent 之前清理所有用户输入
4. **监控使用**：跟踪 API 使用情况并为异常模式设置警报
5. **限制访问**：使用防火墙规则限制对 API 服务器的访问
6. **会话隔离**：确保不同用户会话之间的适当隔离

## 故障排除

### 连接被拒绝

确保服务器正在运行：
```bash
cargo run -p goose-server -- agent
```

### 401 未授权

检查 `X-Secret-Key` 头是否与服务器配置匹配。

### 424 Agent 未初始化

在发送消息之前调用 `/agent/start` 或 `/agent/resume`。

### 流式响应问题

确保正确处理 SSE 格式并消费完整流。

## 示例仓库

更多集成示例，请参见：

- [examples/frontend_tools.py](https://github.com/block/goose/blob/main/examples/frontend_tools.py) - 带自定义工具的 Python 客户端
- [examples/sdk/](https://github.com/block/goose/tree/main/examples/sdk) - Python 和 TypeScript SDK
- [test_acp_client.py](https://github.com/block/goose/blob/main/test_acp_client.py) - ACP 协议客户端

## 其他资源

- [OpenAPI 规范](https://github.com/block/goose/blob/main/ui/desktop/openapi.json)
- [goose 文档](https://block.github.io/goose/)
- [扩展开发指南](./managing-tools/creating-extensions.md)
- [配置指南](./config-files.md)
