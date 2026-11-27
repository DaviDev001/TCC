from fastapi import Header


def current_user(x_user: str = Header("beta-1")) -> str:
    """PLACEHOLDER: trocar por JWT/sessão + papéis (vendedor, gerente, admin)."""
    return x_user
