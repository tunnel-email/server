from pydantic import BaseModel, validator
from string import ascii_lowercase, digits

from dotenv import load_dotenv
from os import getenv

class Token(BaseModel):
    token: str

    @validator("token")
    def token_validator(cls, tok):
        token_length = int(getenv("TOKEN_LENGTH"))

        if len(tok) != token_length:
            raise ValueError(f"Token must be exactly {token_length} characters long")

        for i in tok:
            if not i in ascii_lowercase + digits:
                raise ValueError("Invalid symbol in token")
        
        return tok


class HTTP01_Data(Token):
    url_token: str
    validation_token: str

    # TODO: validators
