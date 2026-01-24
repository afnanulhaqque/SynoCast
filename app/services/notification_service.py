import json
import os
import logging
from pywebpush import webpush, WebPushException
from app.models.user import PushSubscription
from app.extensions import db

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_push_notification(subscription_info, data):
        """
        Send a push notification to a single subscriber.
        subscription_info: dict or PushSubscription model containing endpoint, keys
        data: dict containing title, body, url, etc.
        """
        
        vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
        vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY")
        
        if not vapid_private_key or not vapid_public_key:
            logger.error("VAPID keys not configured.")
            return False

        # Handle both dict and Model object
        if isinstance(subscription_info, PushSubscription):
            sub_info = {
                "endpoint": subscription_info.endpoint,
                "keys": {
                    "p256dh": subscription_info.p256dh,
                    "auth": subscription_info.auth
                }
            }
        else:
            sub_info = subscription_info

        try:
            webpush(
                subscription_info=sub_info,
                data=json.dumps(data),
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": "mailto:admin@synocast.com"}
            )
            return True
        except WebPushException as ex:
            logger.error(f"WebPush Error: {ex}")
            if ex.response and ex.response.status_code == 410:
                # Subscription expired/gone, remove from DB
                NotificationService._remove_dead_subscription(sub_info['endpoint'])
            return False
        except Exception as e:
            logger.error(f"Notification Error: {e}")
            return False

    @staticmethod
    def _remove_dead_subscription(endpoint):
        try:
            sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
            if sub:
                db.session.delete(sub)
                db.session.commit()
                logger.info(f"Removed dead subscription: {endpoint}")
        except Exception as e:
            logger.error(f"Error removing dead subscription: {e}")

    @staticmethod
    def broadcast_weather_alert(alert_data, min_severity='High'):
        """
        Broadcast alert to all subscribers (naive impl - ideally filter by location)
        """
        subs = PushSubscription.query.all()
        for sub in subs:
            # TODO: Add location filtering here based on sub.lat/lon vs alert_data location
            NotificationService.send_push_notification(sub, {
                "title": f"Weather Alert: {alert_data.get('event')}",
                "body": f"{alert_data.get('headline')}",
                "url": "/weather",
                "icon": "/assets/logo/logo-small.png"
            })
