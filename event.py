from dataclasses import dataclass, field
from datetime import datetime


@dataclass(eq=False, repr=True)
class Event:
    id: str
    system: str
    external_id: str = field(init=False, repr=False)
    external_system: str = field(init=False, repr=False)
    summary: str
    start: datetime
    end: datetime
    location: str
    response_type: str
    body: str = field(init=False, repr=False)
