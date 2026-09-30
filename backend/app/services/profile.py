import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.perfil import RespostasInvalidas, carregar_modelo, classificar, vetor_de_respostas
from app.models import Feedback, Profile


logger = logging.getLogger(__name__)


def latest_feedback(database: Session, verification_id: str) -> Feedback | None:
    return database.scalars(
        select(Feedback)
        .where(Feedback.verification_id == verification_id)
        .order_by(Feedback.created_at.desc())
        .limit(1)
    ).first()


def assign_profile(database: Session, verification_id: str) -> Profile:
    """
    Calcula o perfil a partir do questionário mais recente da verificação
    e grava (ou atualiza) a entidade Profile.

    Levanta RespostasInvalidas se não houver questionário ou se ele
    estiver incompleto: registros incompletos são ignorados.
    """

    feedback = latest_feedback(database, verification_id)
    if feedback is None:
        raise RespostasInvalidas("nenhum questionário salvo para esta verificação")

    modelo = carregar_modelo()
    resultado = classificar(modelo, vetor_de_respostas(feedback.answers, modelo["entradas"]))

    profile = database.scalars(select(Profile).where(Profile.verification_id == verification_id)).first()
    if profile is None:
        profile = Profile(verification_id=verification_id)
        database.add(profile)

    profile.assigned_cluster = resultado["assigned_cluster"]
    profile.cluster_label = resultado["cluster_label"]
    profile.probabilities = resultado["probabilities"]
    profile.details = resultado["details"]
    profile.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    database.commit()
    database.refresh(profile)
    return profile


def assign_profile_after_feedback(database: Session, verification_id: str) -> Profile | None:
    """
    Hook síncrono chamado depois de salvar o questionário. Nunca derruba
    o salvamento: questionário incompleto é ignorado e erro do modelo
    só é registrado no log.
    """

    try:
        return assign_profile(database, verification_id)
    except RespostasInvalidas as error:
        logger.info("Perfil não calculado para %s: %s", verification_id, error)
    except Exception:
        database.rollback()
        logger.exception("Falha ao calcular o perfil de %s", verification_id)
    return None


def profile_response(profile: Profile) -> dict:
    return {
        "verification_id": profile.verification_id,
        "profile_result": profile,
    }
