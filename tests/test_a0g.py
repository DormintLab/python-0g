import openai
from a0g import A0G
import dotenv

dotenv.load_dotenv()

a0g = A0G()
service = a0g.get_all_services()[1]
client: openai.OpenAI = a0g.get_openai_client(service.provider)

print(client.chat.completions.create(messages=[
    {"role": "user", "content": "Hello, how are you?"}
], model=service.model))
print(client.chat.completions.create(messages=[
    {"role": "user", "content": "What is the meaning of life?"}
], model=service.model))

print(client.chat.completions.create(messages=[
    {"role": "user", "content": "What is 0g.ai ?"}
], model=service.model))
