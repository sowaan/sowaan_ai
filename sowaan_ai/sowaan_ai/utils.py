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
    
    hf_api_token = _settings.hugging_face_api_token 
    client = InferenceClient(api_key=hf_api_token)

    # Define the prompt for the classification task
    messages = [
        {"role": "user", "content": f"analyze this as productive or non-productive (productive means office working and non-productive means using social media, watching videos and playing games) in office work environment{JD}, response should contain a json object with 2 objects status and message:\n\n{text}"}
    ]

    completion = client.chat.completions.create(
        model=_settings.hugging_face_model, 
        messages=messages,
        max_tokens=500
    )
    
    return completion.choices[0].message.content




