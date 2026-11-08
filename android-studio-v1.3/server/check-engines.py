"""Run real HTTP inference checks against a running Studio server."""
import argparse
import base64
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import wave
import io


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8790')
    parser.add_argument('--token-file', type=Path, default=Path(__file__).with_name('server-token.txt'))
    parser.add_argument('--media', type=Path, required=True, help='Audio o video corto con voz')
    parser.add_argument('--reference', type=Path, help='WAV autorizado de 3–30 s para probar clonación')
    parser.add_argument('--expected', help='Palabra que debe aparecer en la transcripción')
    parser.add_argument('--asr-only', action='store_true')
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme != 'https' and (url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'}):
        parser.error('Usa HTTPS para servidores externos.')
    token = args.token_file.read_text().strip()
    if not args.asr_only and args.reference is None:
        parser.error('Proporciona --reference para comprobar la clonación.')
    failures = []

    def check(label, route, body, content_type, validate):
        request = Request(args.url.rstrip('/') + route, body, {
            'Authorization': 'Bearer ' + token, 'Content-Type': content_type})
        try:
            with urlopen(request, timeout=1800) as response:
                output = response.read(32 * 1024 * 1024 + 1)
            validate(output)
            print(f'{label}: comprobado', flush=True)
        except Exception as error:
            detail = error.read(2048).decode(errors='replace') if isinstance(error, HTTPError) else str(error)
            failures.append(label)
            print(f'{label}: error: {detail}', flush=True)

    def json_body(label, path, data, validate):
        check(label, path, json.dumps(data).encode(), 'application/json', validate)

    def transcript(output):
        text = json.loads(output).get('text', '').strip()
        if not text or (args.expected and args.expected.casefold() not in text.casefold()):
            raise ValueError('La transcripción no contiene la voz o la palabra esperada.')

    def result_text(output):
        result = json.loads(json.loads(output)['text'])
        if not isinstance(result.get('text'), str) or not result['text'].strip():
            raise ValueError('El motor devolvió un resultado vacío.')

    def wav(output):
        with wave.open(io.BytesIO(output)) as audio:
            if audio.getnframes() < audio.getframerate() // 4:
                raise ValueError('La narración es demasiado corta.')
            if not any(audio.readframes(audio.getnframes())):
                raise ValueError('La narración está en silencio.')

    check('Transcripción', '/transcribe', args.media.read_bytes(), 'application/octet-stream', transcript)
    if not args.asr_only:
        for label, instruction in (
            ('Reescritura', 'Reescribe en español conservando Ana y 2026. Devuelve JSON con campo text.'),
            ('Traducción', 'Traduce al inglés conservando Ana y 2026. Devuelve JSON con campo text.'),
        ):
            json_body(label, '/generate', {'input': 'Ana leyó un libro en 2026.', 'instructions': instruction}, result_text)
        json_body('Diseño de voz', '/synthesize', {
            'mode': 'design', 'text': 'Esta es una prueba de Transcriptor Studio.',
            'description': 'Voz cálida y pausada en español.', 'language': 'Spanish'}, wav)
        json_body('Clonación', '/synthesize', {
            'mode': 'clone', 'text': 'Esta es una prueba de la voz de referencia.',
            'reference_audio': base64.b64encode(args.reference.read_bytes()).decode(),
            'language': 'Spanish'}, wav)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
