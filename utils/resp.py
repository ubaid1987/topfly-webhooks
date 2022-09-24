from fastapi.responses import JSONResponse
import json


def TopflyResponse(status_code: int = 200, message: str = "", data={}):
    return JSONResponse(
        status_code=status_code,
        content={
            "message": message,
            "data": data,
        },
    )
