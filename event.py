from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib

@dataclass(eq=False, repr=True)
class Event:
    id: str
    system: str
    summary: str
    start: datetime
    end: datetime
    location: str
    response_type: str
    body: str = field(init=False, repr=False)
    hash_id: str = field(init=False, repr=False)
    exchange_changekey: str | None = None
    is_external: bool = False

    def __post_init__(self):
        self.hash_id = self._calculate_id()

    def _calculate_id(self) -> str:
        payload = {
            "summary": self.summary,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "response_type": self.response_type
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

