import frappe
from io import BytesIO
from PIL import Image
import pytesseract
import numpy as np
import cv2
import json
from transformers import pipeline
from huggingface_hub import InferenceClient
import datetime
import base64
from openai import OpenAI
from google import genai
from google.genai import types
from frappe.utils import get_datetime, now_datetime


def analyze_image(image_path, instance_name, job_description=None):
    file_path = frappe.get_site_path(image_path)
    ai_method = frappe.db.get_value("Sowaan AI Setting", instance_name, "ai_method")
    if ai_method == "Gemini":
        return classify_productivity_from_image(file_path, job_description, instance_name)
    else:
        return classify_productivity(extract_text_from_screenshot(file_path), job_description, instance_name)


def extract_text_from_screenshot(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Perform OCR
    text = pytesseract.image_to_string(gray)
    return text.strip()

def classify_productivity(text, job_description, instance_name):
    if not text:
        return "Uncertain (No Text Detected)"
    JD = ""
    if job_description:
        JD = f" with this Job Description: {job_description}"
    
    _settings = frappe.get_doc("Sowaan AI Setting", instance_name)
    
    if not _settings.ai_method:
        return "AI Method not set in Sowaan AI Setting"
    # Define the prompt for the classification task


    if _settings.length_of_extracted_data_for_ai and _settings.length_of_extracted_data_for_ai > 0:
        text = text[:_settings.length_of_extracted_data_for_ai]
    
    #default prompt
    prompt = f"This below text is extracted from user screen, is it office working or just chilling in office without working anything? , response should contain a plain text json object with 2 objects status (productive or non-productive) and message"
    
    if _settings.prompt:
        prompt = _settings.prompt
    
    messages = [
        {"role": "user", "content": f"{prompt}:\n\n{text}"}
    ]

    client = InferenceClient(api_key=_settings.hugging_face_api_token)
    model = ""

    if _settings.ai_method == "OpenAI":
        client = OpenAI(api_key=_settings.open_ai_api_key)
        model = _settings.open_ai_model

    elif _settings.ai_method == "DeepSeek":
        client = OpenAI(
            api_key=_settings.open_ai_api_key,
            base_url="https://api.deepseek.com"
            )
        model = _settings.open_ai_model

    elif _settings.ai_method == "Hugging Face":
        client = InferenceClient(api_key=_settings.hugging_face_api_token)
        model = _settings.hugging_face_model
 

    completion = client.chat.completions.create(
            model=model, 
            messages=messages,
            max_tokens=800
        )

    result = completion.choices[0].message.content

    return result.strip('```json').strip('```').strip()
    
def classify_productivity_from_image(image_path, job_description, instance_name):
    if not image_path:
        return "No Image Provided"
    JD = ""
    if job_description:
        JD = f" with this Job Description: {job_description}"
    
    _settings = frappe.get_doc("Sowaan AI Setting", instance_name)
    
    if not _settings.ai_method:
        return "AI Method not set in Sowaan AI Setting"
    # Define the prompt for the classification task

    if _settings.ai_method != "Gemini":
        return "Only Gemini is supported for image classification"

    #default prompt
    prompt = f"what user is doing in this image, output a json with status (productive/non-productive) and a message"
    
    if _settings.prompt:
        prompt = _settings.prompt
    
    output_length = 100
    if _settings.output_length:
        output_length = _settings.output_length

    client = genai.Client(
                api_key=_settings.gemini_api_key,
            )
    model = _settings.gemini_model

    base64_image = image_to_base64(image_path)    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="""image/png""",
                    data=base64.b64decode(base64_image),
                ),
            ],
        ),
        
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=output_length,
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text=prompt),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    return response.text

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


