frappe.ui.form.on('Sales Invoice', {
	setup: function(frm,doc) {
		frm.set_query("customer", () => {
			return {
				"filters": {
					"is_parent_customer_cf": 0
				}
			}
		})
	}
})