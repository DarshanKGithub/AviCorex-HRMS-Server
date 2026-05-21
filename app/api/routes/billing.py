from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.db.models import Plan, Subscription, Tenant
from datetime import date, timedelta
import os

router = APIRouter()

try:
    import razorpay
except Exception:
    razorpay = None


def _get_razorpay_client():
    if razorpay is None:
        raise RuntimeError('razorpay package not installed')
    key = os.getenv('RAZORPAY_KEY_ID') or getattr(settings, 'razorpay_key_id', None) or None
    secret = os.getenv('RAZORPAY_KEY_SECRET') or getattr(settings, 'razorpay_key_secret', None) or None
    if not key or not secret:
        raise RuntimeError('Razorpay keys not configured')
    return razorpay.Client(auth=(key, secret)), key


@router.post('/create-order')
def create_order(payload: dict, db: Session = Depends(get_db)):
    """Create a Razorpay order and a pending subscription record.

    payload: { tenant_id, plan_id }
    """
    tenant_id = payload.get('tenant_id')
    plan_id = payload.get('plan_id')
    if not tenant_id or not plan_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='tenant_id and plan_id required')

    tenant = db.scalar(Tenant.__table__.select().where(Tenant.id == tenant_id))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tenant not found')

    plan = db.scalar(Plan.__table__.select().where(Plan.id == plan_id))
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Plan not found')

    client, key_id = _get_razorpay_client()
    # Razorpay expects amount in paise (INR), we store price_cents as paise already
    amount = int(plan.price_cents or 0)
    order = client.order.create({'amount': amount, 'currency': 'INR', 'receipt': f'sub_{tenant_id}_{plan_id}', 'payment_capture': 1})

    # Create pending subscription record
    sub = Subscription(
        tenant_id=tenant_id,
        plan_id=plan_id,
        external_order_id=order.get('id'),
        price_paid_cents=amount,
        starts_at=date.today(),
        ends_at=None,
        status='pending',
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    return {
        'order': order,
        'razorpay_key_id': key_id,
        'subscription_id': sub.id,
    }


@router.post('/webhook')
async def webhook(request: Request, db: Session = Depends(get_db)):
    # Validate signature if possible
    payload = await request.body()
    signature = request.headers.get('X-Razorpay-Signature')
    webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET') or getattr(settings, 'razorpay_webhook_secret', None) or None
    if webhook_secret and razorpay is not None:
        try:
            razorpay.Client().utility.verify_webhook_signature(payload, signature, webhook_secret)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid webhook signature')

    event = await request.json()
    event_type = event.get('event')

    # Handle payment.captured
    if event_type == 'payment.captured' or event_type == 'order.paid':
        # order id
        order_id = None
        if event_type == 'payment.captured':
            order_id = event.get('payload', {}).get('payment', {}).get('entity', {}).get('order_id')
        else:
            order_id = event.get('payload', {}).get('order', {}).get('entity', {}).get('id')

        if order_id:
            # Find subscription by external_order_id
            sub = db.scalar(Subscription.__table__.select().where(Subscription.external_order_id == order_id))
            if sub:
                # Activate subscription
                sub.status = 'active'
                # For monthly plans, set ends_at +30 days
                plan = db.scalar(Plan.__table__.select().where(Plan.id == sub.plan_id))
                if plan and (plan.billing_period or 'monthly') == 'monthly':
                    sub.ends_at = date.today() + timedelta(days=30)
                sub.updated_at = sub.updated_at
                db.commit()
    return {'ok': True}
