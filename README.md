# Observing transcriber

Watch changes to files in a folder and automatically transcribe them to a specified folder

Uses [faster whisper](https://github.com/guillaumekln/faster-whisper) for transcriptions

Results are saved in .srt format

All settings are in settings.yaml file, remember to set observed_path and transcription_destination_path

### settings.yaml

```yaml
# whisper settings
# one of https://huggingface.co/Systran or path to local model
model_path_or_id: small.en

device: cpu # or gpu

# file settings
observed_path: <SET PATH TO OBSERVED FOLDER>
transcription_destination_path: <WHERE YOU WANT TO SAVE TRANSCRIPTIONS>

# optional

# if you want to keep original audio files, save them in this path
processed_files_path: 

# wait for this many seconds before starting transcription
upload_lag: 1
```

## Usage 

### From source

Requires:
- python

Optional:
- make

Steps:

1. Clone repository

```bash
git clone https://github.com/krystianMoras/observing_transcriber.git
```
2. Update settings.yaml

3. If you don't have it already install poetry

```bash
pip install poetry
```

4. Run script
```bash
cd observing_transcriber
make install
make run
```

or

```bash
cd observing_transcriber
poetry install
poetry run python watcher.py
```

### From executable

1. Download latest [release](https://github.com/krystianMoras/observing_transcriber/releases)
2. Update settings.yaml
3. Run observing_transcriber.exe

