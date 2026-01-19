"""
File monitoring endpoints for hand history directory monitoring.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.file_watcher import FileWatcherService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class DirectoryMonitoringRequest(BaseModel):
    """Request model for starting directory monitoring."""
    platform: str
    directory_path: str


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status."""
    platform: str
    directory_path: str
    is_active: bool
    last_scan: str = None
    file_count: int
    is_monitoring: bool


class DefaultPathsResponse(BaseModel):
    """Response model for default paths."""
    platform: str
    paths: List[str]


class DirectoryScanResponse(BaseModel):
    """Response model for directory scan."""
    directory_path: str
    files_found: List[str]
    total_files: int


def get_file_watcher() -> FileWatcherService:
    """Get the file watcher service instance."""
    from app.main import file_watcher_service
    if file_watcher_service is None:
        raise HTTPException(status_code=503, detail="File monitoring service not available")
    return file_watcher_service


@router.get("/default-paths/{platform}", response_model=DefaultPathsResponse)
async def get_default_paths(
    platform: str,
    current_user: User = Depends(get_current_user),
    watcher: FileWatcherService = Depends(get_file_watcher)
):
    """
    Get default hand history paths for a platform.
    
    Args:
        platform: Platform name ('pokerstars' or 'ggpoker')
        
    Returns:
        List of default directory paths for the platform
    """
    try:
        if platform not in ['pokerstars', 'ggpoker']:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        paths = await watcher.get_default_paths(platform)
        
        return DefaultPathsResponse(
            platform=platform,
            paths=paths
        )
        
    except Exception as e:
        logger.error("Failed to get default paths", platform=platform, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get default paths")


@router.post("/start")
async def start_monitoring(
    request: DirectoryMonitoringRequest,
    current_user: User = Depends(get_current_user),
    watcher: FileWatcherService = Depends(get_file_watcher)
):
    """
    Start monitoring a directory for hand history files.
    
    Args:
        request: Directory monitoring configuration
        
    Returns:
        Success message and monitoring status
    """
    try:
        if request.platform not in ['pokerstars', 'ggpoker']:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        success = await watcher.start_monitoring(
            str(current_user.id),
            request.platform,
            request.directory_path
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start monitoring")
        
        return {
            "message": "Monitoring started successfully",
            "platform": request.platform,
            "directory_path": request.directory_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start monitoring", 
                    platform=request.platform, 
                    directory=request.directory_path, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start monitoring")


@router.post("/stop")
async def stop_monitoring(
    request: DirectoryMonitoringRequest,
    current_user: User = Depends(get_current_user),
    watcher: FileWatcherService = Depends(get_file_watcher)
):
    """
    Stop monitoring a directory.
    
    Args:
        request: Directory monitoring configuration
        
    Returns:
        Success message
    """
    try:
        if request.platform not in ['pokerstars', 'ggpoker']:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        success = await watcher.stop_monitoring(
            str(current_user.id),
            request.platform,
            request.directory_path
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop monitoring")
        
        return {
            "message": "Monitoring stopped successfully",
            "platform": request.platform,
            "directory_path": request.directory_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop monitoring", 
                    platform=request.platform, 
                    directory=request.directory_path, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")


@router.get("/status", response_model=List[MonitoringStatusResponse])
async def get_monitoring_status(
    current_user: User = Depends(get_current_user),
    watcher: FileWatcherService = Depends(get_file_watcher)
):
    """
    Get monitoring status for the current user.
    
    Returns:
        List of monitoring configurations and their status
    """
    try:
        status_list = await watcher.get_monitoring_status(str(current_user.id))
        
        return [
            MonitoringStatusResponse(
                platform=status['platform'],
                directory_path=status['directory_path'],
                is_active=status['is_active'],
                last_scan=status['last_scan'].isoformat() if status['last_scan'] else None,
                file_count=status['file_count'],
                is_monitoring=status['is_monitoring']
            )
            for status in status_list
        ]
        
    except Exception as e:
        logger.error("Failed to get monitoring status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")


@router.post("/scan-directory", response_model=DirectoryScanResponse)
async def scan_directory(
    directory_path: str,
    recursive: bool = True,
    current_user: User = Depends(get_current_user),
    watcher: FileWatcherService = Depends(get_file_watcher)
):
    """
    Scan a directory for hand history files.
    
    Args:
        directory_path: Directory to scan
        recursive: Whether to scan subdirectories
        
    Returns:
        List of found hand history files
    """
    try:
        files = await watcher.scan_directory_for_files(directory_path, recursive)
        
        return DirectoryScanResponse(
            directory_path=directory_path,
            files_found=files,
            total_files=len(files)
        )
        
    except Exception as e:
        logger.error("Failed to scan directory", directory=directory_path, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to scan directory")


@router.get("/platforms")
async def get_supported_platforms():
    """
    Get list of supported poker platforms.
    
    Returns:
        List of supported platform names
    """
    return {
        "platforms": ["pokerstars", "ggpoker"],
        "descriptions": {
            "pokerstars": "PokerStars hand history monitoring",
            "ggpoker": "GGPoker hand history monitoring"
        }
    }