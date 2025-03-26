// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt


frappe.ui.form.on('Image', {
    refresh: function(frm) {
        frm.add_custom_button(__('Read Text'), function() {
            frappe.call({
                method: 'sowaan_ai.sowaan_ai.doctype.image.image.read_text',
                args: {
                    docname: frm.doc.name  // Pass the current document name
                },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('text', response.message);
                        
                        // Save the document with the extracted text
                        frm.save();
                    } else {
                        frappe.msgprint(__('No text could be extracted.'));
                    }
                }
            });
        });

        frm.add_custom_button(__('Analyze'), function() {
            frappe.call({
                method: 'sowaan_ai.sowaan_ai.doctype.image.image.analyze',
                args: {
                    docname: frm.doc.name,
                    instance_name: frm.doc.instance_name
                },
                callback: function(response) {
                    frappe.msgprint(__('Job enqueued. Please check back in a few minutes.'));
                }
            });
        });

    }
});

