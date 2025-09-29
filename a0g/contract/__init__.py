import json
import os
from pathlib import Path
from typing import Literal


def get_abi(name: Literal["inference", "ledger"]):
    return json.loads((Path(__file__).parent / f"{name}_abi.json").read_text())


def get_ca(name: Literal["inference", "ledger"]):
    if name == "inference":
        return os.environ.get(
            "A0G_INFERENCE_CA", "0x192ff84e5E3Ef3A6D29F508a56bF9beb344471f3"
        )

    elif name == "ledger":
        return os.environ.get(
            "A0G_LEDGER_CA", "0x907a552804CECC0cBAeCf734E2B9E45b2FA6a960"
        )

    raise RuntimeError(f"No contract address found with name: {name}")
