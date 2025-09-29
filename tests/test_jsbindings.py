import time
from pathlib import Path
import execjs


ctx = execjs.compile(Path("./a0g/jsbindings/dist/bundle.js").read_text())

# Ждём инициализацию
timeout = 5.0  # секунд
interval = 0.05
elapsed = 0.0

while not ctx.call("isReady"):
    time.sleep(interval)
    elapsed += interval
    if elapsed > timeout:
        raise TimeoutError("Pedersen hash initialization timed out")

# Теперь можно безопасно вызывать
msg = [0, 0]
result = ctx.call("pedersenHashSync", msg)
print(result)
