"""Init constructor for package
"""

from pathlib import Path

__pkgname__ = 'THERMALCAMERA_S3'

THERMALCAMERA_S3_ROOT = Path(__file__).parent
THERMALCAMERA_S3_BASE = THERMALCAMERA_S3_ROOT.parent

THERMALCAMERA_S3_DIS_VIDEO = Path().home() / 'thermalcam_videos/display'
if not Path.exists(THERMALCAMERA_S3_DIS_VIDEO):
    Path.mkdir(THERMALCAMERA_S3_DIS_VIDEO)

THERMALCAMERA_S3_PIX_VIDEO = Path().home() / 'thermalcam_videos/pixels'
if not Path.exists(THERMALCAMERA_S3_PIX_VIDEO):
    Path.mkdir(THERMALCAMERA_S3_PIX_VIDEO)

THERMALCAMERA_S3_AREA_VIDEO = Path().home() / 'thermalcam_videos/area'
if not Path.exists(THERMALCAMERA_S3_AREA_VIDEO):
    Path.mkdir(THERMALCAMERA_S3_AREA_VIDEO)