// Copyright (c) 2020, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Rebate', {
	onload: function (frm) {
		frm.get_field("customer_rebate_detail").grid.cannot_add_rows = true;
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
	create_journal_entry: function (frm) {
		if (frm.doc.customer_rebate_detail.length == 0) {
			frappe.throw(__('Customer rebate details cann\'t be empty' ))
		}		
		if (frm.doc.default_receivable_account==undefined) {
			frappe.throw(__('Default Receivable Account cann\'t be empty' ))
		}		
		if (frm.doc.expense_account==undefined) {
			frappe.throw(__('Expense Account cann\'t be empty' ))
		}	
		return frappe.call({
			doc: frm.doc,
			method: 'process_sales_invoice_and_create_journal_entry',
			callback: function(r) {
				setTimeout(function() { 
					let si='';
					frappe.msgprint(__('Journal Entry {0} is submitted.',['<a href="#Form/Journal%20Entry/'+r.message[0]+'">' + r.message[0]+ '</a>']));
					frappe.msgprint(__('{0} invoices are updated as paid.',[r.message[1]]));
				}, 100);
				console.log(r)
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
frappe.ui.form.on('Customer Rebate Detail CT', {
	before_customer_rebate_detail_remove: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		let total_amount=frm.doc.total_amount-row.sales_amount
		let total_discount=frm.doc.total_discount-row.rebate_amount
		frm.set_value('total_amount', total_amount)
		frm.set_value('total_discount', total_discount)
	}
})
