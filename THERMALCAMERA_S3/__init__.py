"""Init constructor for package
"""

from pathlib import Path

__pkgname__ = 'THERMALCAMERA_S3'

THERMALCAMERA_S3_ROOT = Path(__file__).parent
THERMALCAMERA_S3_BASE = THERMALCAMERA_S3_ROOT.parent

THERMALCAMERA_S3_OUT = Path().home() / 'thermalcam'
if not Path.exists(THERMALCAMERA_S3_OUT):
    Path.mkdir(THERMALCAMERA_S3_OUT)

THERMALCAMERA_S3_VIDEO = THERMALCAMERA_S3_OUT / 'videos'
if not Path.exists(THERMALCAMERA_S3_VIDEO):
    Path.mkdir(THERMALCAMERA_S3_VIDEO)

THERMALCAMERA_S3_DATA = THERMALCAMERA_S3_OUT / 'data'
if not Path.exists(THERMALCAMERA_S3_DATA):
    Path.mkdir(THERMALCAMERA_S3_DATA)
