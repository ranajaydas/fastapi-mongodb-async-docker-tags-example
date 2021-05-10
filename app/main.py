from fastapi import FastAPI

from .database import startup_db_client, shutdown_db_client, os
from .views import router

# Initialize FastAPI
app = FastAPI()
app.include_router(router=router, prefix='/v1')
app.add_event_handler('startup', startup_db_client)
app.add_event_handler('shutdown', shutdown_db_client)
