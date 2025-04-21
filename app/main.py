from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth, admin
from app.db.database import async_session
from app.db.models import Role
from app.db.crud.crud_role import get_role_by_name
from app.core.constants import DefaultRoles

app = FastAPI()

# CORS configuration (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication and admin routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

# Startup event: seed default roles if they don't exist
@app.on_event("startup")
async def seed_roles():
    async with async_session() as db:
        missing = []
        for role_name in (role.value for role in DefaultRoles):
            if not await get_role_by_name(db, role_name):
                missing.append(Role(name=role_name))
        if missing:
            for role in missing:
                db.add(role)
            await db.commit()
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
