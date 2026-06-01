from pydantic import BaseModel
from typing import Literal


class VerifyRequest(BaseModel):
    credential_type: Literal["qr", "nfc"]
    credential_value: str
    gate_id: str
    action: Literal["entry", "exit"] = "entry"
