import datetime
import io
import os
import pyaudio
import pvcobra
import pvleopard
import pvporcupine
import struct
import sys
import textwrap
import threading
import time
import tkinter as tk

from PIL import Image, ImageTk
from pvleopard import *
from pvrecorder import PvRecorder
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from time import sleep

pv_access_key = "QxI3hdPlXsoQxvZGOXHIzsFjCUsq54eEImH3PhsaIA6zCdtFCq5GoQ=="
stability_api_key = "sk-9fr1k7CCQOovuvABbHNQU1JGf1jTtzcQ9kSpREgFrgJkJALI"

audio_stream = None
cobra = None
pa = None
porcupine = None
recorder = None
global text_var
global screen_width, screen_height

count = 0

CloseProgram_list = ["Close program", "End program", "Exit program", "Stop program",
                     "Close the program", "End the program", "Exit the program",
                     "Stop the program", "Exit"]

DisplayOn_list = ["Turn on", "Wake up"]

DisplayOff_list = ["Turn off", "Sleep"]

Save_list = ["Save", "Keep", "Save it", "Keep it", "Save image", "Keep image",
             "Save the image", "Keep the image", "Save that image", "Keep that image"]

root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root['bg'] = 'black'
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.overrideredirect(True)
root.attributes("-fullscreen", True)
root.update()

def close_image_window():
    windows = root.winfo_children()
    for window in windows:
        if isinstance(window, tk.Toplevel):
            if window.attributes("-fullscreen"):
                print("closing image window")
                window.destroy()

def close_program():
    recorder = Recorder()
    recorder.stop()
    o.delete
    recorder = None
    sys.exit("Program terminated")

def current_time():
    time_now = datetime.datetime.now()
    formatted_time = time_now.strftime("%m-%d-%Y %I:%M %p\n")
    print("The current date and time is:", formatted_time)

def generate_image(prompt):
    stability_api = client.StabilityInference(
        key=stability_api_key,
        verbose=True,
    )

    answers = stability_api.generate(
        prompt=prompt,
        steps=50,
        cfg_scale=8.0,
        width=1024,
        height=1024,
        samples=1,
        sampler=generation.SAMPLER_K_DPMPP_2M
    )

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                raise ValueError("Your request activated the API's safety filters and could not be processed. "
                                 "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img_data = io.BytesIO(artifact.binary)
                img = Image.open(img_data)
                return img

def detect_silence():
    cobra = pvcobra.create(access_key=pv_access_key)

    silence_pa = pyaudio.PyAudio()

    cobra_audio_stream = silence_pa.open(
        rate=cobra.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=cobra.frame_length
    )

    last_voice_time = time.time()

    while True:
        cobra_pcm = cobra_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)
        if cobra.process(cobra_pcm) > 0.2:
            last_voice_time = time.time()
        else:
            silence_duration = time.time() - last_voice_time
            if silence_duration > 0.8:
                print("End of query detected\n")
                cobra_audio_stream.stop_stream
                cobra_audio_stream.close()
                cobra.delete()
                last_voice_time = None
                break

def display_on(transcript):
    for word in DisplayOn_list:
        if word in transcript:
            print("\'"f"{word}\' detected")
            current_time
            os.system("xset dpms force on")
            print("\nTurning on display.")
            sleep(1)

def display_off(transcript):
    for word in DisplayOff_list:
        if word in transcript:
            print("\'"f"{word}\' detected")
            current_time
            print("\nTurning off display.")
            os.system("xset dpms force off")
            sleep(1)

def draw_request(transcript):
    global text_var

    prompt = transcript
    print("You requested the following image: " + prompt)
    print("\nCreating image...\n")

    wrapped_prompt = textwrap.fill(prompt, width=35)

    text_var.set("Generating new image...\n\n" + wrapped_prompt)
    text_window.update()

    image = generate_image(prompt)

    print("Displaying generated image.")

    update_image(image)

def listen():
    global image_window
    global text_window
    global text_var
    cobra = pvcobra.create(access_key=pv_access_key)

    close_image_window()

    listen_pa = pyaudio.PyAudio()

    listen_audio_stream = listen_pa.open(
        rate=cobra.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=cobra.frame_length
    )
    Statement = "Listening"
    text_var.set("Listening")
    text_window.update()

    print("Listening...")

    while True:
        listen_pcm = listen_audio_stream.read(cobra.frame_length)
        listen_pcm = struct.unpack_from("h" * cobra.frame_length, listen_pcm)

        if cobra.process(listen_pcm) > 0.3:
            print("Voice detected")
            listen_audio_stream.stop_stream
            listen_audio_stream.close()
            cobra.delete()
            break

def display_logo():
    global image_window
    global screen_width, screen_height
    image_window = tk.Toplevel(root)
    image_window.title("Image Window")
    image_window.geometry(f"{screen_width}x{screen_height}+0+0")
    image_window.attributes("-fullscreen", True)
    image_window.overrideredirect(True)
    image_window.configure(bg='black')
    image = Image.open("/home/deadeye/skynet/Lumina Logo.png")
    original_width, original_height = image.size
    scale = max(screen_width / original_width, screen_height / original_height)
    scaled_width = int(original_width * scale)
    scaled_height = int(original_height * scale)
    image = image.resize((scaled_width, scaled_height))
    image_photo = ImageTk.PhotoImage(image)
    image_canvas = tk.Canvas(image_window, bg='#000000', width=screen_width, height=screen_height)
    x = (screen_width - scaled_width) // 2
    y = (screen_height - scaled_height) // 2
    image_canvas.create_image(x, y, image=image_photo, anchor=tk.NW)
    image_canvas.pack()
    image_window.update()

def on_message(transcript, DisplayOn_list, DisplayOff_list, CloseProgram_list, Save_list):
    words = transcript.split(',')
    for word in words:
        if word in CloseProgram_list:
            close_program()
        elif word in DisplayOn_list:
            display_on(transcript)
        elif word in DisplayOff_list:
            display_off(transcript)
        elif word in Save_list:
            save_image(image_label)
        else:
            draw_request(transcript)

def save_image(image_label):
    global text_var
    global text_window
    global image
    global image_window
    global screen_width, screen_height
    timestamp = datetime.datetime.now().strftime("%m-%d-%Y")
    saved_images_path = "/home/deadeye/skynet/"
    output_filename = f"{saved_images_path}{image_label}_{timestamp}.png"
    image.save(output_filename, format="PNG")
    save_message = (f"Image saved as\n\n" + output_filename)
    print(save_message)
    wrapped_save_message = textwrap.fill(save_message, width=60)
    text_var.set(wrapped_save_message)
    text_window.update()
    sleep(3)
    image_window = tk.Toplevel(root)
    image_window.title("Image Window")
    image_window.geometry(f"{screen_width}x{screen_height}+0+0")
    image_window.attributes("-fullscreen", True)
    image_window.overrideredirect(True)
    image_window.configure(bg='black')
    image = image
    original_width, original_height = image.size
    scale = max(screen_width / original_width, screen_height / original_height)
    scaled_width = int(original_width * scale)
    scaled_height = int(original_height * scale)
    image = image.resize((scaled_width, scaled_height))
    image_photo = ImageTk.PhotoImage(image)
    image_canvas = tk.Canvas(image_window, bg='#000000', width=screen_width, height=screen_height)
    x = (screen_width - scaled_width) // 2
    y = (screen_height - scaled_height) // 2
    image_canvas.create_image(x, y, image=image_photo, anchor=tk.NW)
    image_canvas.pack()
    image_window.update()

def text_window_func():
    global text_var
    global text_window
    global screen_width, screen_height
    text_window = tk.Toplevel(root)
    text_window.geometry(f"{screen_width}x{screen_height}+0+0")
    text_window.overrideredirect(True)
    text_window.focus_set()
    text_window.configure(bg='black')
    text_var = tk.StringVar()
    label = tk.Label(text_window, textvariable=text_var, bg='#000000', fg='#ADD8E6', font=("Arial Black", 72))
    label.pack(side=tk.TOP, anchor=tk.CENTER, pady=screen_height // 4)
    print("text window open")
    text_window.update()

def update_image(image):
    global image_window
    global screen_width, screen_height
    image_window = tk.Toplevel(root)
    image_window.title("Image Window")
    image_window.geometry(f"{screen_width}x{screen_height}+0+0")
    image_window.attributes("-fullscreen", True)
    image_window.overrideredirect(True)
    image_window.configure(bg='black')
    original_width, original_height = image.size
    scale = max(screen_width / original_width, screen_height / original_height)
    scaled_width = int(original_width * scale)
    scaled_height = int(original_height * scale)
    image = image.resize((scaled_width, scaled_height))
    image_photo = ImageTk.PhotoImage(image)
    image_canvas = tk.Canvas(image_window, bg='#000000', width=screen_width, height=screen_height)
    x = (screen_width - scaled_width) // 2
    y = (screen_height - scaled_height) // 2
    image_canvas.create_image(x, y, image=image_photo, anchor=tk.NW)
    image_canvas.pack()
    image_window.update()

def wake_word():
    porcupine = None
    pa = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(
            access_key=pv_access_key,
            keyword_paths=["sky_net_linux.ppn"]
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected!")
                break

    finally:
        if porcupine is not None:
            porcupine.delete()

        if audio_stream is not None:
            audio_stream.close()

        if pa is not None:
            pa.terminate()

class Recorder(threading.Thread):
    def __init__(self):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        recorder = PvRecorder(device_index=-1, frame_length=512)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()

        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass

        return self._pcm

try:
    o = create(access_key=pv_access_key)

    count = 0

    while True:
        try:
            if count == 0:
                display_logo()
            else:
                pass
            count = 1
            recorder = Recorder()
            wake_word()
            text_window_func()
            recorder = Recorder()
            recorder.start()
            listen()
            detect_silence()
            transcript, words = o.process(recorder.stop())
            recorder.stop()
            print("You said: " + transcript)
            on_message(transcript, DisplayOn_list, DisplayOff_list, CloseProgram_list, Save_list)
            image_label = transcript.replace(" ", "_")
            recorder.stop()
            o.delete
            recorder = None

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

except KeyboardInterrupt:
    sys.exit("\nExiting Lumina")
