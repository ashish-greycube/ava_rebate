frappe.ui.form.on('Customer', {
	setup: function(frm,doc) {
		frm.set_query("parent_customer_cf", () => {
			return {
				"filters": {
					"is_parent_customer_cf": 1
				}
			}
		});		
	}
})