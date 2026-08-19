from fastapi import APIRouter

from app.database import session_scope
from app.services.pipeline import evaluate_approaches

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


@router.get("")
def get_evaluation():
    with session_scope() as session:
        return evaluate_approaches(session)
