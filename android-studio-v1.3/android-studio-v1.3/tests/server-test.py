"""Protocol tests only: Qwen inference is mocked, no model downloaded."""
import os, sys, io, base64, importlib.util, types
from pathlib import Path
os.environ['STUDIO_TOKEN'] = 'test-token-32-characters-long-abc'
spec=importlib.util.spec_from_file_location('studio_server',Path(__file__).resolve().parents[1] / 'server' / 'server.py')
m=importlib.util.module_from_spec(spec);sys.modules['studio_server']=m;spec.loader.exec_module(m)
from fastapi.testclient import TestClient
import numpy as np
import soundfile as sf
class MockModel:
    def generate_voice_design(self, **kw):
        assert kw['language']=='Spanish'
        return [np.zeros(8000,dtype=np.float32)],16000
    def create_voice_clone_prompt(self, **kw):
        assert kw['ref_audio'][0].shape[0] == 48000
        return ['prompt']
    def generate_voice_clone(self, **kw):
        assert kw['voice_clone_prompt']==['prompt']
        return [np.zeros(8000,dtype=np.float32)],16000
m.get_model=lambda mode:MockModel()
sys.modules['librosa']=types.SimpleNamespace(effects=types.SimpleNamespace(time_stretch=lambda a,rate:a))
c=TestClient(m.app);h={'Authorization':'Bearer '+os.environ['STUDIO_TOKEN']}
assert c.get('/live').status_code==200 and c.get('/live').json()=={'ok':True}
assert c.get('/health').status_code==401
assert c.get('/health',headers=h).json()['ok'] is True
assert c.post('/synthesize',headers=h,json={'mode':'design','text':'Hola','description':''}).status_code==400
r=c.post('/synthesize',headers=h,json={'mode':'design','text':'Hola mundo','description':'Voz cálida'})
assert r.status_code==200 and r.content.startswith(b'RIFF'),r.text
r=c.post('/synthesize',headers=h,json={'mode':'design','text':'Hola','description':'Voz cálida','language':'Klingon'})
assert r.status_code==422
b=io.BytesIO();sf.write(b,np.zeros(48000,dtype=np.float32),16000,format='WAV')
ref=base64.b64encode(b.getvalue()).decode()
r=c.post('/synthesize',headers=h,json={'mode':'clone','text':'Hola','reference_audio':ref,'reference_text':'Muestra de voz'})
assert r.status_code==200 and r.content.startswith(b'RIFF'),r.text
assert c.post('/synthesize',headers=h,json={'mode':'clone','text':'Hola','reference_audio':'not-base64'}).status_code==400
assert c.post('/synthesize',headers=h,json={'mode':'clone','text':'x'*12001}).status_code==422
m.lock.acquire()
try: assert c.post('/synthesize',headers=h,json={'mode':'design','text':'Hola','description':'voz'}).status_code==429
finally:m.lock.release()
assert ''.join(m.chunks('Uno. Dos. '+'Texto largo. '*200)) == 'Uno. Dos. '+'Texto largo. '*200
print('PASS server contract: public liveness, protected health, design/clone WAV, invalid languages/audio/length, concurrency. Inference mocked.')

# Local text endpoint: mock only the actual Ollama inference transport.
class OllamaResult:
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self,*a):
        import json
        return json.dumps({'done':True,'done_reason':'stop','message':{'content':'{"text":"Hola"}'}}).encode()
import json
old_open=m.urllib.request.urlopen
captured=[]
def fake_open(req,timeout):
    captured.append((req.full_url,json.loads(req.data)))
    return OllamaResult()
m.urllib.request.urlopen=fake_open
try:
    r=c.post('/generate',headers=h,json={'instructions':'Devuelve JSON','input':'Hola'})
    assert r.status_code==200,r.text
    assert json.loads(r.json()['text'])['text']=='Hola'
    assert captured[0][0]=='http://127.0.0.1:11434/api/chat'
    assert captured[0][1]['stream'] is False
    assert captured[0][1]['keep_alive']==0
    assert c.post('/generate',json={'instructions':'x','input':'x'}).status_code==401
finally:m.urllib.request.urlopen=old_open
# ASR endpoint: test streaming upload, result and cleanup with a fake model.
paths=[]
class Whisper:
    def __init__(self,*a,**kw):assert kw['device']=='cpu'
    def transcribe(self,path,**kw):
        paths.append(path)
        assert os.path.exists(path)
        return [types.SimpleNamespace(text=' Hola servidor local.')],types.SimpleNamespace(language='es')
sys.modules['faster_whisper']=types.SimpleNamespace(WhisperModel=Whisper)
r=c.post('/transcribe',headers={**h,'Content-Type':'application/octet-stream'},content=b'audio-test')
assert r.status_code==200 and 'Hola servidor local' in r.json()['text'],r.text
assert paths and not os.path.exists(paths[0])
assert c.post('/transcribe',content=b'audio-test').status_code==401
print('PASS own-server processing: Ollama routing, no cloud fallback, ASR upload, auth and temporary-file cleanup. Inference mocked.')

sys.modules.pop('faster_whisper',None)
assert c.get('/diagnostics').status_code == 401
r=c.get('/diagnostics',headers=h)
assert r.status_code==200 and r.json()['inference_verified'] is False
assert 'summary' in r.json() and 'dependencies' in r.json()
print('PASS local setup diagnostics: authorized access, explicit unverified inference, dependency/model report.')
