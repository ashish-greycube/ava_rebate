# -*- coding: utf-8 -*-
# Copyright (c) 2020, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class CustomerRebate(Document):
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
				print(condition)
		cond_for_parent=cond
		if (customer):
			cond+=" and si.customer ='"+customer+"'"

		#normal_customer
		normal_customer_rebate_data = frappe.db.sql(""" select t.customer, t.total as sales_amount, ((t.total*rslab.rebate_percentage)/100)+t.fixed_rebate as rebate_amount
from
(   select si.customer,sum(si.base_net_total) as total, rg.name as rgroup,rg.fixed_rebate
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



		group_customer_rebate_data = frappe.db.sql(""" select t.customer,t.total as sales_amount,(t.total/t1.total)*t.fixed_rebate+t.slab_rebate as rebate_amount
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

