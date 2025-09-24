"""
Data ingestion endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any

from app.database import get_db
from app.services import DataIngestionService

router = APIRouter()


class IngestResponse(BaseModel):
    """Response for ingestion operations"""
    message: str
    records_inserted: int = 0
    records_updated: int = 0


@router.post("/trains", summary="Ingest trains data from CSV")
async def ingest_trains_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Ingest trains data from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    csv_content = content.decode('utf-8')

    ingestion_service = DataIngestionService(db)
    try:
        result = await ingestion_service.ingest_trains_csv(csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/fitness-certificates", summary="Ingest fitness certificates from CSV")
async def ingest_fitness_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Ingest fitness certificates from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    csv_content = content.decode('utf-8')

    ingestion_service = DataIngestionService(db)
    try:
        result = await ingestion_service.ingest_fitness_certificates_csv(csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/job-cards", summary="Ingest job cards from CSV")
async def ingest_job_cards_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Ingest job cards from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    csv_content = content.decode('utf-8')

    ingestion_service = DataIngestionService(db)
    try:
        result = await ingestion_service.ingest_job_cards_csv(csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/mileage", summary="Ingest mileage data from CSV")
async def ingest_mileage_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Ingest mileage data from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    csv_content = content.decode('utf-8')

    ingestion_service = DataIngestionService(db)
    try:
        result = await ingestion_service.ingest_mileage_csv(csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/branding-exposure", summary="Ingest branding exposure data from CSV")
async def ingest_branding_exposure_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Ingest branding exposure data from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    csv_content = content.decode('utf-8')

    ingestion_service = DataIngestionService(db)
    try:
        result = await ingestion_service.ingest_branding_exposure_csv(csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/templates", summary="Get CSV templates")
async def get_csv_templates():
    """Get sample CSV templates for data ingestion"""
    ingestion_service = DataIngestionService(None)  # No DB needed for templates
    templates = await ingestion_service.get_sample_csv_templates()
    return templates
