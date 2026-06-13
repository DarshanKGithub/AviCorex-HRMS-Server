from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
import razorpay
import json

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Subscription, Plan
from app.api.routes.admin import _sync_subscription_features

router = APIRouter()

@router.post('/razorpay')
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('x-razorpay-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail='Missing signature header')
        
    try:
        if settings.razorpay_webhook_secret and settings.razorpay_key_id and settings.razorpay_key_secret:
            client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
            client.utility.verify_webhook_signature(payload.decode('utf-8'), sig_header, settings.razorpay_webhook_secret)
        
        event = json.loads(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the order.paid event
    if event.get('event') == 'order.paid':
        order = event['payload']['order']['entity']
        
        metadata = order.get('notes', {})
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
