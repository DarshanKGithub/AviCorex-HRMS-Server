from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
import stripe

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Subscription, Plan
from app.api.routes.admin import _sync_subscription_features

router = APIRouter()

@router.post('/stripe')
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail='Missing signature header')
        
    try:
        # If no webhook secret is set in config, we can bypass verification for testing,
        # but ideally it should be verified.
        if settings.stripe_webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        else:
            # Fallback for dev/test without webhook secret
            import json
            event = json.loads(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase...
        metadata = session.get('metadata', {})
        subscription_id = metadata.get('subscription_id')
        tenant_id = metadata.get('tenant_id')
        plan_id = metadata.get('plan_id')
        
        if subscription_id and tenant_id and plan_id:
            subscription = db.scalar(select(Subscription).where(Subscription.id == subscription_id))
            if subscription and subscription.status == 'pending_payment':
                subscription.status = 'active'
                plan = db.scalar(select(Plan).where(Plan.id == plan_id))
                if plan:
                    _sync_subscription_features(tenant_id, plan, db)
                db.commit()

    return {'status': 'success'}
