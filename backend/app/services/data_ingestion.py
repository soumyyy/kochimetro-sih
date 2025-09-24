"""
Data Ingestion Service
Handles CSV file ingestion for MVP
"""
import csv
import io
from typing import Dict, Any, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from ..models import (
    Train, FitnessCertificate, JobCard, BrandingCampaign,
    BrandingExposureLog, MileageLog, StablingBay, Depot
)


class DataIngestionService:
    """Service for ingesting data from CSV files"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_trains_csv(self, csv_content: str) -> Dict[str, Any]:
        """Ingest trains data from CSV"""
        reader = csv.DictReader(io.StringIO(csv_content))
        trains_inserted = 0
        trains_updated = 0

        for row in reader:
            train_id = row.get('train_id')
            if not train_id:
                continue

            # Check if train exists
            existing = await self.db.execute(
                select(Train).where(Train.train_id == train_id)
            )
            train = existing.scalar_one_or_none()

            train_data = {
                'train_id': train_id,
                'car_count': int(row.get('car_count', 4)),
                'brand_code': row.get('brand_code'),
                'wrap_id': row.get('wrap_id'),
                'status': row.get('status', 'standby'),
                'current_bay': row.get('current_bay'),
                'notes': row.get('notes')
            }

            if train:
                # Update existing
                for key, value in train_data.items():
                    setattr(train, key, value)
                trains_updated += 1
            else:
                # Create new
                new_train = Train(**train_data)
                self.db.add(new_train)
                trains_inserted += 1

        await self.db.commit()
        return {
            'message': 'Trains data ingested successfully',
            'trains_inserted': trains_inserted,
            'trains_updated': trains_updated
        }

    async def ingest_fitness_certificates_csv(self, csv_content: str) -> Dict[str, Any]:
        """Ingest fitness certificates from CSV"""
        reader = csv.DictReader(io.StringIO(csv_content))
        certificates_inserted = 0

        for row in reader:
            cert_data = {
                'train_id': row.get('train_id'),
                'dept': row.get('dept'),
                'valid_from': datetime.fromisoformat(row.get('valid_from')),
                'valid_to': datetime.fromisoformat(row.get('valid_to')),
                'status': row.get('status', 'valid'),
                'source_ref': row.get('source_ref')
            }

            if cert_data['train_id'] and cert_data['dept']:
                new_cert = FitnessCertificate(**cert_data)
                self.db.add(new_cert)
                certificates_inserted += 1

        await self.db.commit()
        return {
            'message': 'Fitness certificates ingested successfully',
            'certificates_inserted': certificates_inserted
        }

    async def ingest_job_cards_csv(self, csv_content: str) -> Dict[str, Any]:
        """Ingest job cards from CSV"""
        reader = csv.DictReader(io.StringIO(csv_content))
        jobs_inserted = 0

        for row in reader:
            job_data = {
                'job_id': row.get('job_id'),
                'train_id': row.get('train_id'),
                'source': row.get('source', 'manual'),
                'status': row.get('status', 'open'),
                'priority': int(row.get('priority', 3)) if row.get('priority') else None,
                'due_date': datetime.fromisoformat(row.get('due_date')).date() if row.get('due_date') else None,
                'ibl_required': row.get('ibl_required', 'false').lower() == 'true',
                'title': row.get('title'),
                'details': row.get('details')
            }

            if job_data['job_id'] and job_data['train_id']:
                new_job = JobCard(**job_data)
                self.db.add(new_job)
                jobs_inserted += 1

        await self.db.commit()
        return {
            'message': 'Job cards ingested successfully',
            'jobs_inserted': jobs_inserted
        }

    async def ingest_mileage_csv(self, csv_content: str) -> Dict[str, Any]:
        """Ingest mileage data from CSV"""
        reader = csv.DictReader(io.StringIO(csv_content))
        records_inserted = 0

        for row in reader:
            mileage_data = {
                'train_id': row.get('train_id'),
                'log_date': datetime.fromisoformat(row.get('log_date')).date(),
                'km_run': float(row.get('km_run', 0))
            }

            if mileage_data['train_id'] and mileage_data['log_date']:
                new_mileage = MileageLog(**mileage_data)
                self.db.add(new_mileage)
                records_inserted += 1

        await self.db.commit()
        return {
            'message': 'Mileage data ingested successfully',
            'records_inserted': records_inserted
        }

    async def ingest_branding_exposure_csv(self, csv_content: str) -> Dict[str, Any]:
        """Ingest branding exposure data from CSV"""
        reader = csv.DictReader(io.StringIO(csv_content))
        records_inserted = 0

        for row in reader:
            exposure_data = {
                'train_id': row.get('train_id'),
                'log_date': datetime.fromisoformat(row.get('log_date')).date(),
                'exposure_hours': float(row.get('exposure_hours', 0))
            }

            if exposure_data['train_id'] and exposure_data['log_date']:
                new_exposure = BrandingExposureLog(**exposure_data)
                self.db.add(new_exposure)
                records_inserted += 1

        await self.db.commit()
        return {
            'message': 'Branding exposure data ingested successfully',
            'records_inserted': records_inserted
        }

    async def get_sample_csv_templates(self) -> Dict[str, str]:
        """Get sample CSV templates for data ingestion"""
        return {
            'trains': """train_id,car_count,brand_code,wrap_id,status,current_bay,notes
TS-01,4,BRAND001,WRAP001,active,B-01,
TS-02,4,BRAND002,WRAP002,standby,B-02,
TS-03,4,BRAND003,WRAP003,ibl,B-03,""",

            'fitness_certificates': """train_id,dept,valid_from,valid_to,status,source_ref
TS-01,MECH,2024-01-01T00:00:00,2024-12-31T23:59:59,valid,CERT001
TS-01,ELEC,2024-01-01T00:00:00,2024-12-31T23:59:59,valid,CERT002
TS-02,MECH,2024-01-01T00:00:00,2024-12-31T23:59:59,valid,CERT003""",

            'job_cards': """job_id,train_id,source,status,priority,due_date,ibl_required,title,details
JOB001,TS-01,manual,open,3,2024-09-30,true,Brake inspection,Replace brake pads
JOB002,TS-02,manual,open,2,2024-10-05,false,General maintenance,Oil change""",

            'mileage': """train_id,log_date,km_run
TS-01,2024-09-24,45.2
TS-02,2024-09-24,38.7
TS-03,2024-09-24,42.1""",

            'branding_exposure': """train_id,log_date,exposure_hours
TS-01,2024-09-24,8.5
TS-02,2024-09-24,7.2
TS-03,2024-09-24,8.0"""
        }

    async def validate_csv_format(self, csv_content: str, expected_columns: List[str]) -> Dict[str, Any]:
        """Validate CSV format against expected columns"""
        reader = csv.DictReader(io.StringIO(csv_content))

        if not reader.fieldnames:
            return {
                'valid': False,
                'error': 'CSV file has no headers'
            }

        missing_columns = [col for col in expected_columns if col not in reader.fieldnames]
        if missing_columns:
            return {
                'valid': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}',
                'expected_columns': expected_columns,
                'actual_columns': list(reader.fieldnames)
            }

        # Check for empty rows
        rows = list(reader)
        if not rows:
            return {
                'valid': False,
                'error': 'CSV file is empty'
            }

        # Check first row for data
        first_row = rows[0]
        has_data = any(value.strip() for value in first_row.values())

        return {
            'valid': True,
            'row_count': len(rows),
            'has_data': has_data,
            'columns': list(reader.fieldnames)
        }
