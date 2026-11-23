from typing import Final

import jardiscordengine as JDE


BOT_NAME: Final[str] = "JarBotModulable"
MANKIER_WEB_URL: Final[str] = "https://www.mankier.com"

CONFIRMATION_TIMEOUT: Final[int] = 60
LIST_MESSAGE_LIMIT: Final[int] = 20
PAGE_LIMIT: Final[int] = 1800
REQUEST_TIMEOUT: Final[int] = 10
MAX_WORKERS: Final[int] = 4

PGE_ROLE: Final[JDE.Entities.JDEEntityRole] = JDE.Entities.JDEEntityRole(1559861157844623380, "PGE", _jde_warn = False)
BACH_ROLE: Final[JDE.Entities.JDEEntityRole] = JDE.Entities.JDEEntityRole(1559862969981075536, "BACH", _jde_warn = False)

MAN_CHANNEL: Final[JDE.Entities.JDEEntityChannel] = JDE.Entities.JDEEntityChannel(1564567560370790473, "Man", _jde_warn = False)
