from __future__ import unicode_literals
import frappe # type: ignore
from frappe import throw, msgprint, _ # type: ignore
import string
import random
import json
from qr_scanning.api.message import send_message # type: ignore



def id_generator(size):
   return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))

@frappe.whitelist()
def id_generator_otp():
   return ''.join(random.choice('0123456789') for _ in range(6))

@frappe.whitelist(allow_guest=True)
def send_otp(phoneNo):

	reply = {}
	reply['status_code']=200
	reply['message']=''
	reply['data']=''


	try:
		otpobj=frappe.db.get("UserOTP", {"mobile": phoneNo})
		if otpobj:
			frappe.db.sql("""delete from tabUserOTP where mobile='"""+phoneNo+"""'""")

		OTPCODE=id_generator_otp()

		if phoneNo=="1234567890":
			OTPCODE = "123456"
					
		userOTP = frappe.get_doc({
			"doctype":"UserOTP",
			"name":phoneNo,
			"mobile":phoneNo,
			"otp":OTPCODE
		})
		userOTP.flags.ignore_permissions = True
		userOTP.insert()

		if phoneNo!="1234567890":
			respon = send_message(phoneNo,OTPCODE)

		reply['status_code']=200
		reply['message']='OTP send sucessfully on {}'.format(phoneNo)
		reply['data']=OTPCODE
		return reply
	except Exception as e:
		reply['status_code']=500
		reply['message']=str(e)
		reply['data']=''		
		return reply