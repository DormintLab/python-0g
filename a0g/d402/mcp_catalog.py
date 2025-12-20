from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..base import A0G


@dataclass
class MCPServerInfo:
    sse_url: str
    rating: Optional[int] = None
    updated_at: Optional[datetime] = None
    comments: Optional[List[str]] = None


class MCPCatalog:
    def __init__(self, a0g: A0G,
                 root_hash: str):
        self.a0g = a0g
        self.root_hash = root_hash

    async def search(self, query: str) -> List[MCPServerInfo]:
        pass

    async def get_rating(self, sse_url: str) -> MCPServerInfo:
        pass

    async def feedback_and_refund(self, sse_url: str, rating: int, comment: str):
        pass
