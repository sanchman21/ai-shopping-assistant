from pydantic import BaseModel


class ChoicesResponse(BaseModel):
    choices: list[str]