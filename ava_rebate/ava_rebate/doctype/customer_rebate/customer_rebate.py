# -*- coding: utf-8 -*-
# Copyright (c) 2020, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.email import sendmail_to_system_managers
from frappe.utils import today
from erpnext.accounts.utils import get_balance_on, get_account_currency

class CustomerRebate(Document):

	def make_gl_entries_for_rebate(self,si_list):

		default_currency=frappe.get_value('Company', self.company, 'default_currency')
		cost_center= self.cost_center or frappe.get_cached_value('Company',  self.company,  "cost_center")
		jv_main={
		"company":self.company,
		"voucher_type":"Journal Entry",
		"is_opening":"No",
		"remark":" Customer rebate paid against period {from_date} to {to_date}.".format(from_date=self.from_date,to_date=self.to_date) + "\n List of updated sales invoices are:\n"+si_list,
		"title":"Customer Rebate from {from_date} to {to_date}".format(from_date=self.from_date,to_date=self.to_date),
		"total_debit":self.total_discount,
		"total_credit":self.total_discount,
		"posting_date":today(),
		"account_currency":default_currency,
		}

		credit_account=self.default_receivable_account or frappe.get_cached_value('Company',  self.company,  "default_receivable_account")
		debit_account=self.expense_account
		try:
			je = frappe.new_doc("Journal Entry")
			je.update(jv_main)
			for row in self.customer_rebate_detail:
				credit_party_balance=get_balance_on(party=row.customer, party_type="Customer")
				credit_account_balance=get_balance_on(account=credit_account,cost_center=cost_center)
				jv_credit_row={
						"account": credit_account,
						 "account_type":'Receivable',
						"account_balance" : credit_account_balance,
						"is_advance":"No",
						"party_type":"Customer",
						"party":row.customer,
						"against_account":self.expense_account,
						"credit": row.rebate_amount,
						"credit_in_account_currency":row.rebate_amount,
						"party_balance":credit_party_balance,				
					}
				debit_account_balance=get_balance_on(account=debit_account, cost_center=self.cost_center)
				jv_debit_row={
						"account": debit_account,
                        "account_type":'Expense Account',
                        "account_balance" : debit_account_balance,						
						"is_advance":"No",
                        "party":"",
                        "party_type":"",						
						"debit": row.rebate_amount,
						"debit_in_account_currency":row.rebate_amount,
						"cost_center": cost_center,
					}	
				je.append("accounts",jv_credit_row)
				je.append("accounts",jv_debit_row)
			je.save()
			je.submit()
			frappe.db.commit()
			return je.name
		except:
			frappe.db.rollback()
			title = _("Error while processing customer rebate for {0}").format(self.name)
			traceback = frappe.get_traceback()
			frappe.log_error(message=traceback , title=title)
			sendmail_to_system_managers(title, traceback)
			return False

	def process_sales_invoice_and_create_journal_entry(self):

		from_date=self.from_date
		to_date=self.to_date
		company=self.company
		customer=self.customer
		impacted_sales_invoice_data={}
		cond = "and 1=1"

		if (from_date and to_date):
			cond+=" and si.posting_date between '"+ from_date + "' and '"+to_date+"'"
		if (company):
			cond+=" and si.company ='"+company+"'"
		customer_name_list = ["%s"%(frappe.db.escape(d.customer)) for d in self.customer_rebate_detail]
		if customer_name_list:
			customer_name_condition = ",".join(['%s'] * len(customer_name_list))%(tuple(customer_name_list))
			cond+="{0} in ({1})".format('and si.customer', customer_name_condition)			
		impacted_sales_invoice_data = frappe.db.sql("""select DISTINCT si.name
			from `tabSales Invoice` si
			INNER JOIN `tabCustomer` cust ON si.customer=cust.name
			where 
			si.is_rebate_processed_cf=0
			and si.docstatus=1
			and si.status='Paid'
			and cust.is_parent_customer_cf!=1
	{cond}""".format(cond=cond), as_dict=1)

		si_list=''
		for si in impacted_sales_invoice_data:
			si_list+=si.name+' '

		gl_status=self.make_gl_entries_for_rebate(si_list=si_list)
	
		if gl_status!=False:
			for si in impacted_sales_invoice_data:
				frappe.db.set_value('Sales Invoice', si.name, 'is_rebate_processed_cf', 1)
			return gl_status,si_list
		else :
			frappe.throw(_("JV creation has failed. Please check error log. Sales invoice are not updated."))


	def fill_customer_rebate_details(self):
		self.set('customer_rebate_detail', [])
		total_amount=0
		total_discount=0
		from_date=self.from_date
		to_date=self.to_date
		company=self.company
		customer=self.customer
		customer_group=self.customer_group

		normal_customer_rebate_data={}
		group_customer_rebate_data={}

		cond = "and 1=1"
		if (from_date and to_date):
			cond+=" and si.posting_date between '"+ from_date + "' and '"+to_date+"'"
		if (company):
			cond+=" and si.company ='"+company+"'"
		if (customer_group):
			lft, rgt = frappe.db.get_value("Customer Group", customer_group, ['lft', 'rgt'])
			get_parent_customer_groups=frappe.db.sql("""select name from `tabCustomer Group` where lft >= %s and rgt <= %s""", (lft, rgt), as_dict=1)
			customer_groups = ["%s"%(frappe.db.escape(d.name)) for d in get_parent_customer_groups]
			if customer_groups:
				customer_group_condition = ",".join(['%s'] * len(customer_groups))%(tuple(customer_groups))
				condition="{0} in ({1})".format('and si.customer_group', customer_group_condition)
				cond+=condition
		cond_for_parent=cond
		if (customer):
			cond+=" and si.customer ='"+customer+"'"

		#normal_customer
		normal_customer_rebate_data = frappe.db.sql(""" select t.customer,t.customer_name,t.total as sales_amount, ((t.total*rslab.rebate_percentage)/100)+t.fixed_rebate as rebate_amount
from
(   select si.customer,cust.customer_name,sum(si.base_net_total) as total, rg.name as rgroup,rg.fixed_rebate
    from `tabSales Invoice` si
    INNER JOIN `tabCustomer` cust ON si.customer=cust.name
    INNER JOIN `tabRebate Group CT` rg  ON cust.rebate_group_cf=rg.name
    where 
    si.is_rebate_processed_cf=0
    and si.docstatus=1
    and si.status='Paid'
    and cust.parent_customer_cf is null
    and cust.rebate_group_cf is not null
    and cust.is_parent_customer_cf!=1
    {cond}
   group by si.customer
) t
INNER JOIN `tabRebate Slab CT` rslab 
on t.rgroup=rslab.parent
and t.total BETWEEN rslab.from_amount AND rslab.to_amount 
   """.format(cond=cond), as_dict=1)



		group_customer_rebate_data = frappe.db.sql(""" 
		select t.customer,t.customer_name,
		t.total as sales_amount,
		(t.total/t1.total)*t.fixed_rebate+t.slab_rebate as rebate_amount
		from 
		(
			select si.customer,cust.customer_name, sum(si.base_net_total) as total,
			cust_parent.name as parent_customer,rg.fixed_rebate,
			rslab.rebate_percentage as rebate_percentage,
			(total *rebate_percentage)/100 as slab_rebate
			from `tabSales Invoice` si
			INNER JOIN `tabCustomer` cust ON si.customer=cust.name
			INNER JOIN `tabCustomer` cust_parent ON cust_parent.name = cust.parent_customer_cf
			INNER JOIN `tabRebate Group CT` rg  ON cust_parent.rebate_group_cf=rg.name
			INNER JOIN `tabRebate Slab CT` rslab ON rg.name=rslab.parent
			where 
			si.is_rebate_processed_cf=0
			and si.docstatus=1
			and si.status='Paid'
			and cust.parent_customer_cf is not null
			and cust.rebate_group_cf is null
			and cust.is_parent_customer_cf!=1
			and total BETWEEN rslab.from_amount AND rslab.to_amount 
			{cond} group by si.customer,cust_parent.name
		) t
		inner join 
		(
			select sum(si.base_net_total) as total,
			cust_parent.name as parent_customer
			from `tabSales Invoice` si
			INNER JOIN `tabCustomer` cust ON si.customer=cust.name
			INNER JOIN `tabCustomer` cust_parent ON cust_parent.name = cust.parent_customer_cf
			INNER JOIN `tabRebate Group CT` rg  ON cust_parent.rebate_group_cf=rg.name
			INNER JOIN `tabRebate Slab CT` rslab ON rg.name=rslab.parent
			where 
			si.is_rebate_processed_cf=0
			and si.docstatus=1
			and si.status='Paid'
			and cust.parent_customer_cf is not null
			and cust.rebate_group_cf is null
			and cust.is_parent_customer_cf!=1
			and total BETWEEN rslab.from_amount AND rslab.to_amount 
			{cond_for_parent}
			group by cust_parent.name
		) t1 on t1.parent_customer = t.parent_customer
		""".format(cond=cond,cond_for_parent=cond_for_parent), as_dict=1)



		if not normal_customer_rebate_data and not group_customer_rebate_data:
			frappe.throw(_("No customers found for the mentioned criteria"))

		for customer in normal_customer_rebate_data:
			total_amount+=customer.sales_amount
			total_discount+=customer.rebate_amount

			self.append('customer_rebate_detail', customer)

		for customer in group_customer_rebate_data:
			total_amount+=customer.sales_amount
			total_discount+=customer.rebate_amount
			self.append('customer_rebate_detail', customer)
		self.total_amount=total_amount
		self.total_discount=total_discount
		return True

