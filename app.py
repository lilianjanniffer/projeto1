import streamlit as st
from google import genai
from google.genai.errors import APIError

# --- Configuração do Layout do Streamlit ---
st.set_page_config(
    page_title="Gerador de Treino & Nutrição com IA",
    page_icon="🏋️‍♂️",
    layout="centered",
)

# --- Configuração do Cliente Gemini ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    client = None


def gerar_cardapio_ia(peso, objetivo, calorias, proteinas, carbos, gorduras):
    if not client:
        st.error("❌ Chave GEMINI_API_KEY não encontrada nos Secrets do Streamlit.")
        return None

    prompt = f"""
    Atue como um nutricionista esportivo profissional.
    Crie um cardápio diário prático (café da manhã, almoço, lanche, jantar) adaptado para:
    - Peso: {peso} kg | Objetivo: {objetivo}
    - Metas Calóricas Diárias: {calorias} kcal
    - Macronutrientes: {proteinas}g de proteína, {carbos}g de carboidrato, {gorduras}g de gordura.
    
    Apresente opções com alimentos acessíveis no Brasil e especifique as quantidades aproximadas (em gramas ou medidas caseiras).
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text
    except APIError as e:
        st.error(f"❌ Erro na API do Gemini (Código {e.code}): {e.message}")
        return None
    except Exception as e:
        st.error(f"❌ Erro inesperado ao gerar o cardápio: {e}")
        return None


# --- Lógica de Cálculos do Plano ---
class PlantoSaude:

    def __init__(
        self,
        peso: float,
        altura_cm: float,
        idade: int,
        sexo: str,
        objetivo: str,
        fator_atividade: float,
    ):
        self.peso = peso
        self.altura_cm = altura_cm
        self.idade = idade
        self.sexo = sexo
        self.objetivo = objetivo
        self.fator_atividade = fator_atividade

    def calcular_tmb(self) -> float:
        if self.sexo == "Masculino":
            return (
                (10 * self.peso)
                + (6.25 * self.altura_cm)
                - (5 * self.idade)
                + 5
            )
        else:
            return (
                (10 * self.peso)
                + (6.25 * self.altura_cm)
                - (5 * self.idade)
                - 161
            )

    def calcular_calorias_e_macros(self) -> dict:
        tmb = self.calcular_tmb()
        get = tmb * self.fator_atividade

        if self.objetivo in ["Emagrecimento", "Definição"]:
            calorias_alvo = get - 400
            proteina_g = self.peso * 2.0
            gordura_g = self.peso * 0.8
        elif self.objetivo in ["Hipertrofia", "Ganho de Massa"]:
            calorias_alvo = get + 400
            proteina_g = self.peso * 1.8
            gordura_g = self.peso * 1.0
        else:
            calorias_alvo = get
            proteina_g = self.peso * 1.6
            gordura_g = self.peso * 0.9

        calorias_p_e_g = (proteina_g * 4) + (gordura_g * 9)
        carboidrato_g = max(0, (calorias_alvo - calorias_p_e_g) / 4)

        return {
            "tmb": round(tmb, 2),
            "get": round(get, 2),
            "calorias_alvo": round(calorias_alvo, 2),
            "proteinas_g": round(proteina_g, 1),
            "carboidratos_g": round(carboidrato_g, 1),
            "gorduras_g": round(gordura_g, 1),
        }

    def gerar_plano_treino(self) -> dict:
        if self.objetivo in ["Emagrecimento", "Definição"]:
            return {
                "foco": "Perda de gordura e preservação muscular",
                "estrutura": "ABC (Empurrar / Puxar / Pernas)",
                "frequencia": "4 a 5 dias por semana",
                "cardio": "20-30 min de aeróbico moderado pós-treino",
            }
        else:
            return {
                "foco": "Hipertrofia e ganho de força muscular",
                "estrutura": (
                    "ABCDE ou Push/Pull/Legs com sobrecarga progressiva"
                ),
                "frequencia": "5 dias por semana",
                "cardio": "15 min de caminhada leve para saúde cardiovascular",
            }


# --- Interface Principal ---
st.title("🏋️‍♂️ Gerador de Plano com IA")
st.write("Insira os dados para calcular as metas e gerar o cardápio com IA.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    peso = st.number_input(
        "Peso (kg):", min_value=30.0, max_value=250.0, value=70.0, step=0.5
    )
    altura = st.number_input(
        "Altura (cm):", min_value=100.0, max_value=230.0, value=170.0, step=1.0
    )
    idade = st.number_input(
        "Idade:", min_value=12, max_value=100, value=25, step=1
    )

with col2:
    sexo = st.selectbox("Sexo Biológico:", ["Masculino", "Feminino"])
    objetivo = st.selectbox(
        "Objetivo Principal:",
        ["Hipertrofia", "Emagrecimento", "Definição", "Manutenção"],
    )
    atividade = st.selectbox(
        "Nível de Atividade Física:",
        [
            "Sedentário",
            "Levemente Ativo (1-3 dias/sem)",
            "Moderadamente Ativo (3-5 dias/sem)",
            "Muito Ativo (6-7 dias/sem)",
        ],
    )

fator_map = {
    "Sedentário": 1.2,
    "Levemente Ativo (1-3 dias/sem)": 1.375,
    "Moderadamente Ativo (3-5 dias/sem)": 1.55,
    "Muito Ativo (6-7 dias/sem)": 1.725,
}

st.write("")
if st.button(
    "🚀 Gerar Plano & Cardápio com IA", type="primary", use_container_width=True
):
    plano = PlantoSaude(
        peso=peso,
        altura_cm=altura,
        idade=idade,
        sexo=sexo,
        objetivo=objetivo,
        fator_atividade=fator_map[atividade],
    )

    nutricao = plano.calcular_calorias_e_macros()
    treino = plano.gerar_plano_treino()

    st.success("Cálculos realizados!")

    # Exibição das Métricas
    st.subheader("📊 Recomendações Nutricionais")
    c1, c2, c3 = st.columns(3)
    c1.metric("TMB (Basal)", f"{nutricao['tmb']} kcal")
    c2.metric("Gasto Diário (GET)", f"{nutricao['get']} kcal")
    c3.metric("Meta Calórica", f"{nutricao['calorias_alvo']} kcal")

    st.markdown("#### Macronutrientes Diários:")
    m1, m2, m3 = st.columns(3)
    m1.metric("🥩 Proteínas", f"{nutricao['proteinas_g']} g")
    m2.metric("🍞 Carboidratos", f"{nutricao['carboidratos_g']} g")
    m3.metric("🥑 Gorduras", f"{nutricao['gorduras_g']} g")

    st.divider()

    st.subheader("🏋️‍♂️ Recomendações de Treino")
    st.write(f"**Foco:** {treino['foco']}")
    st.write(f"**Divisão Recomendada:** {treino['estrutura']}")
    st.write(f"**Frequência:** {treino['frequencia']}")
    st.write(f"**Exercício Aeróbico:** {treino['cardio']}")

    st.divider()

    # Chamada da IA
    with st.spinner("🤖 O Gemini está gerando seu cardápio personalizado..."):
        cardapio = gerar_cardapio_ia(
            peso,
            objetivo,
            nutricao["calorias_alvo"],
            nutricao["proteinas_g"],
            nutricao["carboidratos_g"],
            nutricao["gorduras_g"],
        )
        if cardapio:
            st.subheader("🥗 Sugestão de Cardápio (Gerado por IA)")
            st.write(cardapio)
