from pathlib import Path
import os
import subprocess
import sys
import types

import requests
import soundfile as sf
import torch
import torchaudio


CUDA_PATHS = [
    r"C:\Users\bruno\AppData\Local\Programs\Python\Python312\Lib\site-packages\nvidia\cublas\bin",
    r"C:\Users\bruno\AppData\Local\Programs\Python\Python312\Lib\site-packages\nvidia\cudnn\bin",
    r"C:\Users\bruno\AppData\Local\Programs\Python\Python312\Lib\site-packages\nvidia\cuda_nvrtc\bin",
]

for path in CUDA_PATHS:
    if os.path.exists(path):
        os.add_dll_directory(path)
        os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]

sys.stdout.reconfigure(encoding="utf-8")


if not hasattr(torchaudio, "backend"):
    class _AudioMetaData:
        def __init__(self, sample_rate=0, num_frames=0, num_channels=0, **_):
            self.sample_rate = sample_rate
            self.num_frames = num_frames
            self.num_channels = num_channels

    _common = types.ModuleType("torchaudio.backend.common")
    _common.AudioMetaData = _AudioMetaData
    _backend = types.ModuleType("torchaudio.backend")
    _backend.common = _common
    sys.modules["torchaudio.backend"] = _backend
    sys.modules["torchaudio.backend.common"] = _common
    torchaudio.backend = _backend

import demucs.separate
from df.enhance import init_df, enhance
from silero_vad import load_silero_vad, get_speech_timestamps, collect_chunks
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR / "Samples"

audio_file = SAMPLES_DIR / "BRWO260415940.wav"
step1_ffmpeg_file = SAMPLES_DIR / "1_ffmpeg.wav"
demucs_out_dir = SAMPLES_DIR / "demucs_out"
step3_deepfilter_file = SAMPLES_DIR / "3_deepfilter.wav"
step4_vad_file = SAMPLES_DIR / "4_vad.wav"

device = "cuda"

subprocess.run(
    [
        "ffmpeg", "-y", "-i", str(audio_file),
        "-ac", "1",
        "-af", "aresample=16000,highpass=f=80,lowpass=f=7500,loudnorm",
        "-ar", "16000",
        str(step1_ffmpeg_file),
    ],
    check=True,
)

# 2. Demucs: remove música e sons de fundo
demucs.separate.main(
    [
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "-o", str(demucs_out_dir),
        str(step1_ffmpeg_file),
    ]
)
vocals_file = demucs_out_dir / "htdemucs" / step1_ffmpeg_file.stem / "vocals.wav"

df_model, df_state, _ = init_df()

wav, sr = sf.read(str(vocals_file), dtype="float32", always_2d=True)
wav = torch.from_numpy(wav.T).mean(dim=0, keepdim=True)
wav = torchaudio.functional.resample(wav, sr, df_state.sr())

enhanced = enhance(df_model, df_state, wav)
enhanced = torchaudio.functional.resample(enhanced, df_state.sr(), 16000)
sf.write(str(step3_deepfilter_file), enhanced.squeeze(0).cpu().numpy(), 16000)

vad_model = load_silero_vad()

wav16k = enhanced.squeeze(0)
speech_timestamps = get_speech_timestamps(wav16k, vad_model, sampling_rate=16000)
speech_only = collect_chunks(speech_timestamps, wav16k)
sf.write(str(step4_vad_file), speech_only.cpu().numpy(), 16000)

model = WhisperModel(
    "large-v3-turbo",
    device="cuda",
    compute_type="float16",
)

segments, info = model.transcribe(
    str(step4_vad_file),
    language="pt",
    beam_size=5,
)

texto = "".join(seg.text for seg in segments)

payload = {
    "model": "gemma-4-E2B-it",
    "messages": [
        {
            "role": "system",
            "content": '"# System Você é um analista sênior de chamadas do call center da MIDEA. # Objetivo Seu objetivo como analista sênior é realizar uma análise profunda de uma transcrição feita entre um de nossos atendentes e clientes. Você deverá realizar essa análise de maneira minuciosa entendendo o contexto geral e problemático. Você receberá a transcrição contendo as seguintes informações privadas: - Nome do cliente - cpf do cliente - Endereço do cliente (cep,rua,bairro) - telefone do cliente - ... Receberá também as informações referentes à abertura da chamada do cliente: - Motivo da ligação - Problemas referentes à máquina em questão Essa transcrição por muitas vezes possuirá lacunas textuais causadas pelo modelo de transcrição utilizado, apesar disso você não deverá inventar informações. Após a sua análise você deverá enviar em formato json a análise feita, nesse seguinte formato: ```json { "analise_chamada": { "nome_cliente": String nome do cliente da chamada, "nome_contato_cadastrado": String nome do cliente registrado no protocolo, "cpf":String formated xxx.xxx.xxx-xx, "telefone": String formated (DDD)xxxxx-xxxx , "cep": String, "maquina": { "tipo": String, "capacidade": String, "modelo":String }, "motivo_da_ligacao": String, "problema_enfrentado_na_maquina": String, "protocolos_gerados": { "protocolo_atendimento": String, "ordem_servico": String }, "contexto_endereco": { "cidade_estimada": String, "estado":String }, "abertura_de_protoculo_pelo_atendente":Boolean } } ```"',
        },
        {
            "role": "user",
            "content": texto,
        },
    ],
}

response = requests.post(
    "http://localhost:1234/v1/chat/completions",
    json=payload,
)

print(response.json()["choices"][0]["message"]["content"])