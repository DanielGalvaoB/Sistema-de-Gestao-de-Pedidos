from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT


class BusinessRuleError(DomainError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code, content={'detail': exc.detail}
        )

    @app.exception_handler(IntegrityError)
    async def _integrity(request: Request, exc: IntegrityError):
        # Nao expoe a mensagem interna do banco
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'detail': 'Operacao viola uma restricao de integridade '
                '(registro duplicado ou referencia invalida).'
            },
        )
