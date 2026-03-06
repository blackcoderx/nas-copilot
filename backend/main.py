from fastapi import FastAPI

app = FastAPI(title="NAS Copilot", version="0.1.0")


@app.get("/")
def root():
    return {"message": "NAS Copilot API is running"}
