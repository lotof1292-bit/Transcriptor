"""Servidor Qwen para Transcriptor Studio. Ejecutar un solo worker."""
from __future__ import annotations
import base64, gc, io, os, secrets, threading
from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

if os.environ.get('STUDIO_OFFLINE') == '1':
    os.environ['HF_HUB_OFFLINE'] = '1'

TOKEN = os.environ.get('STUDIO_TOKEN', '')
if len(TOKEN) < 24:
    raise RuntimeError('Define STUDIO_TOKEN con al menos 24 caracteres aleatorios.')
app = FastAPI(title='Transcriptor Studio · Servidor local', docs_url=None, redoc_url=None)
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
    if request.method == 'POST' and (size <= 0 or size > 26 * 1024 * 1024):
        return Response('Request size not supported', status_code=413)
    return await call_next(request)

@app.get('/live')
def live():
    """Sonda mínima para Docker/proxy; no revela motores ni configuración."""
    return {'ok': True}

@app.get('/health')
def health(authorization: str | None = Header(None)):
    authorize(authorization)
    return {'ok': True, 'loaded': loaded_mode, 'engine': 'Servidor propio', 'version': 2, 'capabilities':['transcribe','generate','design','clone'], 'text_model':os.environ.get('STUDIO_TEXT_MODEL','qwen3:4b'), 'asr_model':os.environ.get('STUDIO_ASR_MODEL','small')}

def release_voice():
    global loaded_model, loaded_mode
    if loaded_model is not None:
        loaded_model = None
        loaded_mode = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

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
    if not data.text.strip():
        raise HTTPException(400, 'Agrega texto para generar la narración.')
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

# Local processing: no OpenAI calls and no automatic cloud fallback.
import json, tempfile, urllib.request, urllib.error
from fastapi import Request
from starlette.concurrency import run_in_threadpool

class Generate(BaseModel):
    instructions: str = Field(min_length=1, max_length=10000)
    input: str = Field(min_length=1, max_length=60000)

@app.post('/generate')
def generate_local(data: Generate, authorization: str | None = Header(None)):
    authorize(authorization)
    if not lock.acquire(blocking=False):
        raise HTTPException(429, 'El servidor está ocupado; vuelve a intentarlo después.')
    try:
        release_voice()
        # Ollama must be installed on the server. Model selection is server-owned.
        endpoint = os.environ.get('STUDIO_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
        payload = json.dumps({'model': os.environ.get('STUDIO_TEXT_MODEL', 'qwen3:4b'),
            'messages': [{'role':'system', 'content':data.instructions}, {'role':'user', 'content':data.input}],
            'stream':False, 'format':'json', 'think':False, 'keep_alive':0,
            'options':{'temperature':0.15, 'num_ctx':32768, 'num_predict':12000}}).encode()
        req = urllib.request.Request(endpoint+'/api/chat', data=payload, headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=1800) as response:
                body = response.read(4*1024*1024+1)
            if len(body)>4*1024*1024:
                raise HTTPException(502, 'Respuesta local demasiado grande')
            result=json.loads(body)
        except urllib.error.HTTPError as exc:
            raise HTTPException(502, 'Ollama respondió HTTP '+str(exc.code)+'. Comprueba que el modelo local esté descargado.') from exc
        except urllib.error.URLError as exc:
            raise HTTPException(503, 'No se puede conectar con Ollama. Instálalo e inicia su servicio en el servidor.') from exc
        if result.get('done_reason') == 'length' or not result.get('done',False):
            raise HTTPException(422, 'El modelo local no terminó. Divide el texto en partes más pequeñas.')
        text=result.get('message',{}).get('content','')
        if not text.strip():
            raise HTTPException(502, 'El modelo local no devolvió texto')
        try:
            json.loads(text)
        except ValueError as exc:
            raise HTTPException(502, 'El modelo local devolvió JSON inválido. Prueba otra vez o usa un modelo mayor.') from exc
        return {'text':text, 'engine':'Ollama', 'model':os.environ.get('STUDIO_TEXT_MODEL','qwen3:4b')}
    finally:
        lock.release()

@app.post('/transcribe')
async def transcribe_local(request: Request, authorization: str | None = Header(None)):
    authorize(authorization)
    if not lock.acquire(blocking=False):
        raise HTTPException(429, 'El servidor está ocupado; vuelve a intentarlo después.')
    path=None
    try:
        # Bound the actual streamed body, not only the claimed Content-Length.
        with tempfile.NamedTemporaryFile(suffix='.media', delete=False) as temp:
            path=temp.name
            length=0
            async for chunk in request.stream():
                length+=len(chunk)
                if length>24*1024*1024:
                    raise HTTPException(413, 'El máximo de esta versión es 24 MB por archivo.')
                temp.write(chunk)
        if length==0:
            raise HTTPException(400, 'El archivo está vacío')
        def infer():
            release_voice()
            from faster_whisper import WhisperModel
            device=os.environ.get('STUDIO_ASR_DEVICE','cpu')
            model=WhisperModel(os.environ.get('STUDIO_ASR_MODEL','small'), device=device,
                compute_type=os.environ.get('STUDIO_ASR_COMPUTE','int8' if device=='cpu' else 'float16'),
                local_files_only=os.environ.get('STUDIO_OFFLINE','0')=='1')
            try:
                segments,info=model.transcribe(path,beam_size=5,vad_filter=True)
                text=''.join(s.text for s in segments).strip()
                return {'text':text,'language':info.language,'engine':'faster-whisper'}
            finally:
                del model
                gc.collect()
        result = await run_in_threadpool(infer)
        if not result['text']:
            raise HTTPException(422, 'No se detectó voz. Prueba un archivo donde se escuche a alguien hablar.')
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, 'No se pudo transcribir localmente: '+str(exc)) from exc
    finally:
        if path:
            try:os.unlink(path)
            except OSError:pass
        lock.release()

@app.get('/diagnostics')
def diagnostics(authorization: str | None = Header(None)):
    """Read-only setup checks. Does not download models or claim inference works."""
    authorize(authorization)
    import importlib.util
    from pathlib import Path
    dependencies = {name: importlib.util.find_spec(name) is not None
                    for name in ['faster_whisper', 'qwen_tts', 'torch', 'soundfile']}
    text_model = os.environ.get('STUDIO_TEXT_MODEL', 'qwen3:4b')
    asr_model = os.environ.get('STUDIO_ASR_MODEL', 'small')
    ollama = {'reachable': False, 'model_found': False}
    try:
        endpoint = os.environ.get('STUDIO_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
        with urllib.request.urlopen(endpoint + '/api/tags', timeout=5) as response:
            payload = json.loads(response.read(1024*1024))
        names = [item.get('name','') for item in payload.get('models', [])]
        ollama = {'reachable': True, 'model_found': text_model in names or text_model+':latest' in names}
    except Exception:
        pass
    def cached(repo, kind):
        try:
            if Path(repo).is_dir():
                path = Path(repo)
            else:
                from huggingface_hub import snapshot_download
                path = Path(snapshot_download(repo, local_files_only=True))
            if kind == 'asr':
                return (path/'model.bin').is_file()
            shards = list(path.glob('*.safetensors'))
            if not shards:
                return False
            index = path/'model.safetensors.index.json'
            if index.is_file():
                expected = set(json.loads(index.read_text()).get('weight_map',{}).values())
                if not expected or not all((path/name).is_file() for name in expected):
                    return False
            return all(p.stat().st_size > 0 for p in shards)
        except Exception:
            return False
    asr_repo = asr_model if '/' in asr_model or Path(asr_model).is_dir() else 'Systran/faster-whisper-'+asr_model
    found = {'asr':cached(asr_repo,'asr'),
             'voice_design':cached('Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign','voice'),
             'voice_clone':cached(os.environ.get('STUDIO_CLONE_MODEL','Qwen/Qwen3-TTS-12Hz-0.6B-Base'),'voice')}
    lines = ['Dependencias: '+(', '.join(k for k,v in dependencies.items() if not v) or 'instaladas')+'.',
             'Ollama: '+('conectado' if ollama['reachable'] else 'no responde')+'; modelo de texto '+text_model+': '+('encontrado' if ollama['model_found'] else 'no encontrado')+'.',
             'Whisper '+asr_model+': '+('archivo de modelo encontrado' if found['asr'] else 'modelo no encontrado en caché')+'.',
             'Qwen diseño: '+('pesos encontrados' if found['voice_design'] else 'pesos no encontrados')+'; clonación: '+('pesos encontrados' if found['voice_clone'] else 'pesos no encontrados')+'.',
             'Estos controles no prueban la inferencia ni todos los archivos auxiliares de los modelos.']
    if not all(dependencies.values()):lines[0]='Faltan dependencias: '+', '.join(k for k,v in dependencies.items() if not v)+'.'
    return {'ok':True, 'text_model':text_model,'asr_model':asr_model,
            'dependencies':dependencies,'ollama':ollama,'cached_weights':found,
            'inference_verified':False,'summary':'\n'.join(lines)}
