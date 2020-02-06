frappe.ui.form.on('Sales Invoice', {
	onload_post_render: function(frm) {
		// frm.trigger('show_only_child_customers');
	},
	refresh: function(frm) {
		// frm.trigger('show_only_child_customers');
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
	customer: function(frm) {
		frappe.call({
			method: "ava_rebate.api.get_customer_branch_list",
			args: {
				customer_code: frm.doc.customer,
			},
			callback: function (r) {
				if (!r.exc) {
					let customer_branch_list = r.message
					if (customer_branch_list) {
						console.log(customer_branch_list)
						frm.set_df_property('customer_branch_cf', 'options',customer_branch_list)
						frm.set_df_property('customer_branch_cf', 'reqd', 1)
						frm.refresh_field('customer_branch_cf')
					} else {
						frappe.msgprint(__('No branch found for {0}', [frm.doc.customer]))
						frm.set_df_property('customer_branch_cf', 'reqd', 0)
					}
				}
			}
		});
	},
	customer_branch_cf: function(frm) {
		console.log(frm.doc.customer,frm.doc.customer_branch_cf)
		frappe.call({
			method: "ava_rebate.api.get_customer_branch_details",
			args: {
				customer_code: frm.doc.customer,
				customer_branch:frm.doc.customer_branch_cf
			},
			callback: function (r) {
				if (!r.exc) {
					let customer_branch_details = r.message
					if (customer_branch_details) {
						console.log(customer_branch_details)
						frm.set_value('customer_group', customer_branch_details[0])
						frm.set_value('territory', customer_branch_details[1])
						frm.set_value('branch_industry_type_cf', customer_branch_details[2])
					} else {
						frappe.msgprint(__('No branch detail found for {0}', [frm.doc.customer]))
					}
				}
			}
		});
	},
})