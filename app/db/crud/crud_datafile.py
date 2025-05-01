# app/db/crud/crud_datafile.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.db.models import DataFile
from app.schemas.datafile import DataFileCreate


async def get_datafile_by_orthanc_id(db: AsyncSession, orthanc_id: str) -> DataFile | None:
    result = await db.execute(select(DataFile).where(DataFile.orthanc_id == orthanc_id))
    return result.scalars().first()

async def create_datafile(db: AsyncSession, data_in, *, orthanc_id: str | None, storage_path: str | None):
    df = DataFile(**data_in.model_dump(exclude_none=True), orthanc_id=orthanc_id, storage_path=storage_path)
    db.add(df)
    try:
        await db.commit()
        await db.refresh(df)
    except IntegrityError as e:
        await db.rollback()
        # If it’s a duplicate‐orthanc_id error, rethrow so the router can translate to 409
        if "duplicate key value violates unique constraint" in str(e.orig):
            raise
        raise
    return df

async def list_datafiles(db: AsyncSession) -> list[DataFile]:
    result = await db.execute(select(DataFile))
    return result.scalars().all()
