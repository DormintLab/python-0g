from typing import TypedDict, Tuple


class SettleSignerKey(TypedDict):
    settleSignerPublicKey: Tuple[int, int]
    settleSignerEncryptedPrivateKey: str
