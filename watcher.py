from pathlib import Path
import yaml
from faster_whisper import WhisperModel
import asyncio
from watchfiles import awatch, Change
from pathlib import Path
import logging
import srt
import shutil
import sys
import tkinter as tk
import tkinter.filedialog as filedialog
import multiprocessing

def resolve_path(path):
    if getattr(sys, "frozen", False):
        # If the 'frozen' flag is set, we are in bundled-app mode!
        resolved_path = Path(sys._MEIPASS) / path
    else:
        # Normal development mode. Use os.getcwd() or __file__ as appropriate in your case...
        resolved_path = Path(__file__).parent / path

    return resolved_path

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

config = yaml.load(open(resolve_path("settings.yaml"), "r"), Loader=yaml.FullLoader)


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


async def watcher():

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

def start_watcher():
    asyncio.run(watcher())

if __name__ == '__main__':
    multiprocessing.freeze_support()
    # create tkinter window

    root = tk.Tk()
    asyncio_process = multiprocessing.Process(target=start_watcher)

    def restart_thread(asyncio_process):
        logger.info("Restarting watcher with new settings")
        asyncio_process.terminate()
        asyncio_process = multiprocessing.Process(target=start_watcher)
        asyncio_process.start()

    def select_observed_path(observed_path_label):
        observed_path = filedialog.askdirectory()
        config["observed_path"] = observed_path
        observed_path_label.config(text=f"Observed path: {observed_path}")
        yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
        restart_thread(asyncio_process)

    def select_transcription_destination(transcription_destination_label):
        transcription_destination = filedialog.askdirectory()
        config["transcription_destination_path"] = transcription_destination
        transcription_destination_label.config(text=f"Transcription destination: {transcription_destination}")
        yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
        restart_thread(asyncio_process)

    def select_processed_files_path(processed_files_path_label):
        processed_files_path = filedialog.askdirectory()
        config["processed_files_path"] = processed_files_path
        processed_files_path_label.config(text=f"Processed files path: {processed_files_path}")
        yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
        restart_thread(asyncio_process)

    def select_model_path_or_id(model_path_or_id_label):
        input_path_or_id = model_path_or_id_input.get()
        if input_path_or_id:
            model_path_or_id = input_path_or_id
        else:

            model_path_or_id = filedialog.askdirectory()
            model_path_or_id_input.delete(0, tk.END)
            model_path_or_id_input.insert(0, model_path_or_id)
        config["model_path_or_id"] = model_path_or_id
        model_path_or_id_label.config(text=f"Model path or id: {model_path_or_id}")
        yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
        restart_thread(asyncio_process)

    def select_device(device_label):
        # switch between cpu and gpu
        device = "cpu" if config["device"] == "cuda" else "cuda"
        config["device"] = device
        device_label.config(text=f"Device: {device}")

        yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
        restart_thread(asyncio_process)

    def select_upload_lag(upload_lag_label):
        upload_lag = tk.simpledialog.askinteger("Upload lag", "Enter upload lag in seconds")
        upload_lag_label.config(text=f"Upload lag: {upload_lag}")
        config["upload_lag"] = upload_lag
        yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
        restart_thread(asyncio_process)

    def enable_processed_files_path(processed_files_path_label, processed_files_path_button):
        if save_files.get():
            processed_files_path_label.config(state="normal")
            processed_files_path_button.config(state="normal")
            select_processed_files_path(processed_files_path_label)
        else:
            processed_files_path_label.config(state="disabled")
            processed_files_path_button.config(state="disabled")
            config["processed_files_path"] = None
            yaml.dump(config, open(resolve_path("settings.yaml"), "w"), sort_keys=False)
            restart_thread(asyncio_process)

    root.title("Whisper Watcher")

    root.geometry("500x500")

    # show current observed path

    observed_path_label = tk.Label(root, text=f"Observed path: {observed_path}")
    observed_path_label.pack()
    observed_path_button = tk.Button(root, text="Select observed path", command=lambda: select_observed_path(observed_path_label))
    observed_path_button.pack()

    # show current transcription destination

    transcription_destination_label = tk.Label(root, text=f"Transcription destination: {transcription_destination}")
    transcription_destination_label.pack()
    transcription_destination_button = tk.Button(root, text="Select transcription destination", command=lambda: select_transcription_destination(transcription_destination_label))
    transcription_destination_button.pack()

    # show current processed files path


    # save processed files checkbox
    save_files = tk.BooleanVar(value=processed_files_path is not None)
    processed_files_path_label = tk.Label(root, text=f"Processed files path: {processed_files_path}", state="normal" if save_files.get() else "disabled")
    processed_files_path_button = tk.Button(root, text="Select processed files path", command=lambda: select_processed_files_path(processed_files_path_label), state="normal" if save_files.get() else "disabled")
    
    processed_files_checkbox = tk.Checkbutton(root, text="Save processed files", variable=save_files, command=lambda: enable_processed_files_path(processed_files_path_label, processed_files_path_button))
    processed_files_checkbox.pack()
    processed_files_path_button.pack()
    processed_files_path_label.pack()

    # show current model path or id

    model_path_or_id_label = tk.Label(root, text=f"Model path or id: {model_path_or_id}")
    model_path_or_id_label.pack()
    # text box for model path or id
    model_path_or_id_input = tk.Entry(root)
    model_path_or_id_input.pack()
    model_path_or_id_button = tk.Button(root, text="Select model path or id", command=lambda: select_model_path_or_id(model_path_or_id_label))
    model_path_or_id_button.pack()



    # show current device

    device_label = tk.Label(root, text=f"Device: {device}")
    device_label.pack()
    device_toggle_button = tk.Button(root, text="Toggle device", command=lambda : select_device(device_label))
    device_toggle_button.pack()


    # show current upload lag

    upload_lag_label = tk.Label(root, text=f"Upload lag: {upload_lag}")
    upload_lag_label.pack()
    upload_lag_button = tk.Button(root, text="Select upload lag", command=lambda : select_upload_lag(upload_lag_label))
    upload_lag_button.pack()


    # view logs

    def view_logs():
        logs = open("watcher.log", "r").read()
        logs_window = tk.Toplevel(root)
        logs_window.title("Logs")
        logs_window.geometry("500x500")
        logs_text = tk.Text(logs_window)
        logs_text.insert(tk.END, logs)
        logs_text.pack()

    logs_button = tk.Button(root, text="View logs", command=view_logs)
    logs_button.pack()

    # start watcher

    def on_close():
        asyncio_process.terminate()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    asyncio_process.start()

    root.mainloop()


