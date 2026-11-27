from fastapi import Header


def current_user(x_user: str = Header("system")) -> str:
    """PLACEHOLDER: trocar por JWT/sessão + papéis (caixa, gerente, admin)."""
    return x_user
