import secrets

def generate_worker_token() -> str:
    return f"reson_w_{secrets.token_urlsafe(32)}"