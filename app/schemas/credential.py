from pydantic import BaseModel


class NFCAssign(BaseModel):
    nfc_tag_uid: str
