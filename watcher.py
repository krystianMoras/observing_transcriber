from pathlib import Path
import yaml
from faster_whisper import WhisperModel
import asyncio
from watchfiles import awatch, Change
from pathlib import Path
import logging
import srt
import shutil

# clear last log
open('watcher.log', 'w').close()

# log to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SUPPORTED_FILETYPES = [".m4a", ".mp4", ".wav"]

config = yaml.load(open(f"{Path(__file__).parent}/settings.yaml", "r"), Loader=yaml.FullLoader)


observed_path = Path(config["observed_path"])
transcription_destination = Path(config["transcription_destination_path"])

if config.get("processed_files_path"):
    processed_files_path = Path(config["processed_files_path"])
else:
    processed_files_path = None

upload_lag = config.get("upload_lag", 5)
model_path_or_id = config["model_path_or_id"]
device = config["device"]


def filter(change:Change, path:str):
    if change != Change.deleted and Path(path).suffix in SUPPORTED_FILETYPES:
        return True
    return False

def segments_to_srt(segments):

    srt_segments = []

    for i, segment in enumerate(segments):
        srt_segment = srt.Subtitle(
        index=i,
        start=srt.timedelta(seconds=segment.start),
        end=srt.timedelta(seconds=segment.end),
        content=segment.text
    )
        srt_segments.append(srt_segment)

    composed = srt.compose(srt_segments)

    return composed



async def process_recordings(observed_path:Path, transcription_destination:Path, model_path_or_id:str, device:str, processed_files_path:Path=None, upload_lag:int=5):
    await asyncio.sleep(upload_lag)

    # for each file in voice_recordings_public_path

    logger.info(f"Processing recordings in {observed_path}")

    # find paths to all audio files in voice_recordings_public_path

    paths_to_audio_files = [file for file in observed_path.iterdir() if file.suffix in SUPPORTED_FILETYPES]
    logger.info(f"Found {len(paths_to_audio_files)} audio files to transcribe")

    if len(paths_to_audio_files) > 0:    
        model = WhisperModel(model_path_or_id, device=device, compute_type="default")

        for file in paths_to_audio_files:
            # transcribe
            logger.info(f"Transcribing {file.as_posix()}")
            segments, _ = model.transcribe(file.as_posix())
            segments = list(segments)
            
            logger.info(f"Transcribed")

            # write srt file
            srt_file = transcription_destination / f"{file.stem}.srt"
            logger.info(f"Writing srt file to {srt_file.as_posix()}")
            with srt_file.open("w") as f:
                f.write(segments_to_srt(segments))

            # move file to processed_files_path
            if processed_files_path:
                logger.info(f"Moving file to {processed_files_path.as_posix()}")
                new_file_path = processed_files_path / file.name
                shutil.move(file, new_file_path)

            else:
                logger.info(f"Deleting file {file.as_posix()}")
                file.unlink()




async def main():

    task = None
    logger.info(f"Processing existing files in {observed_path}")

    await process_recordings(observed_path, transcription_destination, model_path_or_id, device, processed_files_path, upload_lag)

    logger.info(f"Done processing existing files in {observed_path}")
    logger.info(f"Watching for file changes in {observed_path}")

    async for changes in awatch(observed_path, watch_filter=filter):
        logger.info(changes)
        if task:
            task.cancel()

        # start a task to transcribe the recording
        task = asyncio.create_task(process_recordings(observed_path, transcription_destination, model_path_or_id, device, processed_files_path, upload_lag))


if __name__ == '__main__':
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('stopped via KeyboardInterrupt')
