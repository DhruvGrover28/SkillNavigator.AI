"""
Supervisor Agent REST API Routes
Provides endpoints for supervisor agent management and orchestration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from agents.supervisor_agent import SupervisorAgent
from database.db_connection import Database

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

class ConfigUpdateRequest(BaseModel):
    scraping_interval_hours: Optional[int] = None
    scoring_threshold: Optional[float] = None
    max_auto_applications: Optional[int] = None
    auto_apply_enabled: Optional[bool] = None
    follow_up_interval_days: Optional[int] = None

class WorkflowResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    workflow_id: Optional[str] = None
    phases: Optional[Dict] = None
    summary: Optional[Dict] = None
    error: Optional[str] = None

class SystemStatusResponse(BaseModel):
    overall_health: str
    agents_status: Dict
    workflow_running: bool
    auto_mode_enabled: bool
    last_scraping_time: Optional[str] = None
    config: Dict
    statistics: Dict

# Dependency to get supervisor agent
_supervisor_instance = None

async def get_supervisor() -> SupervisorAgent:
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = SupervisorAgent()
        await _supervisor_instance.initialize()
    return _supervisor_instance

@router.post("/workflow/trigger", response_model=WorkflowResponse)
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_user_id),
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Manually trigger the complete job search workflow
    """
    try:
        search_params = {
            'query': request.search_query,
            'location': request.location,
            'job_type': request.job_type,
            'experience_level': request.experience_level,
            'salary_min': request.salary_min,
            'salary_max': request.salary_max,
            'max_jobs': request.max_jobs or 50,
            'user_id': user_id
        }
        
        # Run workflow in background
        def run_workflow():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(supervisor.trigger_job_search(search_params))
            return result
        
        background_tasks.add_task(run_workflow)
        
        return WorkflowResponse(
            success=True,
            message="Workflow started successfully",
            workflow_id=f"workflow_{user_id}_{int(datetime.now().timestamp())}"
        )
        
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Get comprehensive system status and health information
    """
    try:
        status = await supervisor.get_system_status()
        
        return SystemStatusResponse(
            overall_health=status['overall_health'],
            agents_status=status['agents'],
            workflow_running=status['workflow_running'],
            auto_mode_enabled=status['auto_mode_enabled'],
            last_scraping_time=status.get('last_scraping_time'),
            config=status['config'],
            statistics=status.get('statistics', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-mode/start")
async def start_auto_mode(
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Start automated job search mode
    """
    try:
        result = await supervisor.start_auto_mode()
        return result
        
    except Exception as e:
        logger.error(f"Error starting auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-mode/stop")
async def stop_auto_mode(
    user = Depends(get_current_user_from_token),
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Stop automated job search mode
    """
    try:
        result = await supervisor.stop_auto_mode()
        return result
        
    except Exception as e:
        logger.error(f"Error stopping auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config", response_model=Dict)
async def update_configuration(
    request: ConfigUpdateRequest,
    user = Depends(get_current_user_from_token),
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Update supervisor agent configuration
    """
    try:
        config_updates = request.dict(exclude_unset=True)
        result = await supervisor.update_configuration(config_updates)
        return result
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_configuration(
    user = Depends(get_current_user_from_token),
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Get current supervisor agent configuration
    """
    try:
        return supervisor.config
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/history")
async def get_workflow_history(
    days: int = 30,
    user = Depends(get_current_user_from_token)
):
    """
    Get workflow execution history for the user
    """
    try:
        database = Database()
        
        # Get workflow history from system activity logs
        query = """
        SELECT timestamp, action, message, metadata, level
        FROM system_activity_log 
        WHERE agent_name = 'supervisor_agent' 
        AND timestamp >= datetime('now', '-{} days')
        ORDER BY timestamp DESC
        """.format(days)
        
        history = database.fetch_all(query)
        
        return {
            'success': True,
            'history': [
                {
                    'timestamp': record['timestamp'],
                    'action': record['action'],
                    'message': record['message'],
                    'metadata': record['metadata'],
                    'level': record.get('level', 'info')
                }
                for record in history
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/health")
async def get_agents_health(
    user = Depends(get_current_user_from_token),
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Get health status of all sub-agents
    """
    try:
        health_status = {}
        
        # Check scraper agent
        try:
            if hasattr(supervisor.scraper_agent, 'health_check'):
                health_status['scraper'] = await supervisor.scraper_agent.health_check()
            else:
                health_status['scraper'] = {'status': 'healthy', 'message': 'Agent available'}
        except Exception as e:
            health_status['scraper'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Check scoring agent
        try:
            if hasattr(supervisor.scoring_agent, 'health_check'):
                health_status['scoring'] = await supervisor.scoring_agent.health_check()
            else:
                health_status['scoring'] = {'status': 'healthy', 'message': 'Agent available'}
        except Exception as e:
            health_status['scoring'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Check auto-apply agent
        try:
            if hasattr(supervisor.autoapply_agent, 'health_check'):
                health_status['autoapply'] = await supervisor.autoapply_agent.health_check()
            else:
                health_status['autoapply'] = {'status': 'healthy', 'message': 'Agent available'}
        except Exception as e:
            health_status['autoapply'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Check tracker agent
        try:
            if hasattr(supervisor.tracker_agent, 'health_check'):
                health_status['tracker'] = await supervisor.tracker_agent.health_check()
            else:
                health_status['tracker'] = {'status': 'healthy', 'message': 'Agent available'}
        except Exception as e:
            health_status['tracker'] = {'status': 'unhealthy', 'error': str(e)}
        
        return {
            'success': True,
            'agents': health_status,
            'overall_health': 'healthy' if all(
                agent.get('status') == 'healthy' 
                for agent in health_status.values()
            ) else 'degraded'
        }
        
    except Exception as e:
        logger.error(f"Error getting agents health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/emergency-stop")
async def emergency_stop(
    user = Depends(get_current_user_from_token),
    supervisor: SupervisorAgent = Depends(get_supervisor)
):
    """
    Emergency stop for all supervisor operations
    """
    try:
        # Stop auto mode
        await supervisor.stop_auto_mode()
        
        # Set workflow_running to False
        supervisor.workflow_running = False
        
        # Log emergency stop
        await supervisor.database.log_system_activity(
            agent_name="supervisor_agent",
            action="emergency_stop",
            message="Emergency stop initiated by user",
            level="warning"
        )
        
        return {
            'success': True,
            'message': 'Emergency stop executed successfully',
            'status': 'stopped'
        }
        
    except Exception as e:
        logger.error(f"Error in emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))