from fastapi import FastAPI

app = FastAPI(title="Warhammer 40k LOS Analyzer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
