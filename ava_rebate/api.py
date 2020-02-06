import frappe

@frappe.whitelist(allow_guest=True)
def get_customer_branch_list(customer_code):
	doc = frappe.get_doc('Customer',customer_code)
	customer_branch_list=[]
	for d in doc.get("customer_branch_detail_cf"):
		customer_branch_list.append(d.customer_branch)
	print('-------------------',customer_branch_list)
	return customer_branch_list


@frappe.whitelist(allow_guest=True)
def get_customer_branch_details(customer_code,customer_branch):	
	doc = frappe.get_doc('Customer',customer_code)
	customer_branch_list=[]
	for d in doc.get("customer_branch_detail_cf"):
		if (d.customer_branch==customer_branch):
			print('----------------------------------',d.customer_group,d.territory,d.industry_type)
			return d.customer_group,d.territory,d.industry_type
