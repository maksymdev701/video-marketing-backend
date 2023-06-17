from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from routers import auth, user

origins = [settings.CLIENT_ORIGIN]
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user.router, prefix="/api/user", tags=["User"])

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=9000)
