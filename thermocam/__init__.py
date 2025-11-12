"""Init constructor for package
"""

from pathlib import Path

__pkgname__ = 'thermocam'

THERMOCAM_ROOT = Path(__file__).parent
THERMOCAM_BASE = THERMOCAM_ROOT.parent

THERMOCAM_OUT = Path().home() / 'thermocam_out'
if not Path.exists(THERMOCAM_OUT):
    Path.mkdir(THERMOCAM_OUT)

THERMOCAM_VIDEO = THERMOCAM_OUT / 'videos'
if not Path.exists(THERMOCAM_VIDEO):
    Path.mkdir(THERMOCAM_VIDEO)

THERMOCAM_DATA = THERMOCAM_OUT / 'data'
if not Path.exists(THERMOCAM_DATA):
    Path.mkdir(THERMOCAM_DATA)
