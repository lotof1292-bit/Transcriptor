"""Protocol tests only: Qwen inference is mocked, no model downloaded."""
import os, sys, io, base64, importlib.util, types
from pathlib import Path
os.environ['STUDIO_TOKEN'] = 'test-token-32-characters-long-abc'
project_root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio_server',project_root/'server'/'server.py')
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
print('PASS server contract: auth, health, design/clone WAV, invalid languages/audio/length, concurrency. Inference mocked.')
