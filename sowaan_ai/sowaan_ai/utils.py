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
from openai import OpenAI
from frappe.utils import get_datetime, now_datetime


def analyze_image(image_path, instance_name, job_description=None):
    return classify_productivity(extract_text_from_screenshot(image_path), job_description, instance_name)


def extract_text_from_screenshot(image_path):
    file_path = frappe.get_site_path(image_path)
    img = cv2.imread(file_path)
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




