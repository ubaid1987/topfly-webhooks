from fastapi import FastAPI, Request

from .resp import TopflyResponse
from sentry_sdk import capture_exception


class TopflyException(Exception):
    def __init__(
        self, message: str, data: dict = {}, status_code=400, send_sentry: bool = False
    ):
        self.message = message
        self.data = data
        self.send_sentry = send_sentry
        self.status_code = status_code

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, data={self.data!r}, message={self.message!r})"


def add_topfly_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(TopflyException)
    async def topfly_exception_handler(request: Request, exc: TopflyException):
        if exc.send_sentry:
            capture_exception(exc)
        return TopflyResponse(
            status_code=exc.status_code,
            message=exc.message,
            data=exc.data,
        )
