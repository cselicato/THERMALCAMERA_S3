"""Init constructor for package
"""

from pathlib import Path

__pkgname__ = 'THERMALCAMERA_S3'

THERMALCAMERA_S3_ROOT = Path(__file__).parent
THERMALCAMERA_S3_BASE = THERMALCAMERA_S3_ROOT.parent

THERMALCAMERA_S3_DATA = Path().home() / 'thermalcam_videos'
if not Path.exists(THERMALCAMERA_S3_DATA):
    Path.mkdir(THERMALCAMERA_S3_DATA)