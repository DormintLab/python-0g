import json
import os
from pathlib import Path
from typing import List, Literal, Optional

import web3
from eth_account.signers.local import LocalAccount
from javascript import require
from openai import AsyncOpenAI, OpenAI
from web3.types import ENS

from .contract import get_abi, get_ca
from .types.account import AccountStructOutput
from .types.ledger import LedgerStructOutput
from .types.model import ServiceMetadata, ServiceStructOutput


class A0G:
    bundle = require(str(Path(__file__).parent / "jsbindings/dist/bundle.js"))

    def __init__(
        self,
        private_key: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        if private_key is None:
            private_key = os.environ.get("A0G_PRIVATE_KEY")
            if private_key is None:
                raise Exception("Private key is required")

        if rpc_url is None:
            rpc_url = os.environ.get("A0G_RPC_URL")
            if rpc_url is None:
                rpc_url = "https://evmrpc-testnet.0g.ai"

        self.rpc_url = rpc_url

        self.w3 = self.get_w3(rpc_url)
        self.inference_contract = self.get_contract(self.w3, "inference")
        self.ledger_contract = self.get_contract(self.w3, "ledger")

        self.account: LocalAccount = self.w3.eth.account.from_key(private_key)

    def get_openai_client(self, provider: ENS):
        privider_metadata = self.get_service_metadata(provider)
        if not privider_metadata["success"]:
            raise Exception(f"Provider {provider} is not available")
        return OpenAI(
            api_key="",
            base_url=privider_metadata["endpoint"],
            default_headers=privider_metadata["headers"],
        )

    def get_openai_async_client(self, provider: ENS):
        privider_metadata = self.get_service_metadata(provider)
        if not privider_metadata["success"]:
            raise Exception(f"Provider {provider} is not available")
        return AsyncOpenAI(
            api_key="",
            base_url=privider_metadata["endpoint"],
            default_headers=privider_metadata["headers"],
        )

    def get_service_metadata(self, provider: ENS) -> ServiceMetadata:
        obj = self.bundle.getOpenAIHeadersDemo(
            self.account.key.hex(),
            "Dummy content",
            provider,
            self.rpc_url,
            timeout=100000,
        )
        return json.loads(obj)

    def get_balance(self) -> int:
        balance_wei = self.w3.eth.get_balance(self.account.address)
        return self.w3.from_wei(balance_wei, "ether")

    def get_ledger_inference_address(self):
        return self.ledger_contract.functions.inferenceAddress().call()

    def get_ledger_owner_address(self):
        return self.ledger_contract.functions.owner().call()

    def get_ledger(self) -> LedgerStructOutput:
        try:
            raw = self.ledger_contract.functions.getLedger(self.account.address).call()
            return LedgerStructOutput(
                user=raw[0],
                availableBalance=raw[1],
                totalBalance=raw[2],
                inferenceSigner=raw[3],
                additionalInfo=raw[4],
                inferenceProviders=raw[5],
                fineTuningProviders=raw[6],
            )
        except Exception as e:
            print(e)
            # TODO: Add ledger

    def get_account(self, provider: ENS) -> AccountStructOutput:
        raw = self.inference_contract.functions.getAccount(
            self.account.address, provider
        ).call()
        return raw

    def get_service(self, provider: ENS) -> ServiceStructOutput:
        obj = self.inference_contract.functions.getService(provider).call()
        return ServiceStructOutput(
            provider=obj[0],
            serviceType=obj[1],
            url=obj[2],
            inputPrice=obj[3],
            outputPrice=obj[4],
            updatedAt=obj[5],
            model=obj[6],
            verifiability=obj[7],
            additionalInfo=obj[8],
        )

    def get_all_services(self) -> List[ServiceStructOutput]:
        raw = self.inference_contract.functions.getAllServices.call()
        return [
            ServiceStructOutput(
                provider=obj[0],
                serviceType=obj[1],
                url=obj[2],
                inputPrice=obj[3],
                outputPrice=obj[4],
                updatedAt=obj[5],
                model=obj[6],
                verifiability=obj[7],
                additionalInfo=obj[8],
            )
            for obj in raw
        ]

    def get_w3(self, rpc_url):
        w3 = web3.Web3(web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception(f"RPC URL {rpc_url} is not working")
        return w3

    def get_contract(self, w3: web3.Web3, name: Literal["inference", "ledger"]):
        contract = w3.eth.contract(address=ENS(get_ca(name)), abi=get_abi(name))
        return contract
