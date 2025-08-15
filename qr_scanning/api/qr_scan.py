from __future__ import unicode_literals
import frappe # type: ignore
from frappe import _ # type: ignore
from frappe.utils import nowtime # type: ignore

import traceback

@frappe.whitelist(allow_guest=True)
def qr_validation(**kwargs):

	reply = {}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}

	parameters=frappe._dict(kwargs)
	allKeys = parameters.keys()

	if 'qrcode' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Code not found."
		return reply

	if 'phoneNo' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Phone number not found."
		return reply

	qrcode = parameters['qrcode']
	phoneNo = parameters['phoneNo']

	try:
		query = "SELECT scan_user FROM `tabQR List` WHERE `qrcode`='{}'".format(qrcode)
		qr_list = frappe.db.sql(query,as_dict=1)
		if len(qr_list)==0:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="QR is not valid."
			return reply

		if qr_list[0]['scan_user'] not in [None,'None','','null','0',' ']:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="QR code is used."
			return reply

		if str(qr_list[0]['reward_amount']) in [None,'None','','null','0',' ']:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="QR code amount is not valid."
			return reply


		reply["status_code"]=200
		reply["message"]="QR code is valid."
		return reply

	except Exception as e:
		frappe.log_error(f"User sign up {phoneNo}",str(e))
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]=str(e)
		reply["message_trackeable"]=traceback.format_exc()
		return reply
	

@frappe.whitelist(allow_guest=True)
def qr_process(**kwargs):

	reply = {}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}

	parameters=frappe._dict(kwargs)
	allKeys = parameters.keys()

	if 'qrcode' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Code not found."
		return reply

	if 'phoneNo' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Phone number not found."
		return reply

	qrcode = parameters['qrcode']
	phoneNo = parameters['phoneNo']

	try:
		query = "SELECT scan_user,reward_type,reward_amount FROM `tabQR List` WHERE `qrcode`='{}'".format(qrcode)
		qr_list = frappe.db.sql(query,as_dict=1)

		# return str(qr_list[0]['scan_user'])
		if len(qr_list)==0:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="QR is not valid."
			return reply

		if str(qr_list[0]['scan_user']) not in [None,'None','','null','0',' ']:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="QR code is used."
			return reply

		if str(qr_list[0]['reward_amount']) in [None,'None','','null','0',' ']:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="QR code amount is not valid."
			return reply


		scan_lat = ''
		scan_long = ''
		scan_device = ''

		if 'scan_lat' in allKeys:
			scan_lat = parameters['scan_lat']

		if 'scan_long' in allKeys:
			scan_long = parameters['scan_long']

		if 'scan_device' in allKeys:
			scan_device = parameters['scan_device']	

		current_time = nowtime()

		query = "UPDATE `tabQR List` SET `scan_lat`='{}',`scan_long`='{}',`scan_device`='{}',`scan_user`='{}',`scan_date`=CURDATE(),`scan_time`='{}' WHERE `name`='{}'".format(str(scan_lat),str(scan_long),scan_device,phoneNo,current_time,qrcode)
		customer_update = frappe.db.sql(query,as_dict=1)

		frappe.enqueue(qr_wallet_entry,queue='default',job_name='Wallet entry',timeout=100000,user=phoneNo,amount=str(qr_list[0]['reward_amount']),qrcode=qrcode)
		frappe.local.response['http_status_code'] = 200
		reply["status_code"]=200
		reply["message"]=f"{qr_list[0]['reward_amount']} credited in your wallet."
		return reply

	except Exception as e:
		frappe.log_error(f"User sign up {phoneNo}",str(e))
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]=str(e)
		reply["message_trackeable"]=traceback.format_exc()
		return reply
	
@frappe.whitelist(allow_guest=True)
def qr_reset(**kwargs):
	query = "UPDATE `tabQR List` SET `scan_user`=''"
	customer_update = frappe.db.sql(query,as_dict=1)
	return "Reset all QR"


@frappe.whitelist(allow_guest=True)
def qr_wallet_entry(user,amount,qrcode):

	frappe.set_user("Administrator")
	doc = frappe.get_doc({
		"doctype": "QRWallet",
		"user": user,
		"status": "Unpaid",
		"amount": amount,
		"remain_amount": amount
	})
	doc.insert(ignore_permissions=True)

	query = "UPDATE `tabQR List` SET `wallet`='{}' WHERE `name`='{}'".format(str(doc.name),qrcode)
	customer_update = frappe.db.sql(query,as_dict=1)

	# frappe.db.commit()
	return doc.name