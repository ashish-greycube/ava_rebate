frappe.ui.form.on('Sales Invoice', {
	customer: function (frm) {
		frm.set_query("customer_branch_cf", () => {
			return {
				"filters": {
					name: ['not in', undefined]
				}
			}
		})
		frm.set_value('customer_branch_cf', '')
		frm.set_df_property('customer_branch_cf', 'reqd', 0)
		frm.refresh_field('customer_branch_cf')
		frm.set_value('customer_group', '')
		frm.refresh_field('customer_group')
		frm.set_value('territory', '')
		frm.refresh_field('territory')
		frm.set_value('branch_industry_type_cf', '')
		frm.refresh_field('branch_industry_type_cf')

		frappe.db.get_value('Customer', frm.doc.customer, 'is_parent_customer_cf')
			.then(r => {
				if (!r.exc) {
					if (r.message.is_parent_customer_cf == 1) {
						frm.set_df_property('customer_branch_cf', 'reqd', 1)
						frappe.call({
							method: "ava_rebate.api.get_customer_branch_list",
							args: {
								customer_code: frm.doc.customer,
							},
							callback: function (r) {
								if (!r.exc) {
									let customer_branch_list = r.message
									if (customer_branch_list) {
										frm.set_query("customer_branch_cf", () => {
											return {
												"filters": {
													name: ['in', customer_branch_list]
												}
											}
										})
										frm.refresh_field('customer_branch_cf')
									} else {
										frappe.msgprint(__('No branch found for {0}', [frm.doc.customer]))
									}
								}
							}
						});
					} else {
						frm.set_value('customer_branch_cf', '')
						frm.set_df_property('customer_branch_cf', 'reqd', 0)
						frm.refresh_field('customer_branch_cf')
						frm.set_value('customer_group', '')
						frm.refresh_field('customer_group')
						frm.set_value('territory', '')
						frm.refresh_field('territory')
						frm.set_value('branch_industry_type_cf', '')
						frm.refresh_field('branch_industry_type_cf')
					}
				}
			});
	},
	customer_branch_cf: function (frm) {
		if (frm.doc.customer_branch_cf) {
			frappe.call({
				method: "ava_rebate.api.get_customer_branch_details",
				args: {
					customer_code: frm.doc.customer,
					customer_branch: frm.doc.customer_branch_cf
				},
				callback: function (r) {
					if (!r.exc) {
						let customer_branch_details = r.message
						if (customer_branch_details) {
							frm.set_value('customer_group', customer_branch_details[0])
							frm.refresh_field('customer_group')
							frm.set_value('territory', customer_branch_details[1])
							frm.refresh_field('territory')
							frm.set_value('branch_industry_type_cf', customer_branch_details[2])
							frm.refresh_field('branch_industry_type_cf')
						} else {
							frappe.msgprint(__('No branch detail found for {0}', [frm.doc.customer]))
						}
					}
				}
			});
		}
	},
})