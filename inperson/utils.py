import hashlib
import base64

def generate_hash(solver_group_code, owner_group_code):
    combined = f"{solver_group_code}:{owner_group_code}"
    raw = hashlib.sha256(combined.encode()).digest()
    b64 = base64.b64encode(raw).decode()
    b64 = b64.replace("+", "-").replace("/", "_").replace("=", "")
    if len(b64) >= 10:
        return b64[:10]
    else:
        return b64 + "-" * (10 - len(b64))