"""
Export endpoints for generating PDF and CSV reports.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
import io

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.export_service import ExportService
from app.services.statistics_service import StatisticsService
from app.schemas.statistics import StatisticsFilters
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_export_service() -> ExportService:
    """Get the export service instance."""
    statistics_service = StatisticsService()
    return ExportService(statistics_service)


@router.get("/statistics/csv")
async def export_statistics_csv(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    game_type: Optional[str] = Query(None, description="Game type filter"),
    stakes: Optional[str] = Query(None, description="Stakes filter"),
    position: Optional[str] = Query(None, description="Position filter"),
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export user statistics to CSV format.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        game_type: Optional game type filter
        stakes: Optional stakes filter
        position: Optional position filter
        
    Returns:
        CSV file download
    """
    try:
        # Create filters
        filters = None
        if any([start_date, end_date, game_type, stakes, position]):
            filters = StatisticsFilters(
                start_date=start_date,
                end_date=end_date,
                game_type=game_type,
                stakes=stakes,
                position=position
            )
        
        # Generate CSV
        csv_data = await export_service.export_statistics_csv(str(current_user.id), filters)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"poker_statistics_{timestamp}.csv"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to export statistics CSV", 
                    user_id=str(current_user.id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export statistics")


@router.get("/statistics/pdf")
async def export_statistics_pdf(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    game_type: Optional[str] = Query(None, description="Game type filter"),
    stakes: Optional[str] = Query(None, description="Stakes filter"),
    position: Optional[str] = Query(None, description="Position filter"),
    include_charts: bool = Query(True, description="Include charts in PDF"),
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export user statistics to PDF format.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        game_type: Optional game type filter
        stakes: Optional stakes filter
        position: Optional position filter
        include_charts: Whether to include charts
        
    Returns:
        PDF file download
    """
    try:
        # Create filters
        filters = None
        if any([start_date, end_date, game_type, stakes, position]):
            filters = StatisticsFilters(
                start_date=start_date,
                end_date=end_date,
                game_type=game_type,
                stakes=stakes,
                position=position
            )
        
        # Generate PDF
        pdf_data = await export_service.export_statistics_pdf(
            str(current_user.id), 
            filters, 
            include_charts
        )
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"poker_statistics_{timestamp}.pdf"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to export statistics PDF", 
                    user_id=str(current_user.id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export statistics")


@router.get("/session/{session_id}/pdf")
async def export_session_pdf(
    session_id: str,
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export a detailed session report to PDF.
    
    Args:
        session_id: Session ID to export
        
    Returns:
        PDF file download
    """
    try:
        # Generate session PDF
        pdf_data = await export_service.export_session_report_pdf(
            str(current_user.id), 
            session_id
        )
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_report_{session_id}_{timestamp}.pdf"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to export session PDF", 
                    user_id=str(current_user.id), 
                    session_id=session_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export session report")


@router.get("/hands/csv")
async def export_hands_csv(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    game_type: Optional[str] = Query(None, description="Game type filter"),
    stakes: Optional[str] = Query(None, description="Stakes filter"),
    limit: int = Query(1000, description="Maximum number of hands to export"),
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export hand history data to CSV format.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        game_type: Optional game type filter
        stakes: Optional stakes filter
        limit: Maximum number of hands to export
        
    Returns:
        CSV file download
    """
    try:
        # Create filters
        filters = StatisticsFilters(
            start_date=start_date,
            end_date=end_date,
            game_type=game_type,
            stakes=stakes
        )
        
        # Generate hands CSV
        csv_data = await export_service.export_hands_csv(
            str(current_user.id), 
            filters, 
            limit
        )
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"poker_hands_{timestamp}.csv"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to export hands CSV", 
                    user_id=str(current_user.id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export hands")


@router.get("/comprehensive-report/pdf")
async def export_comprehensive_report_pdf(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    include_hands: bool = Query(False, description="Include detailed hand history"),
    include_charts: bool = Query(True, description="Include charts and graphs"),
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export a comprehensive poker report to PDF format.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        include_hands: Whether to include detailed hand history
        include_charts: Whether to include charts and graphs
        
    Returns:
        PDF file download
    """
    try:
        # Create filters
        filters = None
        if start_date or end_date:
            filters = StatisticsFilters(
                start_date=start_date,
                end_date=end_date
            )
        
        # Generate comprehensive PDF
        pdf_data = await export_service.export_comprehensive_report_pdf(
            str(current_user.id), 
            filters,
            include_hands,
            include_charts
        )
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_poker_report_{timestamp}.pdf"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("Failed to export comprehensive report", 
                    user_id=str(current_user.id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export comprehensive report")


@router.get("/formats")
async def get_supported_export_formats():
    """
    Get information about supported export formats.
    
    Returns:
        Information about available export formats
    """
    return {
        "formats": {
            "csv": {
                "name": "CSV (Comma Separated Values)",
                "description": "Spreadsheet-compatible format for data analysis",
                "mime_type": "text/csv",
                "supports": ["statistics", "hands", "sessions"]
            },
            "pdf": {
                "name": "PDF (Portable Document Format)",
                "description": "Professional report format with charts and formatting",
                "mime_type": "application/pdf",
                "supports": ["statistics", "sessions", "comprehensive_reports"]
            }
        },
        "export_types": {
            "statistics": "Export poker statistics and metrics",
            "hands": "Export detailed hand history data",
            "sessions": "Export session-specific reports",
            "comprehensive": "Export complete poker analysis report"
        },
        "filters": {
            "date_range": "Filter by start and end dates",
            "game_type": "Filter by game type (cash, tournament, etc.)",
            "stakes": "Filter by stakes level",
            "position": "Filter by table position"
        },
        "options": {
            "include_charts": "Include visual charts in PDF reports",
            "include_hands": "Include detailed hand data in reports",
            "limit": "Limit number of records in export"
        }
    }