frappe.listview_settings["Image"] = {
	onload: function (listview) {
		listview.page.add_action_item(__("Analyze"), () => {
			const selected_docs = listview.get_checked_items().map((image) => image.name);
			frappe.call({
				method: 'sowaan_ai.sowaan_ai.doctype.image.image.bulk_analyze',
                args: {
                    docnames: selected_docs
                },
                freeze: true,
                callback: function(response) {
                    frappe.msgprint(__('Jobs enqueued for selected documents. Please check back in a few minutes.'));
                }
			});
		});
	},
};