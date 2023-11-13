# main.py

from fastapi import FastAPI
from app.api.auth import register, login  # Import the routers

app = FastAPI()

# Include the routers in the app
app.include_router(register.router, prefix="/auth", tags=["auth"])
app.include_router(login.router, prefix="/auth", tags=["auth"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
