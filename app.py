import os
import tempfile
from datetime import datetime
import streamlit as st
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ============== OpenAI (Whisper + opcional organização via GPT) ==============
try:
    from openai import OpenAI
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    _client = None

def transcrever_audio(audio_bytes, filename_hint="audio.wav"):
    if _client is None:
        raise RuntimeError("Biblioteca openai não inicializada. Verifique a instalação e a variável OPENAI_API_KEY.")
    # Salva bytes temporariamente
    suffix = os.path.splitext(filename_hint)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
        tf.write(audio_bytes)
        temp_path = tf.name
    # Transcreve com Whisper
    with open(temp_path, "rb") as f:
        tr = _client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return tr.text

def organizar_transcricao_bruta(transcricao):
    """
    Usa um modelo de linguagem para estruturar o texto em:
    - PAUTAS E DELIBERAÇÕES (bullet points)
    - ENCAMINHAMENTOS (Responsável + prazo + ação)
    """
    if _client is None:
        return transcricao  # fallback simples
    prompt = f"""
    Reescreva o texto abaixo em formato de ata executiva, em português, seguindo este esqueleto:

    PAUTAS E DELIBERAÇÕES:
    - ...
    - ...

    ENCAMINHAMENTOS:
    - Responsável: ... | Ação: ... | Prazo: ...

    Mantenha fiel ao conteúdo, seja claro e objetivo. Texto a organizar:
    \"\"\"
    {transcricao}
    \"\"\"
    """
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um secretário executivo especialista em atas formais."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        # Se falhar, devolve a transcrição bruta
        return transcricao

# ========================= Geração de arquivos ================================
def gerar_docx(data, hora, local, participantes, assinatura, corpo_pautas, corpo_encaminhamentos):
    doc = Document()
    doc.add_heading(f'ATA DE COMITÊ EXECUTIVO ({data})', level=1)

    doc.add_paragraph(
        f"No dia {data}, às {hora}, foi realizada reunião "
        f"{'online' if 'online' in local.lower() else 'presencial'} "
        f"no {local}, para alinhamentos acerca de assuntos gerenciais."
    )

    doc.add_heading("Presentes:", level=2)
    if isinstance(participantes, list):
        for p in participantes:
            if p.strip():
                doc.add_paragraph(f"- {p.strip()}")
    else:
        doc.add_paragraph(participantes)

    doc.add_heading("Pautas e Deliberações:", level=2)
    doc.add_paragraph(corpo_pautas or "[Sem pautas]")

    doc.add_heading("Encaminhamentos:", level=2)
    doc.add_paragraph(corpo_encaminhamentos or "[Sem encaminhamentos]")

    if assinatura:
        doc.add_paragraph("\n")
        doc.add_paragraph(assinatura)
        doc.add_paragraph("Líder do Projeto CEPAM")
        doc.add_paragraph("JMLIMA Assessoria Empresarial")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)
    return tmp.name

def gerar_pdf(data, hora, local, participantes, assinatura, corpo_pautas, corpo_encaminhamentos):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    normal = styles["Normal"]

    doc = SimpleDocTemplate(tmp.name, pagesize=A4, topMargin=36, bottomMargin=36, leftMargin=36, rightMargin=36)
    story = []

    story.append(Paragraph(f"ATA DE COMITÊ EXECUTIVO ({data})", h1))
    story.append(Paragraph(
        f"No dia {data}, às {hora}, foi realizada reunião "
        f"{'online' if 'online' in local.lower() else 'presencial'} "
        f"no {local}, para alinhamentos acerca de assuntos gerenciais.",
        normal
    ))

    story.append(Paragraph("Presentes:", h2))
    if isinstance(participantes, list):
        for p in participantes:
            if p.strip():
                story.append(Paragraph(f"- {p.strip()}", normal))
    else:
        story.append(Paragraph(participantes, normal))

    story.append(Paragraph("Pautas e Deliberações:", h2))
    story.append(Paragraph(corpo_pautas or "[Sem pautas]", normal))

    story.append(Paragraph("Encaminhamentos:", h2))
    story.append(Paragraph(corpo_encaminhamentos or "[Sem encaminhamentos]", normal))

    if assinatura:
        story.append(Paragraph("<br/>", normal))
        story.append(Paragraph(assinatura, normal))
        story.append(Paragraph("Líder do Projeto CEPAM", normal))
        story.append(Paragraph("JMLIMA Assessoria Empresarial", normal))

    doc.build(story)
    return tmp.name

# ============================= UI / STREAMLIT ================================
st.set_page_config(page_title="Agente de Atas Executivas", page_icon="📝", layout="centered")
st.title("📝 Agente de Atas Executivas")
st.caption("Grave, transcreva, valide e gere a ata no modelo padrão (DOCX/PDF).")

# Estado da sessão
if "gravando" not in st.session_state:
    st.session_state.gravando = False
if "transcricao" not in st.session_state:
    st.session_state.transcricao = ""
if "pautas" not in st.session_state:
    st.session_state.pautas = ""
if "encaminhamentos" not in st.session_state:
    st.session_state.encaminhamentos = ""
if "trechos" not in st.session_state:
    st.session_state.trechos = []  # histórico de transcrições parciais

st.sidebar.header("Comandos")
colA, colB = st.sidebar.columns(2)
if colA.button("▶️ Iniciar"):
    st.session_state.gravando = True
if colB.button("⏸️ Pausar"):
    st.session_state.gravando = False

st.sidebar.divider()
if st.sidebar.button("🧹 Limpar sessão"):
    st.session_state.gravando = False
    st.session_state.transcricao = ""
    st.session_state.pautas = ""
    st.session_state.encaminhamentos = ""
    st.session_state.trechos = []
    st.success("Sessão limpa.")

with st.expander("⚙️ Preferências (opcional)", expanded=False):
    usar_gpt_para_organizar = st.checkbox("Organizar transcrição automaticamente (GPT)", value=True,
                                          help="Estrutura PAUTAS e ENCAMINHAMENTOS com GPT. Requer OPENAI_API_KEY.")
    assinatura_padrao = st.text_input("Assinatura padrão (opcional)", value="Verônica Gois")

st.markdown("---")

# Gravação / Upload de áudio
st.subheader("1) Captura de áudio")
st.write("Clique em **Iniciar** na barra lateral e use o controle abaixo para gravar trechos da reunião.")

# `st.audio_input` pede permissão ao microfone e captura um trecho por vez
audio_file = st.audio_input("🎤 Gravar um trecho e soltar para enviar", disabled=not st.session_state.gravando)

if st.session_state.gravando and audio_file is not None:
    with st.spinner("Transcrevendo trecho..."):
        try:
            texto = transcrever_audio(audio_file.getvalue(), filename_hint=audio_file.name or "audio.wav")
            st.session_state.trechos.append(texto.strip())
            st.session_state.transcricao += ("\n" if st.session_state.transcricao else "") + texto.strip()
            st.success("Trecho transcrito e adicionado ✅")
        except Exception as e:
            st.error(f"Falha na transcrição: {e}")

# Upload adicional de arquivo de áudio
st.write("Ou faça upload de um arquivo de áudio externo (mp3, wav, m4a, webm):")
up = st.file_uploader("Enviar arquivo de áudio", type=["mp3", "wav", "m4a", "webm"], accept_multiple_files=False)
if up is not None:
    with st.spinner("Transcrevendo arquivo..."):
        try:
            texto = transcrever_audio(up.getvalue(), filename_hint=up.name)
            st.session_state.trechos.append(texto.strip())
            st.session_state.transcricao += ("\n" if st.session_state.transcricao else "") + texto.strip()
            st.success("Arquivo transcrito e adicionado ✅")
        except Exception as e:
            st.error(f"Falha na transcrição: {e}")

st.markdown("---")

# Organização do conteúdo
st.subheader("2) Organização do conteúdo")
if st.button("🧩 Organizar transcrição (gerar Pautas/Encaminhamentos)") and st.session_state.transcricao.strip():
    with st.spinner("Organizando com GPT..."):
        organizado = organizar_transcricao_bruta(st.session_state.transcricao.strip())
        # Heurística simples para quebrar em seções
        parts = organizado.split("ENCAMINHAMENTOS:")
        if len(parts) == 2:
            st.session_state.pautas = parts[0].replace("PAUTAS E DELIBERAÇÕES:", "").strip()
            st.session_state.encaminhamentos = parts[1].strip()
        else:
            # fallback: tudo vai para pautas
            st.session_state.pautas = organizado
            st.session_state.encaminhamentos = ""

col1, col2 = st.columns(2)
with col1:
    st.text_area("PAUTAS E DELIBERAÇÕES (edite se desejar)", key="pautas", height=200)
with col2:
    st.text_area("ENCAMINHAMENTOS (edite se desejar)", key="encaminhamentos", height=200)

st.markdown("---")

# Dados obrigatórios
st.subheader("3) Dados obrigatórios da ata")
with st.form("dados_obrigatorios"):
    hoje = datetime.now().strftime("%d/%m/%Y")
    data = st.text_input("📅 Data da reunião", value=hoje)
    hora = st.text_input("⏰ Hora de início", value=datetime.now().strftime("%H:%M"))
    local = st.text_input("📍 Local (ex.: 'Sede - Sala X' ou 'Online - Meet')")
    participantes_raw = st.text_area("👥 Participantes (um por linha)", placeholder="Nome 1\nNome 2\nNome 3")
    assinatura = st.text_input("📝 Responsável pela assinatura", value=assinatura_padrao or "")
    submitted = st.form_submit_button("Validar dados")
    if submitted:
        if not data or not hora or not local or not participantes_raw or not assinatura:
            st.error("❌ Todos os campos obrigatórios devem ser preenchidos.")
        else:
            st.success("✅ Dados validados. Você pode gerar a ata.")

st.markdown("---")

# Geração e download
st.subheader("4) Gerar e baixar a ata")
gerar = st.button("📦 Gerar arquivos (DOCX + PDF)")
if gerar:
    if not data or not hora or not local or not participantes_raw or not assinatura:
        st.error("❌ Preencha e valide os dados no passo 3 antes de gerar.")
    else:
        participantes = [p.strip() for p in participantes_raw.splitlines() if p.strip()]
        pautas_texto = st.session_state.pautas.strip() or st.session_state.transcricao.strip()
        encaminhamentos_texto = st.session_state.encaminhamentos.strip()

        with st.spinner("Gerando DOCX e PDF..."):
            path_docx = gerar_docx(data, hora, local, participantes, assinatura, pautas_texto, encaminhamentos_texto)
            path_pdf  = gerar_pdf(data, hora, local, participantes, assinatura, pautas_texto, encaminhamentos_texto)

        with open(path_docx, "rb") as f:
            st.download_button("⬇️ Baixar Word (.docx)", f, file_name=f"ATA_{data.replace('/','-')}.docx")
        with open(path_pdf, "rb") as f:
            st.download_button("⬇️ Baixar PDF (.pdf)", f, file_name=f"ATA_{data.replace('/','-')}.pdf")

st.markdown("---")
with st.expander("🧾 Visualizar transcrição bruta capturada"):
    st.write(st.session_state.transcricao or "_(Sem transcrição até o momento)_")

st.caption("Dica: mantenha a gravação em trechos curtos para melhor precisão.")