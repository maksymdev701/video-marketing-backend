from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

origins = ["http://localhost:3000"]
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=9000)
