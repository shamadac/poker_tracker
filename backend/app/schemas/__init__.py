"""
Pydantic schemas for request/response validation.
"""

from .auth import *
from .user import *
from .hand import *
from .analysis import *
from .statistics import *
from .file_processing import *
from .common import *

__all__ = [
    # Auth schemas
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshTokenRequest",
    
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPreferencesUpdate",
    "APIKeyUpdate",
    "UserProfile",
    
    # Hand schemas
    "HandBase",
    "HandCreate",
    "HandUpdate",
    "HandResponse",
    "HandListResponse",
    "HandUploadResponse",
    "HandFilters",
    "DetailedAction",
    "HandResult",
    "TournamentInfo",
    "CashGameInfo",
    "PlayerStack",
    "TimebankInfo",
    
    # Analysis schemas
    "AnalysisBase",
    "AnalysisCreate",
    "AnalysisResponse",
    "HandAnalysisRequest",
    "SessionAnalysisRequest",
    "AnalysisHistoryResponse",
    
    # Statistics schemas
    "StatisticsFilters",
    "BasicStatistics",
    "AdvancedStatistics",
    "PositionalStatistics",
    "TournamentStatistics",
    "StatisticsResponse",
    "StatisticsSummary",
    "TrendData",
    "ExportRequest",
    
    # File processing schemas
    "FileProcessingTaskBase",
    "FileProcessingTaskCreate",
    "FileProcessingTaskUpdate",
    "FileProcessingTaskResponse",
    "ProcessingProgressResponse",
    "ProcessingStatistics",
    "BatchProcessingRequest",
    "SingleFileProcessingRequest",
    "ProcessingTaskCreatedResponse",
    "ProcessingServiceStatus",
    "SupportedFormatsResponse",
    "TaskCancellationResponse",
    "UserTasksResponse",
    
    # Common schemas
    "PaginationParams",
    "ErrorResponse",
    "SuccessResponse",
    "ValidationError",
]