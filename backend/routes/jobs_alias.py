from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get('/api/jobs')
async def jobs_no_slash(request: Request):
    # Redirect to canonical trailing-slash route
    qs = request.url.query
    path = '/api/jobs/'
    if qs:
        return RedirectResponse(url=f"{path}?{qs}")
    return RedirectResponse(url=path)
