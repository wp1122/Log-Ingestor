from pydantic import BaseModel


class LogModel(BaseModel):
    level: str = None
    message: str = None
    resourceId: str = None
    timestamp: str = None
    traceId: str = None
    spanId: str = None
    commit: str = None
    metadata: dict = None


class SearchLogModel(BaseModel):
    query_string: str = None
    start_timestamp: str = None
    end_timestamp: str = None
    query: LogModel = None
    limit: int = 100
    offset: int = 0
