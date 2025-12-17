from pydantic import BaseModel


class ZGStorageObject(BaseModel):
    tx_hash: str
    root_hash: str
