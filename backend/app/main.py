from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app.routes.feedback import router as feedback_router
from app.routes.profile import router as profile_router
from app.routes.verification import router as verification_router
from app.routes.auth import router as auth_router
from app.routes.game import router as game_router
from app.routes.skills import router as skills_router
from app.services.google_fact_check import GoogleFactCheckService
from seed import seed_skills


Base.metadata.create_all(bind=engine)

# Initialize skills on startup
try:
    db = SessionLocal()
    seed_skills(db)
    db.close()
except Exception as e:
    print(f"Warning: Failed to seed skills: {e}")

app = FastAPI(
    title="Fact Check Backend",
    description="Backend para consulta ao Google Fact Check Tools API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy routes
app.include_router(verification_router)
app.include_router(feedback_router)
app.include_router(profile_router)
app.include_router(auth_router)

# New routes (Game + Knowledge Tracing)
app.include_router(game_router)
app.include_router(skills_router)


@app.get("/")
def root():
    return {
        "message": "Fact Check Backend",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/api/fact-check")
def fact_check(
    query: str = Query(
        ...,
        min_length=3,
        description="Afirmação ou assunto que será pesquisado"
    ),
    language_code: str = Query(
        "pt-BR",
        description="Idioma da pesquisa"
    ),
    max_age_days: int | None = Query(
        None,
        description="Idade máxima dos resultados"
    ),
    page_size: int = Query(
        10,
        ge=1,
        le=100,
        description="Quantidade de resultados"
    ),
):
    try:
        result = GoogleFactCheckService.search_claims(
            query=query,
            language_code=language_code,
            max_age_days=max_age_days,
            page_size=page_size,
        )

        return result

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {error}"
        )