import os
import sys

from javascript import require
import dotenv
from a0g import A0G
dotenv.load_dotenv()
os.environ["REQ_TIMEOUT"] = "0"

a0g = A0G()
service = a0g.get_all_services()[1]
print(service, file=sys.stderr)
bundle = require("../a0g/jsbindings/dist/bundle.js")

private_key = os.environ.get("A0G_PRIVATE_KEY")
print(bundle.getOpenAIHeadersDemo(private_key, "Dummy content", service.provider, a0g.rpc_url,
                                  timeout=100000))
