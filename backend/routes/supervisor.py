"""
Supervisor Agent REST API Routes - Simplified Version
Provides basic endpoints for supervisor agent management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from agents.simple_supervisor_agent import SimpleSupervisorAgent
from database.db_connection import Database, get_db, SystemLog
from middleware.auth_middleware import get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

# Pydantic models for request/response
class WorkflowTriggerRequest(BaseModel):
    search_query: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    max_jobs: Optional[int] = 50

class SystemStatusResponse(BaseModel):
    success: bool
    auto_mode_enabled: bool
    last_search_time: Optional[str] = None
    agents_status: Dict
    message: Optional[str] = None

# Global supervisor instance
_supervisor_instance = None

async def get_supervisor() -> SimpleSupervisorAgent:
    global _supervisor_instance
    if _supervisor_instance is None:
        # Prefer the globally-initialized supervisor from main if available
        try:
            import main as main_module
            global_supervisor = getattr(main_module, 'supervisor_agent', None)
            if global_supervisor is not None:
                _supervisor_instance = global_supervisor
                return _supervisor_instance
        except Exception:
            # If import fails or global not set, create a local instance
            pass

        _supervisor_instance = SimpleSupervisorAgent()
        await _supervisor_instance.initialize()
    return _supervisor_instance

@router.post("/workflow/trigger")
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_user_id)
):
    """
    Manually trigger the complete job search workflow
    """
    try:
        supervisor = await get_supervisor()
        
        search_params = {
            'query': request.search_query,
            'keywords': request.search_query,
            'location': request.location or 'Remote',
            'job_type': request.job_type,
            'experience_level': request.experience_level,
            'salary_min': request.salary_min,
            'salary_max': request.salary_max,
            'max_jobs': request.max_jobs or 50,
            'max_results': request.max_jobs or 50,
            'user_id': user_id
        }
        
        # Start workflow in background
        result = await supervisor.trigger_job_search(search_params)
        
        return {
            'success': True,
            'message': 'Workflow started successfully',
            'workflow_id': f"workflow_1_{int(datetime.now().timestamp())}",
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(user_id: int = Depends(get_user_id)):
    """
    Get basic system status information
    """
    try:
        supervisor = await get_supervisor()
        
        # Get basic status
        status = {
            'scraper_agent': 'healthy' if supervisor.scraper_agent else 'unavailable',
            'scoring_agent': 'healthy' if supervisor.scoring_agent else 'unavailable',
            'autoapply_agent': 'healthy' if supervisor.autoapply_agent else 'unavailable'
        }
        
        return SystemStatusResponse(
            success=True,
            auto_mode_enabled=supervisor.is_auto_mode,
            last_search_time=supervisor.last_search_time.isoformat() if supervisor.last_search_time else None,
            agents_status=status,
            message="System status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-mode/start")
async def start_auto_mode(user_id: int = Depends(get_user_id)):
    """
    Start automated job search mode
    """
    try:
        supervisor = await get_supervisor()
        result = await supervisor.start_auto_mode()
        return result
        
    except Exception as e:
        logger.error(f"Error starting auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-mode/stop")
async def stop_auto_mode(user_id: int = Depends(get_user_id)):
    """
    Stop automated job search mode
    """
    try:
        supervisor = await get_supervisor()
        result = await supervisor.stop_auto_mode()
        return result
        
    except Exception as e:
        logger.error(f"Error stopping auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_configuration(user_id: int = Depends(get_user_id)):
    """
    Get current supervisor agent configuration
    """
    try:
        supervisor = await get_supervisor()
        return {
            'success': True,
            'config': {
                'auto_apply_enabled': supervisor.auto_apply_enabled,
                'auto_apply_threshold': supervisor.auto_apply_threshold,
                'max_auto_applies_per_day': supervisor.max_auto_applies_per_day,
                'is_auto_mode': supervisor.is_auto_mode
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/health")
async def get_agents_health(user_id: int = Depends(get_user_id)):
    """
    Get health status of all sub-agents
    """
    try:
        supervisor = await get_supervisor()
        
        health_status = {
            'scraper': {'status': 'healthy' if supervisor.scraper_agent else 'unavailable'},
            'scoring': {'status': 'healthy' if supervisor.scoring_agent else 'unavailable'},
            'autoapply': {'status': 'healthy' if supervisor.autoapply_agent else 'unavailable'}
        }
        
        return {
            'success': True,
            'agents': health_status,
            'overall_health': 'healthy'
        }
        
    except Exception as e:
        logger.error(f"Error getting agents health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/history")
async def get_workflow_history(days: int = 30):
    """
    Get workflow execution history
    """
    try:
        db = Database().get_session()
        try:
            cutoff = datetime.utcnow().timestamp() - (days * 24 * 3600)
            history_rows = (
                db.query(SystemLog)
                .filter(SystemLog.agent_name == 'supervisor_agent')
                .order_by(SystemLog.timestamp.desc())
                .limit(200)
                .all()
            )

            history = []
            for row in history_rows:
                if row.timestamp and row.timestamp.timestamp() < cutoff:
                    continue
                history.append({
                    'action': row.action,
                    'message': row.message,
                    'level': row.level,
                    'timestamp': row.timestamp.isoformat() if row.timestamp else None,
                    'metadata': row.get_metadata()
                })

            return {
                'success': True,
                'history': history,
                'message': 'Workflow history retrieved successfully'
            }
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error getting workflow history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/analyze/{user_id}")
async def analyze_user_outcomes(
    user_id: int = Depends(get_user_id)
):
    """
    Analyze user outcomes and apply adaptive learning
    """
    try:
        supervisor = await get_supervisor()
        result = await supervisor.analyze_user_outcomes(user_id)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing user outcomes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/tune-threshold/{user_id}")
async def tune_scoring_threshold(
    user_id: int = Depends(get_user_id)
):
    """
    Dynamically tune scoring threshold for user
    """
    try:
        supervisor = await get_supervisor()
        result = await supervisor.adaptive_threshold_tuning(user_id)
        return result
        
    except Exception as e:
        logger.error(f"Error tuning threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule/setup/{user_id}")
async def setup_user_schedule(
    user_id: int,
    schedule_config: Dict,
    current_user_id: int = Depends(get_user_id)
):
    """
    Setup per-user scheduling configuration
    """
    try:
        supervisor = await get_supervisor()
        result = await supervisor.setup_user_schedule(current_user_id, schedule_config)
        return result
        
    except Exception as e:
        logger.error(f"Error setting up user schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/insights/{user_id}")
async def get_user_insights(
    user_id: int = Depends(get_user_id)
):
    """
    Get personalized insights and recommendations for user
    """
    try:
        supervisor = await get_supervisor()
        
        # Get learning data for user
        learning_data = supervisor.learning_data.get('user_insights', {}).get(user_id, {})
        
        if not learning_data:
            # Trigger analysis first
            analysis_result = await supervisor.analyze_user_outcomes(user_id)
            learning_data = supervisor.learning_data.get('user_insights', {}).get(user_id, {})
        
        insights = learning_data.get('insights', [])
        outcomes = learning_data.get('outcomes', {})
        
        return {
            'success': True,
            'user_id': user_id,
            'insights': insights,
            'outcomes': outcomes,
            'scoring_weights': supervisor.learning_data['scoring_weights'],
            'current_threshold': supervisor.auto_apply_threshold
        }
        
    except Exception as e:
        logger.error(f"Error getting user insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/comprehensive")
async def get_comprehensive_health():
    """
    Get comprehensive system health with detailed metrics
    """
    try:
        supervisor = await get_supervisor()
        health_status = await supervisor._comprehensive_health_check()
        
        return {
            'success': True,
            'health_status': health_status,
            'health_metrics': supervisor.health_metrics,
            'retry_config': {
                'max_retries': supervisor.retry_config['max_retries'],
                'active_failed_tasks': len(supervisor.retry_config['failed_tasks'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting comprehensive health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recovery/retry-task/{task_id}")
async def retry_failed_task(
    task_id: str,
    task_data: Dict
):
    """
    Retry a failed task with exponential backoff
    """
    try:
        supervisor = await get_supervisor()
        result = await supervisor.retry_failed_task(task_id, task_data)
        return result
        
    except Exception as e:
        logger.error(f"Error retrying task: {e}")
        raise HTTPException(status_code=500, detail=str(e))