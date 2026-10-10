import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
from fpdf import FPDF
import time
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="Agente de Pesquisa & Relatórios de IA",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Agente Autônomo de Pesquisa e Inteligência Competitiva")
st.markdown(
    "Este agente utiliza a **API da Groq** e **Busca Web em Tempo Real (DuckDuckGo)** "
    "para pesquisar tópicos complexos, sintetizar informações e gerar relatórios técnicos detalhados com citações."
)

# Sidebar para Configurações
st.sidebar.header("⚙️ Configurações do Agente")

# Obter API Key da Groq
api_key_env = os.environ.get("API_KEY_GROQ", "")
api_key_input = st.sidebar.text_input(
    "API_KEY_GROQ",
    value=api_key_env,
    type="password",
    help="Insira sua chave da API da Groq aqui ou configure como variável de ambiente."
)

model_choice = st.sidebar.selectbox(
    "Modelo Groq",
    ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    index=0
)

num_results = st.sidebar.slider(
    "Resultados de Busca por Subtópico",
    min_value=2,
    max_value=6,
    value=3
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Instruções")
st.sidebar.markdown(
    "1. Insira sua **API_KEY_GROQ**.\n"
    "2. Digite um tópico complexo.\n"
    "3. Clique em **Executar Pesquisa e Gerar Relatório**."
)

# Área Principal
topic = st.text_input(
    "🔍 Tópico de Pesquisa",
    placeholder="Ex: Tendências de Inteligência Artificial na Medicina em 2026",
    help="Digite o tema central que o agente deve investigar."
)

if "report_content" not in st.session_state:
    st.session_state.report_content = None
if "references" not in st.session_state:
    st.session_state.references = []

def search_web(query, max_results=3):
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "href": r.get("href"),
                    "body": r.get("body")
                })
    except Exception as e:
        st.warning(f"Erro na busca web para '{query}': {e}")
    return results

def generate_pdf_report(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Título
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, title.encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")
    pdf.ln(10)
    
    # Conteúdo
    pdf.set_font("helvetica", "", 11)
    for line in content.split('\n'):
        clean_line = line.replace('#', '').strip()
        if clean_line:
            try:
                pdf.multi_cell(0, 8, clean_line.encode('latin-1', 'replace').decode('latin-1'))
            except Exception:
                pass
        else:
            pdf.ln(4)
    return pdf.output()

if st.button("🚀 Executar Pesquisa e Gerar Relatório", type="primary"):
    if not api_key_input:
        st.error("⚠️ Por favor, informe a **API_KEY_GROQ** na barra lateral ou via variável de ambiente.")
    elif not topic:
        st.error("⚠️ Por favor, digite um tópico de pesquisa válido.")
    else:
        try:
            client = Groq(api_key=api_key_input)
            
            with st.status("🤖 Agente em execução...", expanded=True) as status:
                
                # Passo 1: Decomposição do Tópico
                status.update(label="Passo 1/4: Decompondo o tópico em sub-questões de pesquisa...", state="running")
                decomposition_prompt = f"""
                Você é um Arquiteto de Pesquisa Sênior. Dado o tópico: "{topic}", 
                gere exatamente 3 perguntas ou sub-tópicos de pesquisa essenciais e complementares 
                para investigar aprofundadamente este tema na web.
                Responda APENAS com as 3 perguntas separadas por quebra de linha, sem numeração ou texto adicional.
                """
                
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "user", "content": decomposition_prompt}],
                    temperature=0.3
                )
                
                sub_queries = [q.strip() for q in response.choices[0].message.content.strip().split('\n') if q.strip()]
                st.write(f"🔎 Sub-questões geradas: {sub_queries}")
                time.sleep(1)
                
                # Passo 2: Busca Web
                status.update(label="Passo 2/4: Realizando buscas em tempo real na web...", state="running")
                all_sources = []
                context_corpus = ""
                
                for i, sq in enumerate(sub_queries):
                    st.write(f"Buscando: {sq}")
                    sources = search_web(sq, max_results=num_results)
                    for s in sources:
                        all_sources.append(s)
                        context_corpus += f"\n[Fonte {len(all_sources)}] Título: {s['title']}\nURL: {s['href']}\nConteúdo: {s['body']}\n"
                
                st.session_state.references = all_sources
                time.sleep(1)
                
                # Passo 3: Síntese e Geração do Relatório
                status.update(label="Passo 3/4: Sintetizando dados e estruturando o relatório técnico...", state="running")
                
                synthesis_prompt = f"""
                Você é um Especialista Sênior em Engenharia de IA e Análise de Mercado. 
                Com base nas informações coletadas da web abaixo sobre o tópico "{topic}", elabore um relatório técnico detalhado, profissional e profundo.
                
                O relatório DEVE seguir estritamente a seguinte estrutura em Markdown:
                1. # Resumo Executivo
                2. # Cenário Atual e Contexto
                3. # Principais Desafios e Gargalos
                4. # Inovações Tecnológicas e Tendências Futuras
                5. # Conclusão e Recomendações Estratégicas
                6. # Referências e Fontes (liste explicitamente as fontes utilizadas com base no corpus).
                
                Utilize citações inline no formato [Fonte X] ao longo do texto quando fizer afirmações baseadas nas fontes fornecidas.
                
                CORPUS DE DADOS COLETADOS:
                {context_corpus}
                """
                
                report_response = client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    temperature=0.4
                )
                
                st.session_state.report_content = report_response.choices[0].message.content
                
                status.update(label="✅ Relatório gerado com sucesso!", state="complete", expanded=False)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro durante a execução do agente: {e}")

# Exibição do Relatório
if st.session_state.report_content:
    st.markdown("---")
    st.header("📄 Relatório Técnico Gerado")
    
    st.markdown(st.session_state.report_content)
    
    st.markdown("---")
    st.subheader("📥 Opções de Exportação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Baixar Relatório em Markdown (.md)",
            data=st.session_state.report_content,
            file_name=f"relatorio_{topic.lower().replace(' ', '_')}.md",
            mime="text/markdown"
        )
        
    with col2:
        pdf_bytes = generate_pdf_report(f"Relatório: {topic}", st.session_state.report_content)
        st.download_button(
            label="📥 Baixar Relatório em PDF (.pdf)",
            data=pdf_bytes,
            file_name=f"relatorio_{topic.lower().replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
    if st.session_state.references:
        with st.expander("📚 Fontes e Links Consultados"):
            for idx, ref in enumerate(st.session_state.references, 1):
                st.markdown(f"**[Fonte {idx}] [{ref['title']}]({ref['href']})**\n\n_{ref['body']}_")
