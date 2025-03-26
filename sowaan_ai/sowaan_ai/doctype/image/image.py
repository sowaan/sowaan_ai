# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from sowaan_ai.sowaan_ai.utils import extract_text_from_screenshot, analyze_image
from sowaan_ai.sowaan_ai.apis.image import process_screenshot


class Image(Document):
	pass

@frappe.whitelist()
def read_text(docname):
	# Fetch the attached files linked to this Image document
	files = frappe.get_all("File", filters={"attached_to_doctype": "Image", "attached_to_name": docname}, fields=["file_url"])
	
	if files:
		# Assuming the first file in the list is the image we want to process
		image_url = files[0].file_url
		if image_url.startswith('/'):
			image_url = image_url[1:]
		
		extracted_text = extract_text_from_screenshot(image_url)

		return extracted_text
	else:
		return None

@frappe.whitelist()
def analyze(docname, instance_name):

	# Fetch the attached files linked to this Image document
	files = frappe.get_all("File", filters={"attached_to_doctype": "Image", "attached_to_name": docname}, fields=["file_url"])
	
	if files:
		# Assuming the first file in the list is the image we want to process
		image_url = files[0].file_url
		if image_url.startswith('/'):
			image_url = image_url[1:]
		
		frappe.enqueue(process_screenshot, docname=docname, ss_path=image_url, instance_name=instance_name)

@frappe.whitelist()
def bulk_analyze(docnames):
	docnames = json.loads(docnames)
	for docname in docnames:
		# Fetch the attached files linked to this Image document
		files = frappe.get_all("File", filters={"attached_to_doctype": "Image", "attached_to_name": docname}, fields=["file_url"])
		
		if files:
			instance_name = frappe.db.get_value("Image", docname, "instance_name")
			# Assuming the first file in the list is the image we want to process
			image_url = files[0].file_url
			if image_url.startswith('/'):
				image_url = image_url[1:]
			
			frappe.enqueue(process_screenshot, docname=docname, ss_path=image_url, instance_name=instance_name)
