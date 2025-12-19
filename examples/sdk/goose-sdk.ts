/**
 * goose TypeScript/JavaScript SDK
 * 
 * A TypeScript SDK for integrating goose AI agent into your applications.
 * 
 * Example usage:
 * ```typescript
 * import { GooseClient } from './goose-sdk';
 * 
 * const client = new GooseClient('http://localhost:3001', 'your-secret-key');
 * 
 * // Start agent
 * await client.startAgent({ provider: 'openai', model: 'gpt-4' });
 * 
 * // Send message and get response
 * for await (const event of client.sendMessage('my-session', 'Hello!')) {
 *   if (event.message) {
 *     console.log(event.message);
 *   }
 * }
 * ```
 */

export interface MessageContent {
  type: string;
  text: string;
  annotations?: Record<string, any>;
}

export interface Message {
  role: string;
  created: number;
  content: MessageContent[];
}

export interface Event {
  type: string;
  message?: Message;
  raw?: Record<string, any>;
}

export interface Extension {
  name: string;
  type: string;
  cmd?: string;
  args?: string[];
  envs?: Record<string, string>;
  timeout?: number;
  bundled?: boolean;
}

export interface Session {
  id: string;
  name?: string;
  created?: number;
  updated?: number;
  working_dir?: string;
}

export interface StartAgentOptions {
  provider?: string;
  model?: string;
  working_dir?: string;
}

export interface SendMessageOptions {
  working_dir?: string;
}

/**
 * Client for interacting with the goose HTTP API.
 */
export class GooseClient {
  private baseUrl: string;
  private secretKey: string;
  private timeout: number;

  /**
   * Create a new goose client.
   * 
   * @param baseUrl - Base URL of the goose server (default: http://localhost:3001)
   * @param secretKey - Authentication secret key (default: "test")
   * @param timeout - Request timeout in milliseconds (default: 60000)
   */
  constructor(
    baseUrl: string = 'http://localhost:3001',
    secretKey: string = 'test',
    timeout: number = 60000
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.secretKey = secretKey;
    this.timeout = timeout;
  }

  /**
   * Get default headers with authentication.
   */
  private getHeaders(additionalHeaders?: Record<string, string>): Record<string, string> {
    return {
      'X-Secret-Key': this.secretKey,
      'Content-Type': 'application/json',
      ...additionalHeaders,
    };
  }

  /**
   * Make an HTTP request to the goose API.
   */
  private async request<T = any>(
    method: string,
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers = this.getHeaders(options?.headers as Record<string, string>);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        signal: controller.signal,
        ...options,
      });

      if (!response.ok) {
        throw new Error(
          `Request failed: ${response.status} ${response.statusText}`
        );
      }

      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }
      return (await response.text()) as any;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // Agent Management

  /**
   * Start a new agent session.
   */
  async startAgent(options: StartAgentOptions = {}): Promise<any> {
    const payload = {
      provider: options.provider || 'openai',
      model: options.model || 'gpt-4',
      ...(options.working_dir && { working_dir: options.working_dir }),
    };

    return this.request('POST', '/agent/start', {
      body: JSON.stringify(payload),
    });
  }

  /**
   * Resume an existing agent session.
   */
  async resumeAgent(sessionId: string): Promise<any> {
    return this.request('POST', '/agent/resume', {
      body: JSON.stringify({ session_id: sessionId }),
    });
  }

  /**
   * Update the agent's LLM provider and model.
   */
  async updateAgentProvider(provider: string, model: string): Promise<any> {
    return this.request('POST', '/agent/update_provider', {
      body: JSON.stringify({ provider, model }),
    });
  }

  // Messaging

  /**
   * Send a message to the agent and stream the response.
   */
  async *sendMessage(
    sessionId: string,
    message: string,
    options: SendMessageOptions = {}
  ): AsyncGenerator<Event> {
    const payload = {
      messages: [
        {
          role: 'user',
          created: Math.floor(Date.now() / 1000),
          content: [{ type: 'text', text: message }],
        },
      ],
      session_id: sessionId,
      session_working_dir: options.working_dir || '.',
    };

    const response = await fetch(`${this.baseUrl}/reply`, {
      method: 'POST',
      headers: this.getHeaders({ Accept: 'text/event-stream' }),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            const event: Event = {
              type: data.type || 'Unknown',
              raw: data,
            };

            if (data.type === 'Finish') {
              yield event;
              return;
            }

            if (data.message) {
              const msgData = data.message;
              const content: MessageContent[] = (msgData.content || []).map(
                (c: any) => ({
                  type: c.type,
                  text: c.text || '',
                  annotations: c.annotations,
                })
              );

              event.message = {
                role: msgData.role,
                created: msgData.created,
                content,
              };
            }

            yield event;
          } catch (e) {
            // Skip invalid JSON
            continue;
          }
        }
      }
    }
  }

  // Extension Management

  /**
   * Get list of available tools.
   */
  async getTools(): Promise<any[]> {
    return this.request('GET', '/agent/tools');
  }

  /**
   * Add an extension to the agent.
   */
  async addExtension(extension: Extension): Promise<string> {
    const payload: Record<string, any> = {
      name: extension.name,
      type: extension.type,
    };

    if (extension.cmd) payload.cmd = extension.cmd;
    if (extension.args) payload.args = extension.args;
    if (extension.envs) payload.envs = extension.envs;
    if (extension.timeout) payload.timeout = extension.timeout;
    if (extension.bundled !== undefined) payload.bundled = extension.bundled;

    return this.request('POST', '/agent/add_extension', {
      body: JSON.stringify(payload),
    });
  }

  /**
   * Remove an extension from the agent.
   */
  async removeExtension(name: string): Promise<string> {
    return this.request('POST', '/agent/remove_extension', {
      body: JSON.stringify({ name }),
    });
  }

  /**
   * List all available extensions.
   */
  async listExtensions(): Promise<any[]> {
    return this.request('GET', '/config/extensions');
  }

  // Session Management

  /**
   * List all sessions.
   */
  async listSessions(): Promise<Session[]> {
    const data = await this.request<{ sessions: any[] }>('GET', '/sessions');
    return data.sessions.map((s: any) => ({
      id: s.id,
      name: s.name,
      created: s.created,
      updated: s.updated,
      working_dir: s.working_dir,
    }));
  }

  /**
   * Get detailed session information.
   */
  async getSession(sessionId: string): Promise<any> {
    return this.request('GET', `/sessions/${sessionId}`);
  }

  /**
   * Update a session's name.
   */
  async updateSessionName(sessionId: string, name: string): Promise<void> {
    await this.request('POST', `/sessions/${sessionId}/name`, {
      body: JSON.stringify({ name }),
    });
  }

  /**
   * Delete a session.
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.request('DELETE', `/sessions/${sessionId}`);
  }

  /**
   * Export a session's data.
   */
  async exportSession(sessionId: string): Promise<any> {
    return this.request('GET', `/sessions/${sessionId}/export`);
  }

  /**
   * Get insights about all sessions (token usage, costs, etc.).
   */
  async getSessionInsights(): Promise<any> {
    return this.request('GET', '/sessions/insights');
  }

  // Configuration

  /**
   * Get list of available LLM providers.
   */
  async getProviders(): Promise<any[]> {
    return this.request('GET', '/config/providers');
  }

  /**
   * Get available models for a provider.
   */
  async getProviderModels(provider: string): Promise<string[]> {
    return this.request('GET', `/config/providers/${provider}/models`);
  }

  /**
   * Check server status.
   */
  async checkStatus(): Promise<any> {
    return this.request('GET', '/status');
  }
}

// Example usage
async function example() {
  const client = new GooseClient();

  // Check status
  const status = await client.checkStatus();
  console.log('Server status:', status);

  // Start agent
  console.log('\nStarting agent...');
  await client.startAgent({ provider: 'openai', model: 'gpt-4' });

  // List available extensions
  const extensions = await client.listExtensions();
  console.log(`\nAvailable extensions: ${extensions.length}`);

  // Send message
  console.log('\nSending message...');
  const sessionId = 'example-session';

  for await (const event of client.sendMessage(
    sessionId,
    'Write a simple hello world JavaScript function'
  )) {
    if (event.type === 'text' && event.message) {
      for (const content of event.message.content) {
        if (content.type === 'text') {
          console.log(`\nAgent: ${content.text}`);
        }
      }
    } else if (event.type === 'Finish') {
      console.log('\nConversation finished');
    }
  }
}

// Run example if this file is executed directly
if (require.main === module) {
  example().catch(console.error);
}
