from collections import defaultdict, deque
from typing import Deque, Dict, Optional

# chat_id -> deque of track dicts {title, duration, path, url, requested_by}
_queues: Dict[int, Deque[dict]] = defaultdict(deque)
_now_playing: Dict[int, Optional[dict]] = {}


def push(chat_id: int, track: dict) -> int:
    _queues[chat_id].append(track)
    return len(_queues[chat_id])


def pop(chat_id: int) -> Optional[dict]:
    q = _queues[chat_id]
    return q.popleft() if q else None


def peek_all(chat_id: int):
    return list(_queues[chat_id])


def clear(chat_id: int) -> None:
    _queues[chat_id].clear()
    _now_playing.pop(chat_id, None)


def set_now(chat_id: int, track: Optional[dict]) -> None:
    _now_playing[chat_id] = track


def now(chat_id: int) -> Optional[dict]:
    return _now_playing.get(chat_id)


def is_active(chat_id: int) -> bool:
    return _now_playing.get(chat_id) is not None
