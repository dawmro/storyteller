import tkinter as tk
import customtkinter as ctk 

from PIL import ImageTk

from datetime import datetime
import time
import openai
import re
import os
import urllib.request
from gtts import gTTS
from moviepy.editor import *
from tqdm.auto import tqdm

from api_key import API_KEY


# Use API_KEY imported from api_key.py file
openai.api_key = API_KEY



def tStamp():

    return str("["+datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')+" UTC]")



def createFolders(timeStamp: str):

    if not os.path.exists(timeStamp+"/text"):
        os.makedirs(timeStamp+"/text")
    
    if not os.path.exists(timeStamp+"/audio"):
        os.makedirs(timeStamp+"/audio")
            
    if not os.path.exists(timeStamp+"/images"):
        os.makedirs(timeStamp+"/images")
        
    if not os.path.exists(timeStamp+"/videos"):
        os.makedirs(timeStamp+"/videos")



def generateText(text, model_engine):
    
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=text,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.9,
    )
    return completions.choices[0].text
    
    
    
def createVideoClips(paragraphs, timeStamp):

    i=1
    # Loop through each paragraph and generate an imageh
    for para in paragraphs[:-1]:
    
        print(f"{tStamp()} Generate New AI Image From Paragraph...")
        response = openai.Image.create(
            prompt=para.strip(),
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        urllib.request.urlretrieve(image_url, f"{timeStamp}/images/image{i}.jpg")
        print(f"{tStamp()} The Generated Image Saved in Images Folder!")

        # Create gTTS instance and save to a file
        tts = gTTS(text=para, lang='en', slow=False)
        tts.save(f"{timeStamp}/audio/voiceover{i}.mp3")
        print(f"{tStamp()} The Paragraph Converted into VoiceOver & Saved in Audio Folder!")

        # Load the audio file using moviepy
        print(f"{tStamp()} Extract voiceover and get duration...")
        audio_clip = AudioFileClip(f"{timeStamp}/audio/voiceover{i}.mp3")
        audio_duration = audio_clip.duration

        # Load the image file using moviepy
        print(f"{tStamp()} Extract Image Clip and Set Duration...")
        image_clip = ImageClip(f"{timeStamp}/images/image{i}.jpg").set_duration(audio_duration)

        # Use moviepy to create a text clip from the text
        print(f"{tStamp()} Add text to Video Clip")
        screensize = (1024,1024)
        text_clip = TextClip(para, fontsize=70, color="white", stroke_color="black", stroke_width=2, size=screensize, method='caption', align="South")
        text_clip = text_clip.set_duration(audio_duration)

        # Use moviepy to create a final video by concatenating
        # the audio, image, and text clips
        print(f"{tStamp()} Concatenate Audio, Image, Text to Create Final Clip...")
        clip = image_clip.set_audio(audio_clip)
        video = CompositeVideoClip([clip, text_clip])

        # Save Video Clip to a file
        video = video.write_videofile(f"{timeStamp}/videos/video{i}.mp4", fps=24)
        print(f"{tStamp()} The Video{i} Has Been Created Successfully!")
        i+=1



def createListOfClips(timeStamp):

    clips = []
    l_files = os.listdir(timeStamp+"/videos")
    l_files.sort(key=lambda f: int(re.sub('\D', '', f)))
    for file in l_files:
        clip = VideoFileClip(f"{timeStamp}/videos/{file}")
        clips.append(clip)
    
    return clips



if __name__ == "__main__":

    
    app = tk.Tk()
    app.geometry("732x182")
    app.title("Storyteller") 
    ctk.set_appearance_mode("dark") 
    
    image_icon = tk.PhotoImage(file="logo.png")
    app.iconphoto(False, image_icon)

    prompt = ctk.CTkEntry(master=app, height=40, width=712, font=("Arial", 20), text_color="black", fg_color="white") 
    prompt.place(x=10, y=10)
    
     
    # Create timestamp for current run
    timeStamp = str(int(time.time()))
    print(f"{tStamp()} Timestamp: {timeStamp}")
    
    def generate(): 
        
        # Create directiories for text, audio, images and video files
        createFolders(timeStamp)
        
        # Select model to use
        model_engine = "text-davinci-003"
        
        # Prompt to generate story from given text
        #input_text = input(f"{tStamp()} Story about what topic do you want to create?: \n>")
        input_text = prompt.get()
        print(input_text)
        
        # Save input text to file
        with open(timeStamp+"/text/input_text.txt", "w") as file:
            file.write(input_text.strip())
        
        # Generate story
        print(f"{tStamp()} Text generation start...")
        try:
            story = generateText(input_text, model_engine)
            print(f"{tStamp()} Text generation done!")
        except:
            print(f"{tStamp()} Cannot connect with OpenAI servers. \nProbable cause: No Internet connection, Invalid API token")
            exit()
        
        # Display created story
        print(story)
        
        # Save story to file
        with open(timeStamp+"/text/generated_story.txt", "w") as file:
            file.write(story.strip())
        
        # Remove spaces from begining and end of the text
        story.strip()
        
        # Split the text by , and . into paragraphs
        paragraphs = re.split(r"[,.]", story)
        
        # Create video clip for each paragraph
        print(f"{tStamp()} Creating Video Clips for each paragraph start...")
        createVideoClips(paragraphs, timeStamp)
        print(f"{tStamp()} Creating Video Clips for each paragraph done!")

        # Create sorted list of clips
        clips = createListOfClips(str(timeStamp))
        
        # Combine all clips into final video
        print(f"{tStamp()} Concatenate All The Clips to Create a Final Video...")
        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.write_videofile(timeStamp+"/final_video.mp4")
        print(f"{tStamp()} The Final Video Has Been Created Successfully!")
        
        trigger1.configure(fg_color="Green", state="active") 
        trigger.configure(fg_color="Red", state="disabled")

    trigger = ctk.CTkButton(master=app, height=40, width=120, font=("Arial", 20), text_color="white", fg_color="blue", command=generate) 
    trigger.configure(text="Generate") 
    trigger.place(x=306, y=60)


    def snd1():
        command = timeStamp+"\\final_video.mp4"
        os.system(command)

    trigger1 = ctk.CTkButton(master=app, height=40, width=120, font=("Arial", 20), text_color="white", fg_color="Red", command=snd1)
    trigger1.configure(text="Play Video", state="disabled") 
    trigger1.place(x=306, y=120)
    

    app.mainloop()

    
    


# Story about three pigs living in a wooden hut in the middle of the forest




