from pydantic import BaseModel
from typing import List, Tuple


class LedgerStructOutput(BaseModel):
    user: str
    availableBalance: int       # bigint → Python int
    totalBalance: int           # bigint → Python int
    inferenceSigner: Tuple[int, int]
    additionalInfo: str
    inferenceProviders: List[str]
    fineTuningProviders: List[str]
