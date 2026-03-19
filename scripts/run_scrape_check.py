import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "backend"))

from backend.agents.simple_supervisor_agent import SimpleSupervisorAgent
from backend.database.db_connection import database, Job


async def main() -> None:
    await database.initialize()
    supervisor = SimpleSupervisorAgent()
    await supervisor.initialize()

    search_params = {
        "query": "python developer",
        "location": "Remote",
        "job_type": "full-time",
        "max_jobs": 3,
    }

    print("starting scrape with params:", search_params)
    try:
        result = await asyncio.wait_for(
            supervisor.trigger_job_search(search_params),
            timeout=45
        )
    except asyncio.TimeoutError:
        print("scrape timed out after 45s")
        return

    print("search success:", result.get("success"))
    print("jobs found:", result.get("total_found"))
    print("saved to db:", result.get("saved_to_db"))

    session = database.get_session()
    try:
        total_jobs = session.query(Job).count()
        latest = session.query(Job).order_by(Job.id.desc()).first()
        print("db total jobs:", total_jobs)
        if latest:
            print("latest job:", latest.title, "|", latest.company, "|", latest.source)
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
