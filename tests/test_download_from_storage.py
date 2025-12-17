from pathlib import Path

import openai
from a0g import A0G
import dotenv

from a0g.types.storage import ZGStorageObject

dotenv.load_dotenv()



a0g = A0G()
a0g.download_from_storage(ZGStorageObject(root_hash="0x09527e9ba70e1eb55a776eaa5149bf36a79ace6490fe82660e44aa8ecba616da",
                                          tx_hash=""),
                          Path("1.txt"))
