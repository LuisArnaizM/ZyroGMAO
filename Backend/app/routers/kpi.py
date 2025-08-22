from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.auth.dependencies import get_current_user, get_optional_user
from app.schemas.kpi import KpiSummary, KpiTrends, AssetKpi, WorkOrderKpi, FailureKpi
from app.controllers.kpi import get_kpi_summary, get_kpi_trends, get_assets_kpi, get_workorders_kpi, get_failures_kpi


router = APIRouter(tags=["kpi"])


@router.get("/summary", response_model=KpiSummary)
async def kpi_summary(
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_optional_user),
):
    return await get_kpi_summary(db)


@router.get("/trends", response_model=KpiTrends)
async def kpi_trends(
    weeks: int = Query(8, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_optional_user),
):
    return await get_kpi_trends(db, weeks)


@router.get("/assets", response_model=AssetKpi)
async def assets_kpi(
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_optional_user),
):
    return await get_assets_kpi(db)


@router.get("/workorders", response_model=WorkOrderKpi)
async def workorders_kpi(
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_optional_user),
):
    return await get_workorders_kpi(db)


@router.get("/failures", response_model=FailureKpi)
async def failures_kpi(
    db: AsyncSession = Depends(get_db),
    _user = Depends(get_optional_user),
):
    return await get_failures_kpi(db)
