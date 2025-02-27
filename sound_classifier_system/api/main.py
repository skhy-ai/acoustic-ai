import uvicorn
from fastapi import FastAPI
from api.endpoints import router as api_router

app = FastAPI()
app.include_router(api_router)

if __name__ == "__main__":
    print("Run API Server (A) or test (T):")
    choice = input().strip()
    if choice == "A":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Implement any test logic or CLI-based operations here.
        print("Running in test mode...")
