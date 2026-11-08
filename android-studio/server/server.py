"""Servidor Qwen para Transcriptor Studio. Ejecutar un solo worker."""
from __future__ import annotations
import base64, gc, io, os, secrets, threading
from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

TOKEN = os.environ.get('STUDIO_TOKEN', '')
if len(TOKEN) < 24:
    raise RuntimeError('Define STUDIO_TOKEN con al menos 24 caracteres aleatorios.')
app = FastAPI(title='Transcriptor Studio · Qwen', docs_url=None, redoc_url=None)
lock = threading.Lock()
loaded_model = None
loaded_mode = None

class Speech(BaseModel):
    mode: Literal['design', 'clone']
    text: str = Field(min_length=1, max_length=12000)
    language: Literal['Auto','Spanish','English','Chinese','Japanese','Korean','German','French','Russian','Portuguese','Italian'] = 'Spanish'
    description: str = Field(default='', max_length=3000)
    reference_audio: str = Field(default='', max_length=11200000)
    reference_text: str = Field(default='', max_length=5000)
    speed: float = Field(default=1, ge=0.5, le=2)
    pause_ms: int = Field(default=250, ge=0, le=1500)

def authorize(header: str | None):
    if not header or not secrets.compare_digest(header, 'Bearer ' + TOKEN):
        raise HTTPException(401, 'Token de servidor incorrecto')

@app.middleware('http')
async def max_body(request, call_next):
    # Check before JSON parsing; chunked requests are explicitly rejected.
    raw = request.headers.get('content-length', '0')
    try:
        size = int(raw)
    except ValueError:
        return Response('Invalid content length', status_code=400)
    if request.method == 'POST' and (size <= 0 or size > 16 * 1024 * 1024):
        return Response('Request size not supported', status_code=413)
    return await call_next(request)

@app.get('/health')
def health(authorization: str | None = Header(None)):
    authorize(authorization)
    return {'ok': True, 'loaded': loaded_mode, 'engine': 'Qwen3-TTS', 'version': 1}

def get_model(mode):
    global loaded_model, loaded_mode
    if loaded_mode == mode and loaded_model is not None:
        return loaded_model
    import torch
    from qwen_tts import Qwen3TTSModel
    loaded_model = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    model_id = ('Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign' if mode == 'design'
                else os.environ.get('STUDIO_CLONE_MODEL', 'Qwen/Qwen3-TTS-12Hz-0.6B-Base'))
    device = os.environ.get('STUDIO_DEVICE', 'cuda:0' if torch.cuda.is_available() else 'cpu')
    loaded_model = Qwen3TTSModel.from_pretrained(
        model_id, device_map=device,
        dtype=torch.float32 if device == 'cpu' else torch.bfloat16,
        attn_implementation='sdpa')
    loaded_mode = mode
    return loaded_model

def chunks(text, limit=600):
    result = []
    while len(text) > limit:
        cut = max(text.rfind('\n', 0, limit), text.rfind('. ', 0, limit), text.rfind(' ', 0, limit))
        if cut < limit // 2:
            cut = limit
        else:
            cut += 1
        result.append(text[:cut]); text = text[cut:]
    if text:
        result.append(text)
    return result

@app.post('/synthesize')
def synthesize(data: Speech, authorization: str | None = Header(None)):
    authorize(authorization)
    if not lock.acquire(blocking=False):
        raise HTTPException(429, 'El servidor ya está generando otra voz. Inténtalo después.')
    try:
        import numpy as np
        import soundfile as sf
        import librosa
        model = None
        prompt = None
        if data.mode == 'clone':
            try:
                raw = base64.b64decode(data.reference_audio, validate=True)
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError('máximo 8 MB')
                ref, rate = sf.read(io.BytesIO(raw), dtype='float32', always_2d=True)
                duration = len(ref) / rate
                if not 3 <= duration <= 30:
                    raise ValueError('la muestra debe durar de 3 a 30 segundos')
                ref = ref.mean(axis=1)
            except Exception as exc:
                raise HTTPException(400, 'Referencia inválida: usa WAV/FLAC/MP3 de 3–30 s; ' + str(exc)) from exc
            model = get_model(data.mode)
            prompt = model.create_voice_clone_prompt(
                ref_audio=(ref, rate), ref_text=data.reference_text.strip() or None,
                x_vector_only_mode=not bool(data.reference_text.strip()))
        elif not data.description.strip():
            raise HTTPException(400, 'Describe la voz que quieres crear')
        if model is None:
            model = get_model(data.mode)
        segments = []
        rate_out = None
        # Design is independent per segment; use a short audition and clone it
        # afterwards if consistent long narration is required.
        for part in chunks(data.text):
            if data.mode == 'design':
                wavs, sr = model.generate_voice_design(
                    text=part, language=data.language, instruct=data.description)
            else:
                wavs, sr = model.generate_voice_clone(
                    text=part, language=data.language, voice_clone_prompt=prompt)
            samples = np.asarray(wavs[0], dtype=np.float32).reshape(-1)
            if data.speed != 1:
                samples = librosa.effects.time_stretch(samples, rate=data.speed)
            if rate_out is not None and rate_out != sr:
                raise RuntimeError('Cambió la frecuencia de audio')
            rate_out = sr
            if segments and data.pause_ms:
                segments.append(np.zeros(int(sr * data.pause_ms / 1000), dtype=np.float32))
            segments.append(samples)
        audio = np.concatenate(segments)
        out = io.BytesIO()
        sf.write(out, audio, rate_out, format='WAV', subtype='PCM_16')
        return Response(out.getvalue(), media_type='audio/wav', headers={'X-Voice-Origin': 'synthetic'})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, 'No se pudo generar: ' + str(exc)) from exc
    finally:
        lock.release()
