from fastapi import FastAPI, HTTPException, Query

from app.services.google_fact_check import GoogleFactCheckService


app = FastAPI(
    title="Fact Check Backend",
    description="Backend para consulta ao Google Fact Check Tools API",
    version="1.0.0",
)


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
