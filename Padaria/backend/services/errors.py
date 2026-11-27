class BusinessError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message, self.status = message, status


class NotFound(BusinessError):
    def __init__(self, what: str = "Registro"):
        super().__init__(f"{what} não encontrado", 404)
