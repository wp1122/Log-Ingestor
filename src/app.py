from elasticsearch8 import Elasticsearch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.base import LogModel, SearchLogModel
from datetime import datetime

INDEX_NAME = "logs"

es = Elasticsearch("http://localhost:9200")

app = FastAPI(
    title="Log Ingestor and Query Interface",
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/logs")
async def add_log(request: LogModel):
    document = {
        "level": request.level,
        "message": request.message,
        "resourceId": request.resourceId,
        "timestamp": datetime.strptime(request.timestamp, "%Y-%m-%dT%H:%M:%SZ"),
        "traceId": request.traceId,
        "spanId": request.spanId,
        "commit": request.commit,
        "metadata": request.metadata,
    }

    es.index(index=INDEX_NAME, body=document)
    return {"status": "ok"}


@app.post("/logs/search")
async def search_logs(request: SearchLogModel):
    musts = []

    if request.query:
        matches = {}
        for key, value in request.query.model_dump().items():
            if value:
                if type(value) == str:
                    matches[key] = {"query": value}
                elif type(value) == dict:
                    for k, v in value.items():
                        if v:
                            matches[f"{key}.{k}"] = {"query": v}

        for field, query in matches.items():
            musts.append({"match": {field: query}})

    if request.start_timestamp and request.end_timestamp:
        musts.append(
            {
                "range": {
                    "timestamp": {
                        "gte": datetime.strptime(
                            request.start_timestamp, "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "lte": datetime.strptime(
                            request.end_timestamp, "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    }
                }
            }
        )

    if request.query_string:
        musts.append(
            {
                "multi_match": {
                    "query": request.query_string,
                    "fields": [
                        "level",
                        "message",
                        "resourceId",
                        "traceId",
                        "spanId",
                        "commit",
                        "metadata.parentResourceId",
                    ],
                }
            }
        )

    if len(musts) == 0:
        raise HTTPException(
            status_code=400, detail="None of the search parameters passed"
        )

    results = es.search(
        index=INDEX_NAME,
        from_=request.offset,
        size=request.limit,
        query={"bool": {"should": musts}},
    )

    hits = results["hits"]["hits"]
    logs = [LogModel.model_validate(hit["_source"]).model_dump() for hit in hits]

    return {"logs": logs, "total": results["hits"]["total"]["value"]}
