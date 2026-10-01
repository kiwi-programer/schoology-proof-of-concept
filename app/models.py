from pydantic import BaseModel

class GetRequest(BaseModel):
    path: str  # "/v1/..." or full https://api.schoology.com/v1/... URL