from pathlib import Path

import openai
from a0g import A0G
import dotenv

dotenv.load_dotenv()

a0g = A0G()
service = a0g.get_all_services()[0]
obj = a0g.upload_to_storage(Path(__file__))
print(obj)
print(a0g.download_from_storage(obj, Path("1.py")))
