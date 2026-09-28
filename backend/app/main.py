from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes.feedback import router as feedback_router
from app.routes.verification import router as verification_router
from app.services.google_fact_check import GoogleFactCheckService


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fact Check Backend",
    description="Backend para consulta ao Google Fact Check Tools API",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(verification_router)
app.include_router(feedback_router)


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
