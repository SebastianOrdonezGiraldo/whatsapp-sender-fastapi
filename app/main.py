from fastapi. middleware.cors import CORSMiddleware

import app
from migrations.env import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings. cors_origins_list,  # Usa . cors_origins_list
    # ...
)