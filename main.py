import os
from dotenv import load_dotenv
from fastapi import FastAPI
from search_employee import search_router

app = FastAPI()
load_dotenv()

# Include the search_employee router
app.include_router(search_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
