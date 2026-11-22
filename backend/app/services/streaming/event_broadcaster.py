import asyncio
import json
import time
from typing import Dict, Set, AsyncGenerator, Any

class EventBroadcaster:
    """Manages real-time Server-Sent Events (SSE) subscriptions for live agent progress."""
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}  # task_id -> set of subscriber queues
        self._event_counter = 0

    def subscribe(self, task_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if task_id not in self._subscribers:
            self._subscribers[task_id] = set()
        self._subscribers[task_id].add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        if task_id in self._subscribers:
            self._subscribers[task_id].discard(queue)
            if not self._subscribers[task_id]:
                del self._subscribers[task_id]

    async def broadcast(self, task_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcasts a genuine agent lifecycle event to all subscribed connections."""
        if task_id not in self._subscribers:
            return

        self._event_counter += 1
        payload = {
            "event_id": self._event_counter,
            "task_id": task_id,
            "event_type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        raw_msg = f"id: {self._event_counter}\nevent: {event_type}\ndata: {json.dumps(payload)}\n\n"

        for queue in list(self._subscribers[task_id]):
            try:
                queue.put_nowait(raw_msg)
            except asyncio.QueueFull:
                pass

    async def event_generator(self, task_id: str, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """Yields SSE-formatted messages with periodic keep-alive heartbeats."""
        try:
            # Yield initial connection confirmation
            yield f": connected to task {task_id}\n\n"

            while True:
                try:
                    # Wait up to 15s for new event, otherwise emit ping heartbeat
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield f": ping {int(time.time())}\n\n"
        finally:
            self.unsubscribe(task_id, queue)

broadcaster = EventBroadcaster()

