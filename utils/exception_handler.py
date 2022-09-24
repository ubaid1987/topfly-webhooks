from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from .resp import TopflyResponse


class TopflyException(Exception):
    def __init__(self, message: str, data: dict = {}, send_sentry: bool = False):
        self.message = message
        self.data = data
        self.send_sentry = send_sentry


def add_topfly_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(TopflyException)
    async def topfly_exception_handler(request: Request, exc: TopflyException):
        if exc.send_sentry:
            pass
        return TopflyResponse(
            status_code=400,
            message=exc.message,
            data=exc.data,
        )
