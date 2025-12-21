import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from ..base import A0G


@dataclass
class MCPServerInfo:
    sse_url: str
    rating: Optional[int] = None
    updated_at: Optional[datetime] = None
    comments: Optional[List[str]] = None


class MCPCatalog:
    def __init__(self, a0g: A0G):
        self.a0g = a0g
        self.ca = "0x0f6d71111ca628a799c849d554b6096906397b7e"

    async def search(self, query: str) -> List[MCPServerInfo]:
        meta_info = json.dumps({"query": query,
                                "timestamp": datetime.now(tz=timezone.utc).timestamp()})
        receipt = self.a0g.pay(self.ca, 0.1,
                               meta_info=meta_info)

        return []

    async def get_rating(self, sse_url: str) -> MCPServerInfo:
        pass

    async def feedback_and_refund(self, sse_url: str, rating: int, comment: str):
        pass
