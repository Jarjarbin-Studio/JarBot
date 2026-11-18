
import json
import urllib.error
import urllib.request

import jardiscordengine as JDE

from jarbot_modulable.services.generic_helpers import log_error, log_info, log_warning


def request_pterodactyl_stop() -> None:
    panel_url = JDE.Systems.JDEEnv("PTERODACTYL_PANEL_URL")
    api_key = JDE.Systems.JDEEnv("PTERODACTYL_API_KEY")
    server_id = JDE.Systems.JDEEnv("PTERODACTYL_SERVER_ID")

    if not all((panel_url, api_key, server_id)):
        log_error("Pterodactyl", "Missing API configuration.")
        return

    panel_url = panel_url.rstrip("/")

    # Remove an accidentally included server interface path.
    if panel_url.endswith("/server"):
        panel_url = panel_url[:-7]

    url = (
        f"{panel_url}/api/client/servers/"
        f"{server_id}/power"
    )

    log_info("Pterodactyl", "Requesting server shutdown...")

    request = urllib.request.Request(
        url,
        data=json.dumps({"signal": "stop"}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.pterodactyl.v1+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            log_info("Pterodactyl", f"Shutdown request accepted (HTTP {response.status}).")

    except urllib.error.HTTPError as error:
        log_warning("Pterodactyl", f"Shutdown request rejected: HTTP {error.code} - {error.reason}")

    except urllib.error.URLError as error:
        log_warning("Pterodactyl", f"Unable to reach the panel: {error.reason}")

    except TimeoutError:
        log_warning("Pterodactyl", "Shutdown request timed out.")
