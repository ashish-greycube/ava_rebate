// Copyright (c) 2020, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Rebate', {
	onload: function (frm) {
		frm.set_value("from_date", frappe.datetime.month_start());
		frm.set_query('customer', () => {
			return {
				filters: {
					"is_parent_customer_cf":0
				}
			}
		})		
	},
	get_sales_invoices: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'fill_customer_rebate_details',
			callback: function(r) {
				if(r.message=='true')
				console.log(r)
				frm.refresh();
			}
		})
	},
	customer_group: function (frm) {
		frm.set_query('customer', () => {
			return {
				filters: {
					"customer_group": frm.doc.customer_group,
					"is_parent_customer_cf":0
				}
			}
		})
		frm.refresh_field("customer")
	}
});
