import os
import tempfile
from datetime import datetime
import streamlit as st
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ======== TRANSCRIÇÃO GRATUITA (LOCAL) ========
try:
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
except Exception as e:
    model = None
    whisper_error = e

def transcrever_audio_local(audio_bytes, filename_hint="audio.wav"):
    if model is None:
        raise RuntimeError(f"Whisper não inicializado: {whisper_error}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        tf.write(audio_bytes)
        temp_path = tf.name
    segments, _ = model.transcribe(temp_path, language="pt", vad_filter=True)
    return " ".join([seg.text for seg in segments]).strip()

# ======== ORGANIZAÇÃO OPCIONAL ========
def organizar_texto_local(texto):
    try:
        from transformers import pipeline
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        resumo = summarizer(texto, max_length=220, min_length=60, do_sample=False)[0]["summary_text"]
        return f"- {resumo}", "- [Definir responsáveis, ações e prazos]"
    except:
        return texto, ""

# ======== GERAÇÃO DE ARQUIVOS ========
def gerar_docx(data, hora, local, participantes, assinatura, pautas, encaminhamentos):
    doc = Document()
    doc.add_heading(f'ATA DE COMITÊ EXECUTIVO ({data})', level=1)
    doc.add_paragraph(f"No dia {data}, às {hora}, foi realizada reunião no {local}, para alinhamentos acerca de assuntos gerenciais.")
    doc.add_heading("Presentes:", level=2)
    for p in participantes: doc.add_paragraph(f"- {p}")
    doc.add_heading("Pautas e Deliberações:", level=2)
    doc.add_paragraph(pautas or "[Sem pautas]")
    doc.add_heading("Encaminhamentos:", level=2)
    doc.add_paragraph(encaminhamentos or "[Sem encaminhamentos]")
    doc.add_paragraph(f"\n{assinatura}\nLíder do Projeto CEPAM\nJMLIMA Assessoria Empresarial")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)
    return tmp.name

def gerar_pdf(data, hora, local, participantes, assinatura, pautas, encaminhamentos):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(tmp.name, pagesize=A4)
    story = [
        Paragraph(f"ATA DE COMITÊ EXECUTIVO ({data})", styles["Heading1"]),
        Paragraph(f"No dia {data}, às {hora}, foi realizada reunião no {local}, para alinhamentos acerca de assuntos gerenciais.", styles["Normal"]),
        Paragraph("Presentes:", styles["Heading2"])
    ]
    for p in participantes: story.append(Paragraph(f"- {p}", styles["Normal"]))
    story += [
        Paragraph("Pautas e Deliberações:", styles["Heading2"]),
        Paragraph(pautas or "[Sem pautas]", styles["Normal"]),
        Paragraph("Encaminhamentos:", styles["Heading2"]),
        Paragraph(encaminhamentos or "[Sem encaminhamentos]", styles["Normal"]),
        Paragraph(f"{assinatura}<br/>Líder do Projeto CEPAM<br/>JMLIMA Assessoria Empresarial", styles["Normal"])
    ]
    doc.build(story)
    return tmp.name

# ================== UI ==================
st.set_page_config(page_title="Agente de Atas (GRÁTIS)", page_icon="📝", layout="centered")
st.title("📝 Agente de Atas Executivas — Modo GRÁTIS (sem API)")

if "transcricao" not in st.session_state: st.session_state.transcricao = ""
if "pautas" not in st.session_state: st.session_state.pautas = ""
if "encaminhamentos" not in st.session_state: st.session_state.encaminhamentos = ""

st.subheader("1) Upload de áudio (WAV recomendado)")
up = st.file_uploader("Enviar arquivo de áudio", type=["wav","mp3","m4a","webm"])
if up is not None:
    with st.spinner("Transcrevendo..."):
        try:
            texto = transcrever_audio_local(up.getvalue(), filename_hint=up.name)
            st.session_state.transcricao += "\n" + texto
            st.success("Transcrição adicionada ✅")
        except Exception as e:
            st.error(f"Erro na transcrição: {e}")

st.subheader("2) Organização do conteúdo")
if st.button("🧩 Organizar"):
    p, e = organizar_texto_local(st.session_state.transcricao.strip())
    st.session_state.pautas, st.session_state.encaminhamentos = p, e
col1, col2 = st.columns(2)
col1.text_area("Pautas", key="pautas")
col2.text_area("Encaminhamentos", key="encaminhamentos")

st.subheader("3) Dados obrigatórios")
data = st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"))
hora = st.text_input("Hora", value=datetime.now().strftime("%H:%M"))
local = st.text_input("Local")
participantes_raw = st.text_area("Participantes (um por linha)")
assinatura = st.text_input("Assinatura", value="Verônica Gois")

st.subheader("4) Gerar ata")
if st.button("📦 Gerar arquivos"):
    participantes = [p for p in participantes_raw.splitlines() if p.strip()]
    docx_file = gerar_docx(data, hora, local, participantes, assinatura, st.session_state.pautas, st.session_state.encaminhamentos)
    pdf_file  = gerar_pdf(data, hora, local, participantes, assinatura, st.session_state.pautas, st.session_state.encaminhamentos)
    with open(docx_file,"rb") as f: st.download_button("⬇️ Baixar Word", f, "ATA.docx")
    with open(pdf_file,"rb") as f: st.download_button("⬇️ Baixar PDF", f, "ATA.pdf")

st.subheader("5) Transcrição bruta")
st.write(st.session_state.transcricao or "_sem conteúdo_")
