import asyncio

from a0g.d402.mcp_catalog import MCPCatalog
from a0g import A0G
import dotenv

dotenv.load_dotenv()

a0g = A0G()

catalog = MCPCatalog(a0g=a0g)
print(asyncio.run(catalog.search("test")))
