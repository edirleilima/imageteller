from fastapi import FastAPI, File, UploadFile, Query, Form, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import FileResponse
import mimetypes
from openai import OpenAI, OpenAIError
from typing import List
import os
import openai
import base64
import time
import uuid
import requests
from os.path import exists
import io
from pydantic import BaseModel
import urllib3
import re
import random
import mysql.connector
import json
import aiohttp
import websockets
import asyncio
from ollama import Client
from ollama import ResponseError
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

#data folders
DATA_PATH = os.getenv("DATA_PATH")
IMAGE_FOLDER = f"{DATA_PATH}/images"
CHAPTER_FOLDER = f"{DATA_PATH}/chapters/"

#LLM Settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE")
LLM_CHARACTER_LIB_PROVIDER = os.getenv("LLM_CHARACTER_LIB_PROVIDER")
LLM_CHARACTER_LIB_MODEL = os.getenv("LLM_CHARACTER_LIB_MODEL")
LLM_CHARACTER_LIB_TEMPERATURE = os.getenv("LLM_CHARACTER_LIB_TEMPERATURE")
LLM_IMAGE_PROVIDER = os.getenv("LLM_IMAGE_PROVIDER")
LLM_IMAGE_MODEL = os.getenv("LLM_IMAGE_MODEL")
LLM_IMAGE_TEMPERATURE = os.getenv("LLM_IMAGE_TEMPERATURE")
OLLAMA_SERVER = os.getenv("OLLAMA_SERVER")
OLLAMA_SERVER_IMAGE = os.getenv("OLLAMA_SERVER_IMAGE")
VLLM_SERVER = os.getenv("VLLM_SERVER")
OPENAI_KEY = os.getenv("OPENAI_KEY")

NLP_API_SERVER = os.getenv("NLP_API_SERVER")

#database settings
db_config = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'database': os.getenv("DB_DATABASE")
}

#api settings
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access_token"
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

#website settings
ADMIN_USER = os.getenv("ADMIN_USER")
IMAGE_URL = os.getenv("IMAGE_URL")
CHAPTER_URL = os.getenv("CHAPTER_URL")
MAX_FILE_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

#comfyui settings
comfyui_username = os.getenv("COMFYUI_USERNAME")
comfyui_password = os.getenv("COMFYUI_PASSWORD")
comfyui_credentials = base64.b64encode(f"{comfyui_username}:{comfyui_password}".encode('utf-8')).decode('utf-8')
comfyui_auth_header = f"Basic {comfyui_credentials}"
comfyui_server_address = os.getenv("COMFYUI_SERVER")
comfyui_client_id = str(uuid.uuid4())
comfyui_negative_prompt = "((poorly drawn hands)), ((poorly drawn face)), (((deformed))), blurry, ((bad anatomy)), (((bad proportions))), ((extra limbs)), cloned face, ((((ugly)))), (((duplicate))), ((mutilated)), extra fingers, (too many fingers), mutated hands, (((disfigured))), out of frame, extra limbs, gross proportions, (malformed limbs), ((missing arms)), ((missing legs)), (((extra arms))), (((extra legs))), (fused fingers), (((long neck)))"
comfyui_workflow = "/code/app/assets/workflows/workflow_flux_schnell_8_api.json"

image_generation_queue = asyncio.Queue()

async def init_life_span(app: FastAPI):
    asyncio.create_task(image_generation_worker())
    yield

client_openai = OpenAI(api_key = OPENAI_KEY)
client_ollama = Client(host=OLLAMA_SERVER)
client_ollama_image = Client(host=OLLAMA_SERVER_IMAGE)
client_vllm = OpenAI(base_url=VLLM_SERVER, api_key="NONE")

app = FastAPI(root_path="/imageteller-api", docs_url=None, redoc_url=None, openapi_url=None, lifespan=init_life_span)

class Chapter(BaseModel):    
    story_id: str
    chapter_id: str
    user: str
    text: str

origins = [
    os.getenv("DOMAIN_URL")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Character library

male_actors = [
    "Leonardo DiCaprio",
    "Brad Pitt",
    "Johnny Depp",
    "Robert Downey Jr.",
    "Tom Hanks",
    "George Clooney",
    "Matt Damon",
    "Ryan Gosling",
    "Chris Hemsworth",
    "Tom Hardy",
    "Idris Elba",
    "Chadwick Boseman",
    "Joseph Gordon-Levitt",
    "Colin Firth",
    "Matthew McConaughey"
]

female_actors = [
    "Scarlett Johansson",
    "Anne Hathaway",
    "Natalie Portman",
    "Emma Stone",
    "Amy Adams",
    "Emma Watson",
    "Rachel McAdams",
    "Jennifer Lawrence",
    "Angelina Jolie",
    "Sandra Bullock"
]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
  
def send_openai_request(messages, model_name, temperature):
    can_continue = True
    result = ""
    try:
        response = client_openai.chat.completions.create(model=model_name, messages=messages, temperature=temperature, max_tokens=4096, top_p=1, frequency_penalty=0, presence_penalty=0)
        result = response.choices[0].message.content.strip()
        can_continue = True
    except openai.APITimeoutError as e:
        can_continue = False
        print(f"OpenAI API request timed out: {e}")
        time.sleep(1)
    except openai.InternalServerError as e:
        can_continue = False
        print(f"OpenAI API returned an API Error: {e}")
        time.sleep(1)
    except openai.APIConnectionError as e:
        can_continue = False
        print(f"OpenAI API request failed to connect: {e}")
        time.sleep(1)
    except openai.BadRequestError as e:
        can_continue = True
        print(f"OpenAI API request was invalid: {e}")
        time.sleep(1)
    except openai.AuthenticationError as e:
        can_continue = True
        print(f"OpenAI API request was not authorized: {e}")
        time.sleep(1)
    except openai.PermissionDeniedError as e:
        can_continue = True
        print(f"OpenAI API request was not permitted: {e}")
        time.sleep(1)
    except openai.RateLimitError as e:
        can_continue = False
        print(f"OpenAI API request exceeded rate limit: {e}")
        time.sleep(1)
    except openai.ConflictError as e:
        can_continue = False
        print(f"OpenAI API service unavailable: {e}")
        time.sleep(1)
    except openai.NotFoundError as e:
        can_continue = False
        print(f"OpenAI API service unavailable: {e}")
        time.sleep(1)
    except openai.UnprocessableEntityError as e:
        can_continue = False
        print(f"OpenAI API service unavailable: {e}")
        time.sleep(1)
    return can_continue, result

def send_ollama_request(messages, model_name, temperature):
    can_continue = True
    result = ""
    try:
        response = client_ollama.chat(model=model_name, messages=messages, think=False, options = {'temperature': temperature})
        result = response["message"]["content"].strip()
        can_continue = True
    except ResponseError as e:
        print(f"Ollama Error: {e.error}")
        can_continue = True
    return can_continue, result

def send_ollama_image_request(messages, model_name, temperature):
    can_continue = True
    result = ""
    try:
        response = client_ollama_image.chat(model=model_name, messages=messages, options = {'temperature': temperature})
        result = response["message"]["content"].strip()
        can_continue = True
    except ResponseError as e:
        print(f"Ollama Error: {e.error}")
        can_continue = True
    return can_continue, result

def send_vllm_request(messages, model_name, temperature):
    can_continue = True
    result = ""
    try:
        response = client_vllm.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
                "reasoning_effort": "low",
            },
        )
        result = (response.choices[0].message.content or "").strip()
        can_continue = True
    except OpenAIError as e:
        print(f"vLLM Error: {e}")
        can_continue = True
    return can_continue, result

def send_llm_request(messages, provider, model_name, temperature):
    result = ""
    can_continue = False
    numtries = 0
    while not can_continue:
        if provider == "openai":
            can_continue, result = send_openai_request(messages, model_name, temperature)
        elif provider == "ollama":
            can_continue, result = send_ollama_request(messages, model_name, temperature)
        elif provider == "vllm":
            can_continue, result = send_vllm_request(messages, model_name, temperature)
        numtries = numtries + 1
        if (numtries > 15):
            break
    return re.sub(r'<think>.*?</think>', '', result.strip(), flags=re.IGNORECASE | re.DOTALL).replace('*', '')

def image_to_base64(image_file):
    image_data = image_file.read()
    encoded_string = base64.b64encode(image_data).decode("utf-8")
    return encoded_string

def convert_to_rgb(image):
    if image.mode in ("RGBA", "P"):
        return image.convert("RGB")
    return image

def convert_to_jpeg(image, quality=100):
    byte_arr = io.BytesIO()
    image.save(byte_arr, format="JPEG", quality=quality)
    return byte_arr.getvalue()

def is_jpeg(file):
    return file.lower().endswith((".jpg", ".jpeg"))

def process_image(uploaded_file):
    image = Image.open(uploaded_file)
    # resize image
    base_width = 512
    if image.size[0] > base_width:    
        wpercent = (base_width / float(image.size[0]))
        hsize = int((float(image.size[1]) * float(wpercent)))
        image = image.resize((base_width, hsize), Image.Resampling.LANCZOS)

    if not is_jpeg(uploaded_file):
        image = convert_to_rgb(image)
        image_bytes = convert_to_jpeg(image)  
    else:
        byte_arr = io.BytesIO()
        image.save(byte_arr, format="JPEG")
        image_bytes = byte_arr.getvalue()

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    return encoded_image


def generate_image_description(image_url, file_path, caption):
    caption_instruction = ""
    if caption != "":
        caption_instruction = "When generating the description, take into account that the image has the following caption: " + caption
    full_instructions = "Analyze the provided image and write a short description (a single paragraph) of the subjects present in the image, including their actions and appearance. Focus on key elements such as the interactions between subjects and any significant environmental details that contribute to the mood and context of the scene. Write the description in a single paragraph without headers, bullet points, or numbered items. " + caption_instruction
    if LLM_IMAGE_PROVIDER == "openai":
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": full_instructions
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": "high"
                },
                },
            ],
            }
        ]
        return send_llm_request(messages, LLM_IMAGE_PROVIDER, LLM_IMAGE_MODEL, LLM_IMAGE_TEMPERATURE)
    else:
        encoded_image = process_image(file_path)
        messages=[
            {
                "role": "user",
                "content": full_instructions,
                "images": [encoded_image],
            }
        ]        
        can_continue, result = send_ollama_image_request(messages, LLM_IMAGE_MODEL, LLM_IMAGE_TEMPERATURE) 
        result = result.replace("\n", " ") 
        return result 

def generate_story_prompt(image_descriptions, genre, desc_is_array):
    genre_definition = ""
    if genre == "Comedy":
        genre_definition = "The world is just and strict but finally becomes more free and desirable. The protagonist is initially hilariously vain, self-important and aspiring, but at the end conforms to the world's norms."
    elif genre == "Romance":
        genre_definition = "The world is just but momentarily disturbed by the occurrence of a villainy. The protagonist performs a heroic adventurous quest."
    elif genre == "Tragedy":
        genre_definition = "The world is just but governed by fate and unforgiving. The protagonist misbehaves and finally succumbs and dies."
    elif genre == "Satire":
        genre_definition = "The world is not just, it is dystopian, grotesque and absurd. The protagonist is helpless."
    elif genre == "Mystery":
        genre_definition = "The world is just but has unknown or unexplained or fantastic elements. The protagonist makes a discovery."
    elif genre == "Achiever":
        genre_definition = "An Achiever player focuses on completing challenges, gaining rewards, and demonstrating mastery. Therefore, the narrative must be structured around goal-oriented tasks, measurable progress, milestones, and the desire for recognition. The protagonist is driven by accomplishment and overcoming increasingly difficult challenges."
    elif genre == "Explorer":
        genre_definition = "An Explorer player is focused on discovery, curiosity, and unraveling hidden secrets. Therefore, the narrative must be structured around uncovering mysteries, exploring unknown locations, and the joy of finding something new. The protagonist is driven by a sense of wonder, investigation, and the thrill of the unknown."
    elif genre == "Socializer":
        genre_definition = "A Socializer player focuses on relationships, interactions, and communication. Therefore, the narrative must be structured around friendships, alliances, community building, and the social dynamics between characters. The protagonist is driven by the need for connection, cooperative tasks, and shared experiences."
    elif genre == "Killer":
        genre_definition = "A Killer player focuses on competition, dominance, and asserting power over others. Therefore, the narrative must be structured around conflict, strategic moves, and competitive challenges. The protagonist is driven by a desire for victory, control, and exerting influence over other characters."

    if genre == "Data Storytelling":
        prompt = "Using the following set of sequentially ordered image descriptions, write a compelling narrative that highlights key insights, connects the dots between different data points, and presents a clear and engaging story. The story must have a creative title written using markdown header level 1 (#). Follow the sequence of events as represented in the descriptions, maintaining consistency in mood and context. Ensure the narrative has a clear beginning, middle, and end. Use metaphors, analogies, and emotional appeal to make the story engaging. Avoid referring directly to the images or describing them. Instead, weave the data into the narrative naturally, as if explaining the insights to someone who has never seen the images. Also suggest potential implications, actions, or reflections based on the insights presented. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. Write your response in english only. \n Image descriptions: \n"
    elif genre == "Achiever" or genre == "Explorer" or genre == "Socializer" or genre == "Killer":
        prompt = "Using the following set of sequentially ordered image descriptions, write a cohesive, engaging and complete story resembling a book narrative. The story must have a creative title written using markdown header level 1 (#). The story must include the sequence of events represented in the descriptions, maintaining consistency in mood and context. In addition, the protagonist's journey presented in the narrative must be based on Bartle's definition of the " + genre + " player type. " + genre_definition + " Ensure the narrative has a clear beginning, middle, and end. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. When writing the story, assign names to the subjects, describe their visual attributes (eye color, hair color, hairstyle) and clothes (type, color, style), and develop their characters based on their described actions and appearances. Ensure the story incorporates all key elements from the image descriptions, including the subjects, their interactions, and significant environmental details. Focus on creating a narrative and dialogue that brings the story to life, rather than merely describing the images. Exclude any details specific to the image format, such as speech balloons, text boxes, or floating text. Write your response in english only. \n Image descriptions: \n"
    else:
        if genre_definition == "":
            prompt = "Using the following set of sequentially ordered image descriptions, write a cohesive, engaging and complete story resembling a book narrative. The story must have a creative title written using markdown header level 1 (#). When writing the story, assign names to the subjects, describe their visual attributes (eye color, hair color, hairstyle) and clothes (type, color, style), and develop their characters based on their described actions and appearances. Ensure the story incorporates all key elements from the descriptions, including the subjects, their interactions, and significant environmental details. Follow the sequence of events as represented in the descriptions, maintaining consistency in mood and context. Ensure the narrative has a clear beginning, middle, and end. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. Focus on creating a narrative and dialogue that brings the story to life, rather than merely describing the images. Exclude any details specific to the image format, such as speech balloons, text boxes, or floating text. Write your response in english only. \n Image descriptions: \n"
        else:
            prompt = "Using the following set of sequentially ordered image descriptions, write a cohesive, engaging and complete story resembling a book narrative in the " + genre + " genre. The story must have a creative title written using markdown header level 1 (#). When writing the story, assign names to the subjects, describe their visual attributes (eye color, hair color, hairstyle) and clothes (type, color, style), and develop their characters based on their described actions and appearances. Ensure the story incorporates all key elements from the descriptions, including the subjects, their interactions, and significant environmental details. Follow the sequence of events as represented in the descriptions, maintaining consistency in mood and context. Ensure the narrative has a clear beginning, middle, and end. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. Incorporate genre-specific elements such as setting, tone, themes, and character types to clearly reflect the " + genre + " genre. Focus on creating a narrative and dialogue that brings the story to life, rather than merely describing the images. Exclude any details specific to the image format, such as speech balloons, text boxes, or floating text. Write your response in english only. Use the following definition for the " + genre + " genre: " + genre_definition + "\n Image descriptions: \n"
    if desc_is_array:
        for i in range(0, len(image_descriptions)):
            prompt = prompt + str(i) + ". " + image_descriptions[i] + "\n" 
    else:
        prompt = prompt + image_descriptions

    return prompt

def generate_story(image_descriptions, genre):
    prompt = generate_story_prompt(image_descriptions, genre, True) 
    if genre == "Data Storytelling":
        messages = [{"role": "system", "content": "You are an expert data storyteller."}]  
    else:
        messages = [{"role": "system", "content": "You are a creative story writer."}]  
    messages.append({"role": "user", "content": prompt})

    return send_llm_request(messages, LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE)

def regenerate_chapter_for_story(story, chapter_id):
    prompt = generate_story_prompt(story['image_desc'], story['genre'], False)    
    if story['genre'] == "Data Storytelling":
        messages = [{"role": "system", "content": "You are an expert data storyteller."}]  
    else:
        messages = [{"role": "system", "content": "You are a creative story writer."}] 
    messages.append({"role": "user", "content": prompt})    

    story_text = "# " + story['title'] + "\n"
    regenerate_chapter_title = ""
    for chapter in story['chapters']:
        story_text = story_text + "## " + chapter['title'] + "\n"
        story_text = story_text + "" + chapter['text'] + "\n"
        if str(chapter['id']) == str(chapter_id):
            regenerate_chapter_title = chapter['title']
    
    messages.append({"role": "assistant", "content": story_text})

    if story['genre'] == "Data Storytelling":
        regenerate_prompt = "Reformulate \"" + regenerate_chapter_title + "\". Make significant changes to the description and structure of the chapter, while ensuring it stays consistent with the preceding chapters. Feel free to introduce new elements or perspectives. Ensure that the reformulated chapter leads to different developments in the subsequent chapters. Write the full story. Write your response in english only."
    else: 
        regenerate_prompt = "Reformulate \"" + regenerate_chapter_title + "\". Make significant changes to the events, dialogue, and character interactions within this chapter, while ensuring it stays consistent with the preceding chapters. Feel free to introduce new elements, twists, or perspectives. Ensure that the reformulated chapter leads to different developments in the subsequent chapters. Write the full story. Write your response in english only."
    messages.append({"role": "user", "content": regenerate_prompt})
    
    return send_llm_request(messages, LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE)

def save_story_to_db(parsed_story, user_id, genre, image_desc): 
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    image_desc_str = ""
    for i in range(0, len(image_desc)):
        image_desc_str = image_desc_str + str(i) + ". " + image_desc[i] + "\n" 
    try:
        cursor.execute("INSERT INTO story (title, genre, image_desc, user_id, deleted) VALUES (%s, %s, %s, %s, 2)", 
                       (parsed_story['title'], genre, image_desc_str, user_id))
        story_id = cursor.lastrowid
        parsed_story['id'] = story_id
        for chapter in parsed_story['chapters']:
            cursor.execute(
                "INSERT INTO chapter (story_id, title, text, alignment) VALUES (%s, %s, %s, %s)",
                (story_id, chapter['title'], chapter['text'], chapter['alignment'])
            )
            chapter_id = cursor.lastrowid
            chapter['id'] = chapter_id
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return parsed_story

def update_story_to_db(parsed_story, story_id, chapter_id): 
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE chapter SET deleted = 1 WHERE story_id = %s AND id >= %s", (story_id, chapter_id))
        parsed_story['id'] = story_id
        for chapter in parsed_story['chapters']:
            cursor.execute("SELECT * FROM chapter WHERE story_id = %s AND title = %s AND deleted = 0", (story_id, chapter['title']))
            old_chapter = cursor.fetchone()  
            if old_chapter:
                chapter['id'] = old_chapter[0]
                chapter['title'] = old_chapter[2]
                chapter['text'] = old_chapter[3]
                chapter['alignment'] = old_chapter[4]
                
            else:
                cursor.execute(
                    "INSERT INTO chapter (story_id, title, text, alignment) VALUES (%s, %s, %s, %s)",
                    (story_id, chapter['title'], chapter['text'], chapter['alignment'])
                )
                chapter_id = cursor.lastrowid
                chapter['id'] = chapter_id
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return parsed_story

def parse_story(markdown_story):
    lines = markdown_story.split('\n')
    title = ""
    alignments = ["left", "right", "full"]
    chapters = []
    chapter_title = ""
    chapter_text = ""
    title_regex = re.compile(r"^# (.+)")
    chapter_title_regex = re.compile(r"^## (.+)")
    for line in lines:
        title_match = title_regex.match(line)
        chapter_title_match = chapter_title_regex.match(line)
        if title_match:
            title = title_match.group(1)
        elif chapter_title_match:
            if chapter_title:
                chapters.append({
                    "title": chapter_title.replace("**", ""), 
                    "text": chapter_text.strip(),
                    "alignment": random.choice(alignments)
                    })
                chapter_text = ""
            chapter_title = chapter_title_match.group(1)
        else:
            chapter_text += line + "\n"
    if chapter_title:
        chapters.append({
            "title": chapter_title.replace("**", ""), 
            "text": chapter_text.strip(),
            "alignment": random.choice(alignments)
            })
    return {"title": title.replace("**", ""), "chapters": chapters}

def update_character_library(text, character_library):
    prompt = "Story Text: " + text + " \n\nCharacter Library: " + character_library + "\n\nRead the provided story text and identify the relevant characters mentioned, focusing on those who are named and visually described (e.g., physical appearance, clothing, expressions). For each character, extract and summarize only their visually observable attributes and age group (e.g., infant, child, teenager, adult, senior, elder, ancient). Do not include personality traits, ideological descriptions, or narrative roles. If the text does not provide visual and clothing details for a character, generate the information according to the narrative context. Ensure that the description of all characters includes their visual attributes (all characters must have a hair color, hairstyle, and eye color defined) and clothes details (all characters must have a clothing type and color defined). Use the following format: NAME: DESCRIPTION, where NAME identifies the character's name (followed by a colon), and DESCRIPTION is a concise paragraph summarizing the character's key visually observable details, such as hair color, eye color, age group, clothing type, and clothing type. This should be concise yet comprehensive enough to maintain consistency across scenes. If a character is already in the Character Library but new details are provided, update the existing entry instead of creating a new one. Ensure that each character pair NAME: DESCRIPTION is presented within square brackets: [NAME: DESCRIPTION]. \n\nEnsure that the Character Library does not include characters whose names are defined by generic role descriptors such as 'villager', 'father', 'dragon' or other unnamed individuals.\n\nVery important: you must write only the Character Library without adding commentaries or notes to your response. Write your response in english only."
    messages = [{"role": "system", "content": ""}]  
    messages.append({"role": "user", "content": prompt})
    return send_llm_request(messages, LLM_CHARACTER_LIB_PROVIDER, LLM_CHARACTER_LIB_MODEL, LLM_CHARACTER_LIB_TEMPERATURE)

def extract_character_names(text):
    pattern = r"\[([^\]]+)\]"
    names = re.findall(pattern, text)
    return names

def parse_character_actor(input_string):
    character_actor_dict = {}
    pairs = input_string.split(';')
    for pair in pairs:
        if pair.strip():
            character, actor = pair.split(':')
            character_actor_dict[character.strip()] = actor.strip()
    return character_actor_dict

def convert_actor_library_to_string(library):
    pairs = [f"{character}:{actor}" for character, actor in library.items()]
    result_string = '; \n'.join(pairs) + '; \n'    
    return result_string

def get_random_actor(library, gender, males, females):
    actor_list = males if gender == "male" else females
    random_actor = random.choice(actor_list)
    while random_actor in library.values():
        random_actor = random.choice(actor_list)
    return random_actor

def normalize_actor_library(library):
    normalized_library = {}    
    for full_name, actor in library.items():
        name_parts = full_name.split()
        first_name = name_parts[0]
        normalized_library[full_name] = actor
        if first_name.lower() not in ["dr", "mrs", "mr", "miss", "ms", "sir", "lady", "lord", "prof", "captain", "detective", "inspector"]:
            if first_name not in normalized_library:
                normalized_library[first_name] = actor
        if len(name_parts) > 1:
            last_name = name_parts[-1]
            if last_name.isalpha() and last_name not in normalized_library:
                normalized_library[last_name] = actor
    return normalized_library

def remove_titles(name):
    titles = [r"Dr\.", r"Mrs\.", r"Mr\.", "Miss", r"Ms\.", "Sir", "Lady", "Lord", r"Prof\.", "Captain", "Detective", "Inspector"]
    pattern = r'^(?:' + '|'.join(titles) + r')\s*'
    cleaned_name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
    return cleaned_name

def update_actor_library(actor_library, image_prompt):
    library = parse_character_actor(actor_library)
    character_names = extract_character_names(image_prompt)
    for name in character_names:
        cleaned_name = remove_titles(name)
        if cleaned_name in library:
            continue        
        gender = get_gender(cleaned_name.split()[0], image_prompt) 
        actor = get_random_actor(library, gender, male_actors, female_actors)        
        library[cleaned_name] = actor
        normalized_names = normalize_actor_library({cleaned_name: actor})
        library.update(normalized_names)
    return library

def replace_actors_in_prompt(actor_library, image_prompt):
    def replace_name(match):
        character_name = match.group(1)
        cleaned_name = remove_titles(character_name)
        actor_name = actor_library.get(cleaned_name, cleaned_name)
        return f"({actor_name}:1.2)"    
    return re.sub(r'\[([^\]]+)\]', replace_name, image_prompt)

def generate_illustration_description(chapter, character_library):
    prompt = "Story Chapter: " + chapter + "\n\nCharacter Library: " + character_library + "\n\nIdentify a single significant event in the provided story chapter and write a concise description (maximum of 80 words) to be used as input for a Stable Diffusion model to generate an illustration. Focus on the characters' actions, interactions, and the environment. Only include in the description characters who are explicitly mentioned in the story chapter and refer to them by their names in the generated description. \n\nWhen describing the characters, include all details related to their visual attributes (such as age group, hair color, hairstyle, eye color, clothing type, and clothing colors). If any visual or clothing details for a character are missing from both the chapter and the Character Library, create appropriate attributes that are consistent with the story's setting, genre, and tone. Ensure these details are realistic and coherent with the story context. \n\nVery important: you must write only the description without adding formatting elements, commentaries, or notes to your response. Refer to all characters by name. Write your response in english only."
    messages = [{"role": "system", "content": "You are a creative story writer."}]  
    messages.append({"role": "user", "content": prompt})
    return send_llm_request(messages, LLM_CHARACTER_LIB_PROVIDER, LLM_CHARACTER_LIB_MODEL, LLM_CHARACTER_LIB_TEMPERATURE)

async def image_generation_worker():
    while True:
        future, params = await image_generation_queue.get()
        try:
            result = await comfyui_generate_image_flux_async(*params)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            image_generation_queue.task_done()

async def comfyui_queue_prompt_async(prompt):
    p = {"prompt": prompt, "client_id": comfyui_client_id}
    headers = {"Authorization": comfyui_auth_header}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://{comfyui_server_address}/prompt", json=p, headers=headers) as resp:
            return await resp.json()

async def comfyui_get_image_async(filename, subfolder, folder_type):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    headers = {"Authorization": comfyui_auth_header}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://{comfyui_server_address}/view", params=params, headers=headers) as resp:
            return await resp.read()

async def comfyui_get_history_async(prompt_id):
    headers = {"Authorization": comfyui_auth_header}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://{comfyui_server_address}/history/{prompt_id}", headers=headers) as resp:
            return await resp.json()

async def comfyui_get_images_async(ws, prompt, uri, headers):
    prompt_id = (await comfyui_queue_prompt_async(prompt))['prompt_id']
    output_images = {}
    while True:        
        try:
            out = await asyncio.wait_for(ws.recv(), timeout=30)
        except asyncio.TimeoutError:
            print("WebSocket recv timed out.")
            await asyncio.sleep(15)
            ws = await websockets.connect(uri, additional_headers=headers)
            prompt_id = (await comfyui_queue_prompt_async(prompt))['prompt_id']
            continue  
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed unexpectedly: {e}")
            await asyncio.sleep(15)
            ws = await websockets.connect(uri, additional_headers=headers)
            prompt_id = (await comfyui_queue_prompt_async(prompt))['prompt_id']
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            await asyncio.sleep(15)
            ws = await websockets.connect(uri, additional_headers=headers)
            prompt_id = (await comfyui_queue_prompt_async(prompt))['prompt_id']
            continue

        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = (await comfyui_get_history_async(prompt_id))[prompt_id]
    for node_id, node_output in history['outputs'].items():
        if 'images' in node_output:
            images_output = []
            for image in node_output['images']:
                image_data = await comfyui_get_image_async(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
            output_images[node_id] = images_output
    return output_images

async def comfyui_generate_image_flux_async(workflow, prompt, negative, seed, filename):
    with open(workflow, "r") as file:
        promptdata = json.load(file)

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    promptdata["6"]["inputs"]["text"] = prompt
    promptdata["25"]["inputs"]["noise_seed"] = seed

    uri = f"wss://{comfyui_server_address}/ws?clientId={comfyui_client_id}"
    headers = {"Authorization": comfyui_auth_header}
    async with websockets.connect(uri, additional_headers=headers) as ws:
        images = await comfyui_get_images_async(ws, promptdata, uri, headers)

    if images:
        bytestream = io.BytesIO(images["9"][0])
        with open(filename, "wb") as outfile:
            outfile.write(bytestream.getbuffer())

def generate_character_tags(text, character_library):
    url = NLP_API_SERVER + "/tag-names/"
    payload = {"text": text, "library": character_library}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output = response.json().get("output")
        return output
    else:
        print(f"tag-names failed with status code: {response.status_code}")
    return text

def get_gender(name, storyevent):
    url = NLP_API_SERVER + "/classify-gender-using-pronouns/"
    payload = {"name": name, "text": storyevent}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output = response.json().get("output")
        if output:
            if output == "unknown":
                return get_name_gender(name)
            else:
                return output
        else:
            print("classify-gender-using-pronouns error: no output")
    else:
        print(f"classify-gender-using-pronouns failed with status code: {response.status_code}")
    return ""

def get_name_gender(name):
    url = NLP_API_SERVER + "/classify-gender/"
    payload = {"text": name}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output = response.json().get("output")
        if output:
            return output
        else:
            print("classify-gender error: no output")
    else:
        print(f"classify-gender failed with status code: {response.status_code}")
    return ""

def validate_file_type(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename

async def get_api_key(api_key_query: str = Security(api_key_query), api_key_header: str = Security(api_key_header)):
    if api_key_query == API_KEY or api_key_header == API_KEY:
        return api_key_query or api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(api_key: str = Depends(get_api_key)):
    return get_swagger_ui_html(openapi_url=f"/imageteller-api/openapi.json?{API_KEY_NAME}={api_key}", title="docs")

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(api_key: str = Depends(get_api_key)):
    return get_redoc_html(openapi_url=f"/imageteller-api/openapi.json?{API_KEY_NAME}={api_key}", title="redoc")

@app.get("/openapi.json", include_in_schema=False)
async def openapi(api_key: str = Depends(get_api_key)):
    return app.openapi()

@app.post("/image-to-story/")
async def image_to_story(files: List[UploadFile] = File(...), 
                                  captions: List[str] = Form(...), 
                                  genre: str = Query(...), 
                                  user: str = Query(...)):
    descriptions = []
    if captions is None:
        captions = [''] * len(files)
    elif len(captions) < len(files):
        captions.extend([''] * (len(files) - len(captions)))
    for index, file in enumerate(files):
        contents = await file.read()
        # Validate file size and type
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        validate_file_type(file.filename)
        # Sanitize filename and save file
        unique_filename = str(uuid.uuid4()) + sanitize_filename(os.path.splitext(file.filename)[-1])
        file_path = os.path.join(IMAGE_FOLDER, unique_filename)
        file_url = IMAGE_URL + unique_filename
      
        with open(file_path, "wb") as f:
            f.write(contents)

        desc = generate_image_description(file_url, file_path, captions[index])
        descriptions.append(desc)
    story_markdown = generate_story(descriptions, genre)
    story = parse_story(story_markdown)
    saved_story = save_story_to_db(story, user, genre, descriptions)
    return saved_story

@app.api_route("/images/{image_name}", methods=["GET", "HEAD"])
async def get_image(image_name: str):
    safe_name = os.path.basename(image_name)
    image_path = os.path.join(IMAGE_FOLDER, safe_name)
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    mime_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(image_path, media_type=mime_type)

@app.post("/illustrate-chapter/")
async def illustrate_chapter(chapter: Chapter):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM story WHERE id = %s AND user_id = %s AND deleted = 2", (chapter.story_id, chapter.user))
        story = cursor.fetchone()  
        if story:
            character_library = story[7] if story[7] else ""
            actor_library_str = story[8] if story[8] else ""
            character_library = update_character_library(chapter.text, character_library)
            prompt = generate_illustration_description(chapter.text, character_library)
            prompt = generate_character_tags(prompt, character_library)
            actor_library = update_actor_library(actor_library_str, prompt)
            improved_prompt = replace_actors_in_prompt(actor_library, prompt)
            actor_library_str = convert_actor_library_to_string(actor_library)
            cursor.execute("UPDATE story SET characters = %s, actors = %s WHERE id = %s AND user_id = %s", (character_library, actor_library_str, chapter.story_id, chapter.user))
            conn.commit()
            style = "Photography, realistic detailed skin, 4k, highly detailed, diffused soft lighting, shallow depth of field, sharp focus, hyperrealism, cinematic lighting."
            imgfilename = str(chapter.story_id) + "_" + str(chapter.chapter_id) + ".png"
            imgfullpath = CHAPTER_FOLDER + imgfilename

            params = (comfyui_workflow, improved_prompt + " " + style, comfyui_negative_prompt, -1, imgfullpath)            
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            await image_generation_queue.put((future, params))
            await future

            cursor.close()
            conn.close()
            return {"url": CHAPTER_URL + str(chapter.story_id) + "/" + str(chapter.chapter_id)}
        else:
            imgfilename = str(chapter.story_id) + "_" + str(chapter.chapter_id) + ".png"
            cursor.close()
            conn.close()
            return {"url": CHAPTER_URL + str(chapter.story_id) + "/" + str(chapter.chapter_id)}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    cursor.close()
    conn.close()
    return {}

@app.api_route("/chapters/{story_id}/{chapter_id}", methods=["GET", "HEAD"])
async def get_image(story_id: int, chapter_id: int):
    image_path = os.path.join(CHAPTER_FOLDER, str(story_id) + "_" + str(chapter_id) + ".png")
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    mime_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(image_path, media_type=mime_type)

@app.post("/get-stories/")
async def get_stories(user: str = Query(...)):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        if (user == ADMIN_USER):
            cursor.execute("SELECT * FROM story")
        else:
            cursor.execute("SELECT * FROM story WHERE (user_id = %s OR user_id = '') AND deleted = 0", (user,))
        stories = cursor.fetchall()  
        all_stories = []
        for story in stories:
            candelete = 1
            if (story[2] == "") or (user == ADMIN_USER):
                candelete = 0
            all_stories.append({'id': story[0], 'title': story[1], 'date': story[5], 'can_delete': candelete})        
        cursor.close()
        conn.close()
        return all_stories
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return []

@app.post("/get-story/")
async def get_story(id: str = Query(...), user: str = Query(...)):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        if (user == ADMIN_USER):
            cursor.execute("SELECT * FROM story WHERE id = %s", (id, ))
        else:
            cursor.execute("SELECT * FROM story WHERE id = %s AND (user_id = %s OR user_id = '') AND deleted = 0", (id, user))
        story = cursor.fetchone()  
        if story:
            story_data = {'id': story[0], 'title': story[1]}
            cursor.execute("SELECT * FROM chapter WHERE story_id = %s AND deleted = 0", (id,))
            chapters = cursor.fetchall()
            story_data['chapters'] = [{'id':chapter[0], 'title': chapter[2], 'text': chapter[3], 'alignment': chapter[4]} for chapter in chapters ]
            cursor.close()
            conn.close()
            return story_data
        else:
            return {}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return {}

@app.post("/save-story/")
async def save_story(id: str = Query(...), user: str = Query(...)):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM story WHERE id = %s AND user_id = %s AND deleted = 2", (id, user))
        story = cursor.fetchone()  
        if story:
            cursor.execute("UPDATE story SET deleted = 0 WHERE id = %s AND user_id = %s", (id, user))     
            conn.commit()
            cursor.close()
            conn.close()       
            return {'status': 'success'}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return {'status': 'failure'}

@app.post("/delete-story/")
async def delete_story(id: str = Query(...), user: str = Query(...)):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM story WHERE id = %s AND user_id = %s AND deleted = 0", (id, user))
        story = cursor.fetchone()  
        if story:
            cursor.execute("UPDATE story SET deleted = 1 WHERE id = %s AND user_id = %s", (id, user))     
            conn.commit()
            cursor.close()
            conn.close()       
            return {'status': 'success'}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return {'status': 'failure'}

@app.post("/regenerate-chapter/")
async def regenerate_chapter(chapter: Chapter):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM story WHERE id = %s AND user_id = %s AND deleted = 2", (chapter.story_id, chapter.user))
        story = cursor.fetchone()  
        if story:
            story_data = {'id': story[0], 'title': story[1], 'genre': story[3], 'image_desc': story[4]}
            cursor.execute("SELECT * FROM chapter WHERE story_id = %s AND deleted = 0", (chapter.story_id,))
            chapters = cursor.fetchall()
            story_data['chapters'] = [{'id':chapter[0], 'title': chapter[2], 'text': chapter[3], 'alignment': chapter[4]} for chapter in chapters ]
            new_story_markdown = regenerate_chapter_for_story(story_data, chapter.chapter_id)
            new_story_parsed = parse_story(new_story_markdown)
            new_story_saved = update_story_to_db(new_story_parsed, chapter.story_id, chapter.chapter_id)
            cursor.close()
            conn.close()       
            return {'status': 'success', 'story': new_story_saved}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return {'status': 'failure'}