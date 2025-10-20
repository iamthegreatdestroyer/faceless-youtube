"""Compatibility re-exports for database models.

Historically tests and other modules imported models from
`src.database.models`. The canonical model definitions live in
`src.core.models` in this codebase; re-export common names here to
avoid changing large numbers of imports.
"""
from src.core.models import (
    Base,
    User,
    Video,
    Script,
    Asset,
    VideoAsset,
    Platform,
    Publish,
    Analytics,
    # Expose enums as well
    VideoStatus,
    AssetType,
    LicenseType,
    PlatformName,
    PublishStatus,
)

__all__ = [
    "Base",
    "User",
    "Video",
    "Script",
    "Asset",
    "VideoAsset",
    "Platform",
    "Publish",
    "Analytics",
    "VideoStatus",
    "AssetType",
    "LicenseType",
    "PlatformName",
    "PublishStatus",
]
