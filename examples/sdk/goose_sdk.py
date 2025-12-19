"""
goose Python SDK

A simple Python SDK for integrating goose AI agent into your applications.

Example usage:
    from goose_sdk import GooseClient
    
    async with GooseClient("http://localhost:3001", "your-secret-key") as client:
        # Start agent
        await client.start_agent(provider="openai", model="gpt-4")
        
        # Send message and get response
        async for event in client.send_message("my-session", "Hello!"):
            if event.message:
                print(event.message)
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional, Union, Tuple
import httpx


@dataclass
class MessageContent:
    """Content of a message."""
    type: str
    text: str
    annotations: Optional[Dict[str, Any]] = None


@dataclass
class Message:
    """A message in the conversation."""
    role: str
    created: int
    content: List[MessageContent]


@dataclass
class Event:
    """An event from the agent response stream."""
    type: str
    message: Optional[Message] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class Extension:
    """Extension configuration."""
    name: str
    type: str
    cmd: Optional[str] = None
    args: Optional[List[str]] = None
    envs: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    bundled: Optional[bool] = None


@dataclass
class Session:
    """Session information."""
    id: str
    name: Optional[str] = None
    created: Optional[int] = None
    updated: Optional[int] = None
    working_dir: Optional[str] = None


class GooseClient:
    """
    Client for interacting with the goose HTTP API.
    
    Args:
        base_url: Base URL of the goose server (default: http://localhost:3001)
        secret_key: Authentication secret key (default: "test")
        timeout: Request timeout in seconds (default: 60.0)
    """
    
    # Default timeout for streaming operations
    STREAMING_TIMEOUT = 300.0
    
    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        secret_key: str = "test",
        timeout: float = 60.0
    ):
        self.base_url = base_url.rstrip('/')
        self.secret_key = secret_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    def _headers(self) -> Dict[str, str]:
        """Get default headers with authentication."""
        return {
            "X-Secret-Key": self.secret_key,
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """Make an HTTP request to the goose API."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}{path}"
        headers = self._headers()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        response = await self._client.request(
            method,
            url,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response
    
    # Agent Management
    
    async def start_agent(
        self,
        provider: str = "openai",
        model: str = "gpt-4",
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new agent session.
        
        Args:
            provider: LLM provider name (e.g., "openai", "anthropic")
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            working_dir: Working directory for the agent
            
        Returns:
            Agent initialization response
        """
        payload = {
            "provider": provider,
            "model": model
        }
        if working_dir:
            payload["working_dir"] = working_dir
        
        response = await self._request("POST", "/agent/start", json=payload)
        return response.json()
    
    async def resume_agent(self, session_id: str) -> Dict[str, Any]:
        """
        Resume an existing agent session.
        
        Args:
            session_id: ID of the session to resume
            
        Returns:
            Agent resume response
        """
        response = await self._request(
            "POST",
            "/agent/resume",
            json={"session_id": session_id}
        )
        return response.json()
    
    async def update_agent_provider(
        self,
        provider: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Update the agent's LLM provider and model.
        
        Args:
            provider: New provider name
            model: New model name
            
        Returns:
            Update response
        """
        response = await self._request(
            "POST",
            "/agent/update_provider",
            json={"provider": provider, "model": model}
        )
        return response.json()
    
    # Messaging
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        working_dir: str = "."
    ) -> AsyncIterator[Event]:
        """
        Send a message to the agent and stream the response.
        
        Args:
            session_id: Session ID
            message: Message text
            working_dir: Working directory for the session
            
        Yields:
            Event objects from the agent response stream
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        payload = {
            "messages": [{
                "role": "user",
                "created": int(datetime.now().timestamp()),
                "content": [{"type": "text", "text": message}]
            }],
            "session_id": session_id,
            "session_working_dir": working_dir
        }
        
        headers = self._headers()
        headers["Accept"] = "text/event-stream"
        
        async with self._client.stream(
            "POST",
            f"{self.base_url}/reply",
            json=payload,
            headers=headers,
            timeout=self.STREAMING_TIMEOUT
        ) as stream:
            async for line in stream.aiter_lines():
                if not line:
                    continue
                
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        event = Event(type=data.get("type", "Unknown"), raw=data)
                        
                        if data.get("type") == "Finish":
                            yield event
                            break
                        
                        if "message" in data:
                            msg_data = data["message"]
                            content = []
                            for c in msg_data.get("content", []):
                                content.append(MessageContent(
                                    type=c.get("type"),
                                    text=c.get("text", ""),
                                    annotations=c.get("annotations")
                                ))
                            event.message = Message(
                                role=msg_data.get("role"),
                                created=msg_data.get("created"),
                                content=content
                            )
                        
                        yield event
                    except json.JSONDecodeError:
                        continue
    
    # Extension Management
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools.
        
        Returns:
            List of tool definitions
        """
        response = await self._request("GET", "/agent/tools")
        return response.json()
    
    async def add_extension(self, extension: Extension) -> str:
        """
        Add an extension to the agent.
        
        Args:
            extension: Extension configuration
            
        Returns:
            Success message
        """
        payload = {
            "name": extension.name,
            "type": extension.type
        }
        if extension.cmd:
            payload["cmd"] = extension.cmd
        if extension.args:
            payload["args"] = extension.args
        if extension.envs:
            payload["envs"] = extension.envs
        if extension.timeout:
            payload["timeout"] = extension.timeout
        if extension.bundled is not None:
            payload["bundled"] = extension.bundled
        
        response = await self._request("POST", "/agent/add_extension", json=payload)
        return response.text
    
    async def remove_extension(self, name: str) -> str:
        """
        Remove an extension from the agent.
        
        Args:
            name: Extension name
            
        Returns:
            Success message
        """
        response = await self._request(
            "POST",
            "/agent/remove_extension",
            json={"name": name}
        )
        return response.text
    
    async def list_extensions(self) -> List[Dict[str, Any]]:
        """
        List all available extensions.
        
        Returns:
            List of extension configurations
        """
        response = await self._request("GET", "/config/extensions")
        return response.json()
    
    # Session Management
    
    async def list_sessions(self) -> List[Session]:
        """
        List all sessions.
        
        Returns:
            List of Session objects
        """
        response = await self._request("GET", "/sessions")
        data = response.json()
        
        sessions = []
        for session_data in data.get("sessions", []):
            sessions.append(Session(
                id=session_data["id"],
                name=session_data.get("name"),
                created=session_data.get("created"),
                updated=session_data.get("updated"),
                working_dir=session_data.get("working_dir")
            ))
        return sessions
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session details including conversation history
        """
        response = await self._request("GET", f"/sessions/{session_id}")
        return response.json()
    
    async def update_session_name(self, session_id: str, name: str) -> None:
        """
        Update a session's name.
        
        Args:
            session_id: Session ID
            name: New session name
        """
        await self._request(
            "POST",
            f"/sessions/{session_id}/name",
            json={"name": name}
        )
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
        """
        await self._request("DELETE", f"/sessions/{session_id}")
    
    async def export_session(self, session_id: str) -> Dict[str, Any]:
        """
        Export a session's data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Exported session data
        """
        response = await self._request("GET", f"/sessions/{session_id}/export")
        return response.json()
    
    async def get_session_insights(self) -> Dict[str, Any]:
        """
        Get insights about all sessions (token usage, costs, etc.).
        
        Returns:
            Session insights data
        """
        response = await self._request("GET", "/sessions/insights")
        return response.json()
    
    # Configuration
    
    async def get_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of available LLM providers.
        
        Returns:
            List of provider configurations
        """
        response = await self._request("GET", "/config/providers")
        return response.json()
    
    async def get_provider_models(self, provider: str) -> List[str]:
        """
        Get available models for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            List of model names
        """
        response = await self._request("GET", f"/config/providers/{provider}/models")
        return response.json()
    
    async def check_status(self) -> Dict[str, Any]:
        """
        Check server status.
        
        Returns:
            Status information
        """
        response = await self._request("GET", "/status")
        return response.json()


# Example usage
async def example():
    """Example usage of the goose SDK."""
    async with GooseClient() as client:
        # Check status
        status = await client.check_status()
        print(f"Server status: {status}")
        
        # Start agent
        print("\nStarting agent...")
        await client.start_agent(provider="openai", model="gpt-4")
        
        # List available extensions
        extensions = await client.list_extensions()
        print(f"\nAvailable extensions: {len(extensions)}")
        
        # Send message
        print("\nSending message...")
        session_id = "example-session"
        
        async for event in client.send_message(
            session_id,
            "Write a simple hello world Python script"
        ):
            if event.type == "text" and event.message:
                for content in event.message.content:
                    if content.type == "text":
                        print(f"\nAgent: {content.text}")
            elif event.type == "Finish":
                print("\nConversation finished")


if __name__ == "__main__":
    asyncio.run(example())
