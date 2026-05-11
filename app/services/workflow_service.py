import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json

from app.db.models import WorkflowTemplate, WorkflowInstance, FormTemplate
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# --- Schemas ---
class FormTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schema_json: str

class WorkflowTemplateCreate(BaseModel):
    name: str
    trigger_event: str
    steps_json: str

# --- Service Methods ---

def create_form_template(payload: FormTemplateCreate, db: Session) -> FormTemplate:
    # validate json
    try:
        json.loads(payload.schema_json)
    except Exception:
        raise ValueError("Invalid schema_json")
        
    ft = FormTemplate(**payload.model_dump())
    db.add(ft)
    db.commit()
    db.refresh(ft)
    return ft

def list_form_templates(db: Session) -> List[FormTemplate]:
    return db.query(FormTemplate).filter(FormTemplate.is_active == True).all()

def create_workflow_template(payload: WorkflowTemplateCreate, db: Session) -> WorkflowTemplate:
    # validate json
    try:
        json.loads(payload.steps_json)
    except Exception:
        raise ValueError("Invalid steps_json")
        
    wt = WorkflowTemplate(**payload.model_dump())
    db.add(wt)
    db.commit()
    db.refresh(wt)
    return wt

def list_workflow_templates(db: Session) -> List[WorkflowTemplate]:
    return db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == True).all()

def trigger_workflow(trigger_event: str, target_id: str, db: Session) -> List[WorkflowInstance]:
    """Trigger all active workflows for a given event"""
    templates = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.trigger_event == trigger_event,
        WorkflowTemplate.is_active == True
    ).all()
    
    instances = []
    for tpl in templates:
        instance = WorkflowInstance(
            template_id=tpl.id,
            target_id=target_id,
            current_step=0,
            status="In Progress"
        )
        db.add(instance)
        instances.append(instance)
        
        logger.info(f"Triggered workflow {tpl.name} for target {target_id}")
        
    db.commit()
    return instances

def advance_workflow(instance_id: str, db: Session) -> WorkflowInstance:
    instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first()
    if not instance:
        return None
        
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == instance.template_id).first()
    if not template:
        return instance
        
    steps = json.loads(template.steps_json)
    
    if instance.current_step < len(steps) - 1:
        instance.current_step += 1
        instance.updated_at = datetime.now(timezone.utc)
        logger.info(f"Workflow instance {instance.id} advanced to step {instance.current_step}")
    else:
        instance.status = "Completed"
        instance.updated_at = datetime.now(timezone.utc)
        logger.info(f"Workflow instance {instance.id} completed")
        
    db.commit()
    db.refresh(instance)
    return instance
