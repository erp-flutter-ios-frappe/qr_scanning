from __future__ import unicode_literals
import frappe # type: ignore
from frappe import _ # type: ignore
from datetime import datetime,timedelta

import traceback

@frappe.whitelist(allow_guest=True)
def qr_wallet_balance(**kwargs):

	reply = {}
	reply['status_code']=200
	reply['message']=''
	reply['balance']=0
	reply['total_paid']=0
	reply['total_unpaid']=0

	parameters=frappe._dict(kwargs)
	allKeys = parameters.keys()

	if 'phoneNo' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Phone number not found."
		return reply

	phoneNo = parameters['phoneNo']

	try:
		query_balance = "SELECT SUM(remain_amount) AS balance FROM `tabQRWallet` WHERE `user`='{}' AND `status`!='Paid'".format(phoneNo)
		balance_list = frappe.db.sql(query_balance,as_dict=1)
		if len(balance_list)!=0:
			if balance_list[0]['balance'] not in [None,'None','',' ','0']:
				reply['balance']=float(balance_list[0]['balance'])

		query_total_unpaid = "SELECT SUM(remain_amount) AS total_unpaid FROM `tabQRWallet` WHERE `user`='{}' AND `status`!='Paid'".format(phoneNo)
		total_unpaid_list = frappe.db.sql(query_total_unpaid,as_dict=1)
		if len(total_unpaid_list)!=0:
			if total_unpaid_list[0]['total_unpaid'] not in [None,'None','',' ','0']:
				reply['total_unpaid']=float(total_unpaid_list[0]['total_unpaid'])

		query_total_paid = "SELECT SUM(paid_amount) AS total_paid FROM `tabQRWallet` WHERE `user`='{}' AND `status`!='Unpaid'".format(phoneNo)
		total_paid_list = frappe.db.sql(query_total_paid,as_dict=1)
		if len(total_paid_list)!=0:
			if total_paid_list[0]['total_paid'] not in [None,'None','',' ','0']:
				reply['total_paid']=float(total_paid_list[0]['total_paid'])


		reply["status_code"]=200
		reply["message"]="Balance fetch."
		return reply

	except Exception as e:
		frappe.log_error(f"Balance fetch {phoneNo}",str(e))
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]=str(e)
		reply["message_trackeable"]=traceback.format_exc()
		return reply
	

@frappe.whitelist(allow_guest=True)
def qr_wallet_transaction(**kwargs):

# start_date = "2025-08-01"
# end_date   = "2025-08-15"

	reply = {}
	reply['status_code']=200
	reply['message']=''
	reply['data']=[]

	parameters=frappe._dict(kwargs)
	allKeys = parameters.keys()

	if 'phoneNo' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Phone number not found."
		return reply
	
	if 'start_date' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Start date not found."
		return reply
	
	if 'end_date' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="End date not found."
		return reply	

	phoneNo = parameters['phoneNo']
	start_date = parameters['start_date']
	end_date = parameters['end_date']

	try:

		e_date = datetime.strptime(end_date, "%Y-%m-%d")
		s_date = datetime.strptime(start_date, "%Y-%m-%d")

		if e_date < s_date:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="End date cannot be earlier than start date."
			return reply

		days_diff = (e_date - s_date).days
		if days_diff > 90:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="Date range cannot be more than 90 days."
			return reply

		e_date_new = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
		s_date_new = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)

		query = "SELECT name, amount, paid_amount, remain_amount, status, creation FROM `tabQRWallet` WHERE `user`='{}' AND (`creation` BETWEEN '{}' AND '{}') ORDER BY `creation` DESC".format(phoneNo,str(s_date_new), str(e_date_new))
		frappe.log_error(query,f"Transaction query {phoneNo}")
		transactions = frappe.db.sql(query, as_dict=True)

		reply['data']=transactions
		reply["status_code"]=200
		reply["message"]="Transactions fetch."
		return reply

	except Exception as e:
		frappe.log_error(f"Transaction fetch {phoneNo}",str(e))
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]=str(e)
		reply["message_trackeable"]=traceback.format_exc()
		return reply	