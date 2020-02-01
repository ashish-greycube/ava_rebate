frappe.ui.form.on('Sales Invoice', {
	onload_post_render: function(frm) {
		frm.trigger('show_only_child_customers');
	},
	refresh: function(frm) {
		frm.trigger('show_only_child_customers');
	},
	show_only_child_customers: function(frm) {
		frm.set_query("customer", () => {
			return {
				"filters": {
					"is_parent_customer_cf": 0
				}
			}
		})
	},
})