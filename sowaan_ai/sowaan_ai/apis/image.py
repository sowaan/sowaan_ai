import frappe
import base64
import json
from frappe import _
import requests
from sowaan_ai.sowaan_ai.utils import analyze_image

@frappe.whitelist() 
def save_image(instance_name, ref_name, image=None):
    _settings = frappe.get_doc("Sowaan AI Setting", instance_name)
    try:
        image_doc = frappe.get_doc({
            "doctype": "Image",
            "instance_name": instance_name,
            "ref_name": ref_name
        })
        image_doc.insert(ignore_permissions=True)
        frappe.db.commit() 

        file_url = None
        if image:
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": f"image_{image_doc.name}.png",
                "content": base64.b64decode(image),
                "is_private": 1,
                "attached_to_doctype": "Image",
                "attached_to_name": image_doc.name  # Now the name exists
            })
            file_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            file_url = file_doc.file_url
            

            if (_settings.hugging_face_api_token
                and _settings.hugging_face_model):
                if file_url.startswith('/'):
                    file_url = file_url[1:]

                frappe.enqueue(process_screenshot, docname=image_doc.name, ss_path=file_url, instance_name=instance_name)


        return {"success": True, "message": "Image saved successfully!"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Image API Error")
        return {"success": False, "error": str(e)}


def process_screenshot(docname, ss_path, instance_name):
    response = analyze_image(ss_path, instance_name)
    try:
        productivity = json.loads(response)

        frappe.db.set_value('Image', docname, {
            'productivity_flag': productivity.get("status", ""),
            'productivity_reason': productivity.get("message", ""),
            'error_message': "",
            'ai_response': response
        })

        sent_status = send_data_to_api(docname, productivity.get("status", ""), productivity.get("message", ""), response, instance_name)


    except Exception as e:
        frappe.db.set_value('Image', docname, {
            'productivity_flag': "non-productive",
            'productivity_reason': "",
            'error_message': str(e),
            'ai_response': response
        })

        sent_status = send_data_to_api(docname, "non-productive", "", response, instance_name, error_message)

        # frappe.logger().error(f"Error processing screenshot: {error_message}")


    # Update sent_to_instance based on API response
    frappe.db.set_value('Image', docname, "sent_to_instance", sent_status)


def send_data_to_api(docname, productivity_flag, productivity_reason, ai_response, instance_name, error_message=""):
    """Send data to an external API"""
    try:
        # Get API settings
        _settings = frappe.get_doc("Sowaan AI Setting", instance_name)
        api_url = _settings.get("instance_url") 
        api_key = _settings.get("instance_api_key") 
        api_secret = _settings.get("instance_api_secret") 

        ref_name = frappe.db.get_value('Image', docname, 'ref_name')
        # Prepare payload for the external API
        payload = {
            "ref_name": ref_name,
            "productivity_flag": productivity_flag,
            "productivity_reason": productivity_reason,
            "ai_response": ai_response,
            "error_message": error_message
        }

        # Set headers (if authentication is required)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_key}:{api_secret}"
        }

        # Make the API request
        if api_url and api_key and api_secret:
            url = f"{api_url}/task_tracker.task_tracker.apis.timesheet.update_heartbeat"
            api_response = requests.post(api_url, json=payload, headers=headers)
            
            if api_response.status_code == 200:
                frappe.logger().info(f"API Success: {api_response.json()}")
                return True  # API call was successful
            
            frappe.logger().error(f"API Error: {api_response.status_code} - {api_response.text}")
            return False  # API call failed

    except Exception as api_error:
        frappe.logger().error(f"API Exception: {str(api_error)}")
        return False  # API call failed due to an exception

