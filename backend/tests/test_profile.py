import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import joblib
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.perfil import (
    ENTRADAS,
    RespostasInvalidas,
    carregar_modelo,
    classificar,
    corrigir_aquiescencia,
    vetor_de_respostas,
)


client = TestClient(app)

# Cético de baixa circulação coerente (Q4=1, Q8=5), mais a Q9 pós-verificação
RESPOSTAS_CETICO = {"q1": 1, "q2": 1, "q3": 2, "q4": 1, "q5": 2, "q6": 1, "q7": 1, "q8": 5, "q9": 1}


# ------------------------------------------------------------
# Entrada: vetor X
# ------------------------------------------------------------

def test_vetor_de_respostas_na_ordem_q1_a_q8_ignorando_q9():
    assert vetor_de_respostas(RESPOSTAS_CETICO) == [1, 1, 2, 1, 2, 1, 1, 5]


def test_modelo_recebe_8_respostas_e_usa_7_features():
    modelo = carregar_modelo()

    assert len(modelo["entradas"]) == 8
    assert modelo["entradas"] == ENTRADAS
    assert len(modelo["features"]) == 7


def test_modelo_traz_versao_do_sklearn_usada_no_treino():
    assert carregar_modelo()["versao_sklearn"]


def test_modelo_com_entradas_diferentes_nao_carrega(tmp_path):
    modelo = {**carregar_modelo(), "entradas": ENTRADAS[:-1]}
    caminho = tmp_path / "modelo_antigo.joblib"
    joblib.dump(modelo, caminho)

    with pytest.raises(RuntimeError, match="Retreine"):
        carregar_modelo(caminho)


@pytest.mark.parametrize("chave", ["q1", "q4", "q8"])
def test_respostas_incompletas_sao_rejeitadas(chave):
    answers = {k: v for k, v in RESPOSTAS_CETICO.items() if k != chave}

    with pytest.raises(RespostasInvalidas, match=chave):
        vetor_de_respostas(answers)


def test_resposta_nula_conta_como_incompleta():
    with pytest.raises(RespostasInvalidas):
        vetor_de_respostas({**RESPOSTAS_CETICO, "q3": None})


@pytest.mark.parametrize("valor", [0, 6, 2.5, "3", True])
def test_valores_fora_da_escala_sao_rejeitados(valor):
    with pytest.raises(RespostasInvalidas):
        vetor_de_respostas({**RESPOSTAS_CETICO, "q2": valor})


def test_answers_precisa_ser_objeto():
    with pytest.raises(RespostasInvalidas):
        vetor_de_respostas([1, 1, 2, 1, 2, 1, 1, 5])


# ------------------------------------------------------------
# Correção de aquiescência
# ------------------------------------------------------------

def test_q4_e_q8_coerentes_nao_alteram_respostas():
    corrigidas, aquiescencia = corrigir_aquiescencia([[1, 1, 2, 1, 2, 1, 1, 5]])

    assert aquiescencia[0] == 0
    assert corrigidas.iloc[0].tolist() == [1, 1, 2, 1, 2, 1, 1]


def test_concordar_com_tudo_e_descontado():
    # Q4=5 e Q8=5: aquiescência +2, tudo desce 2 pontos (mínimo 1)
    corrigidas, aquiescencia = corrigir_aquiescencia([[5, 5, 5, 5, 5, 5, 5, 5]])

    assert aquiescencia[0] == 2
    assert corrigidas.iloc[0].tolist() == [3, 3, 3, 3, 3, 3, 3]


# ------------------------------------------------------------
# Saída: probabilidades e rótulos
# ------------------------------------------------------------

def test_probabilidades_somam_1_e_cobrem_todos_os_clusters():
    modelo = carregar_modelo()
    resultado = classificar(modelo, vetor_de_respostas(RESPOSTAS_CETICO))

    probabilidades = resultado["probabilities"]

    assert list(probabilidades) == [f"cluster_{i}" for i in range(len(modelo["mapa_clusters"]))]
    assert all(0 <= p <= 1 for p in probabilidades.values())
    assert sum(probabilidades.values()) == pytest.approx(1, abs=1e-3)


def test_cluster_atribuido_e_o_mais_provavel_e_tem_rotulo():
    modelo = carregar_modelo()
    resultado = classificar(modelo, vetor_de_respostas(RESPOSTAS_CETICO))

    mais_provavel = max(resultado["probabilities"], key=resultado["probabilities"].get)

    assert mais_provavel == f"cluster_{resultado['assigned_cluster']}"
    assert resultado["cluster_label"] == modelo["mapa_clusters"][resultado["assigned_cluster"]]


@pytest.mark.parametrize(
    ("respostas", "perfil"),
    [
        ([2, 2, 5, 2, 5, 1, 3, 4], "Verificador crítico"),
        ([5, 5, 1, 5, 1, 3, 3, 1], "Crente resistente"),
        ([5, 5, 4, 3, 5, 2, 3, 3], "Crente flexível"),
        ([3, 3, 1, 5, 4, 5, 4, 1], "Compartilhador impulsivo"),
        ([1, 1, 2, 1, 2, 1, 1, 5], "Cético de baixa circulação"),
        ([4, 4, 3, 2, 4, 3, 5, 4], "Reativo emocional"),
    ],
)
def test_mapeamento_dos_clusters_para_rotulos(respostas, perfil):
    assert classificar(carregar_modelo(), respostas)["cluster_label"] == perfil


def test_resposta_contraditoria_gera_alerta():
    # Q4=5 e Q8=5: concorda com as duas afirmações opostas
    resultado = classificar(carregar_modelo(), [3, 3, 3, 5, 3, 3, 3, 5])

    assert resultado["details"]["acquiescence"] == 2
    assert any("Q4 e Q8" in alerta for alerta in resultado["details"]["alerts"])


# ------------------------------------------------------------
# API: hook após o questionário e endpoints de perfil
# ------------------------------------------------------------

def criar_verificacao():
    return client.post("/api/verifications", json={"text": "Uma afirmação"}).json()["id"]


def test_perfil_e_calculado_ao_salvar_o_questionario():
    verification_id = criar_verificacao()

    salvo = client.post(f"/api/verifications/{verification_id}/feedback", json={"answers": RESPOSTAS_CETICO})
    assert salvo.status_code == 201

    response = client.get(f"/api/verifications/{verification_id}/profile")
    assert response.status_code == 200

    body = response.json()
    assert body["verification_id"] == verification_id
    assert body["profile_result"]["cluster_label"] == "Cético de baixa circulação"
    assert set(body["profile_result"]) >= {"assigned_cluster", "cluster_label", "probabilities", "processed_at"}


def test_questionario_incompleto_e_salvo_mas_nao_gera_perfil():
    verification_id = criar_verificacao()

    salvo = client.post(
        f"/api/verifications/{verification_id}/feedback",
        json={"answers": {"q1": 4, "q2": 5}},
    )
    assert salvo.status_code == 201

    response = client.get(f"/api/verifications/{verification_id}/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"


def test_recalcular_perfil_sem_questionario_valido_retorna_422():
    verification_id = criar_verificacao()

    response = client.post(f"/api/verifications/{verification_id}/profile")
    assert response.status_code == 422


def test_recalcular_perfil_atualiza_o_registro_existente():
    verification_id = criar_verificacao()
    client.post(f"/api/verifications/{verification_id}/feedback", json={"answers": RESPOSTAS_CETICO})

    # Novo questionário, agora de um Compartilhador impulsivo
    novas = {"q1": 3, "q2": 3, "q3": 1, "q4": 5, "q5": 4, "q6": 5, "q7": 4, "q8": 1, "q9": 2}
    client.post(f"/api/verifications/{verification_id}/feedback", json={"answers": novas})

    response = client.post(f"/api/verifications/{verification_id}/profile")
    assert response.status_code == 200
    assert response.json()["profile_result"]["cluster_label"] == "Compartilhador impulsivo"


def test_perfil_de_verificacao_inexistente_retorna_404():
    response = client.get("/api/verifications/00000000-0000-0000-0000-000000000000/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "Verification not found"
