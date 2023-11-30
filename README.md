# Whisper Watcher

Watch changes to files in a folder and automatically transcribe them to a specified folder

Uses [faster whisper](https://github.com/guillaumekln/faster-whisper) for transcriptions

Results are saved in .srt format


All settings are editable in settings.yaml file as well as in GUI, remember to set observed_path and transcription_destination_path

If you specify a huggingface model, it will be automatically downloaded to the /models directory next to the script/executable.

**!IMPORTANT - audio files are discarded by default unless you set the processed_files_path**

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
upload_lag: 10

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
3. Run whisper_watcher.exe

## How to make it useful

Setup a task in task scheduler at logon:

https://winaero.com/run-app-or-script-at-logon-with-task-scheduler-in-windows-10/

1. Setup a task to sync files from your recording app on your phone to the shared network folder on your PC

How to share files over the network: https://support.microsoft.com/en-us/windows/file-sharing-over-a-network-in-windows-b58704b2-f53a-4b82-7bc1-80f9994725bf

If you have an Android phone I really recommend this app

https://play.google.com/store/apps/details?id=com.sentaroh.android.SMBSync2

2. Adjust upload lag depending on the size of your recordings and your wifi speed

3. Once your recordings land in the shared folder, they will be automatically transcribed and you can use them for further processing.
