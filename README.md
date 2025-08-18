# Agente de Atas Executivas (Streamlit)

App para gravar, transcrever (Whisper), organizar e gerar atas no modelo CEPAM/JMLIMA com download em DOCX/PDF.

## ✅ Recursos
- Grava trechos de áudio via navegador (permite microfone).
- Transcreve com **OpenAI Whisper**.
- Organiza automaticamente PAUTAS/ENCAMINHAMENTOS (opcional, GPT).
- Valida **dados obrigatórios** (data, hora, local, participantes, assinatura).
- Gera **Word (.docx)** e **PDF (.pdf)** prontos para download.

## 🚀 Rodar localmente
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sua_chave_aqui"  # Windows: setx OPENAI_API_KEY "sua_chave_aqui"
streamlit run app.py
```

## ☁️ Publicar no Streamlit Cloud
1. Crie um repositório no GitHub e envie estes arquivos:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/secrets.toml` (veja exemplo abaixo)
2. Acesse https://share.streamlit.io/ → **New app** → selecione o repositório e o arquivo `app.py`.
3. Em **Advanced settings**:
   - Python version: 3.11 (recomendado).
4. Em **Secrets**, adicione:
```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sua_chave_da_openai"
```
5. Deploy e permita o uso do microfone no navegador.

> Observações:
> - O navegador sempre pedirá permissão para o microfone (política de segurança). Após clicar em **Iniciar**, use o widget de áudio para gravar trechos.
> - Recomenda-se gravar trechos de 30–120s para melhor precisão.
> - Custos: o Whisper é cobrado por minuto de áudio. Monitore seu uso na OpenAI.

## 🔧 Dicas
- Se `st.audio_input` não aparecer, atualize o Streamlit (>=1.35).
- Para captação contínua/streaming, considere `streamlit-webrtc` (mais complexo).