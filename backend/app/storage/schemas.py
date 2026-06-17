from pydantic import BaseModel


class SignUploadRequest(BaseModel):
    filename: str
    content_type: str


class SignUploadResponse(BaseModel):
    key: str
    upload_url: str
    expires_in: int


class FinalizeRequest(BaseModel):
    key: str


class FinalizeResponse(BaseModel):
    url: str
    content_type: str
    width: int
    height: int
    size_bytes: int
