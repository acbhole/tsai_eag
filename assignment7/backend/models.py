from pydantic import BaseModel


class URLRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    query: str
    k: int = 5