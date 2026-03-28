import json
import logging
from pywebpush import webpush, WebPushException
from ....domain.ports.outbound.services import IPushSender

logger = logging.getLogger(__name__)


class WebPushSender(IPushSender):
    def __init__(self, vapid_private_key: str, vapid_claims: dict):
        self._private_key = vapid_private_key
        self._claims = vapid_claims

    async def send(self, endpoint: str, p256dh: str, auth: str, title: str, body: str, url: str) -> None:
        try:
            webpush(
                subscription_info={"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}},
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=self._private_key,
                vapid_claims=self._claims,
            )
        except WebPushException as e:
            logger.warning("Push fehlgeschlagen für %s: %s", endpoint[:40], e)
