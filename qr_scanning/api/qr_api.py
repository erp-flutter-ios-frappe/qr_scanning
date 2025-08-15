from __future__ import unicode_literals
import frappe # type: ignore
from frappe import throw, msgprint, _ # type: ignore
import string
import random
import json
import traceback
from frappe.utils.password import update_password as _update_password # type: ignore
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
	

@frappe.whitelist(allow_guest=True)
def sign_up(**kwargs):

	reply = {}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}

	parameters=frappe._dict(kwargs)
	allKeys = parameters.keys()

	if 'phoneNo' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="Phone number not found."
		return reply

	if 'otp' not in allKeys:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]="OTP not found."
		return reply


	phoneNo = parameters['phoneNo']
	otp = parameters['otp']	

	name_pass = True
	firstName = ''
	if 'firstName' in allKeys:
		firstName = parameters['firstName']
	else:
		name_pass = False

	lastName = ''
	if 'lastName' in allKeys:
		lastName = parameters['lastName']
	else:
		name_pass = False

	# city = parameters['city']
	# pincode = parameters['pinCode']
	customerName=phoneNo
	if name_pass:
		customerName = "{} {}".format(firstName,lastName)

	reply= {}
	reply['message']=""
	reply['status_code']=200

	try:
		# otpobj=frappe.db.get("UserOTP", {"mobile": phoneNo})
		# user = frappe.db.get("Customer", {"name": phoneNo})

		query = "SELECT name FROM `tabUserOTP` WHERE `mobile`='{}' AND `otp`='{}'".format(phoneNo,otp)
		otp_list = frappe.db.sql(query,as_dict=1)
		if len(otp_list)==0:
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]=500
			reply["message"]="Invalid OTP."
			return reply

		query = "SELECT name,customer_name,gender,customer_type,image,disabled,mobile_no,email_id FROM `tabCustomer` WHERE `name`='{}'".format(phoneNo)
		customer_list = frappe.db.sql(query,as_dict=1)

		if len(customer_list)!=0:
			if customer_list[0]['disabled'] in [1,True]:
				frappe.local.response['http_status_code'] = 500
				reply["status_code"]=500
				reply["message"]="Your account is not active."
				return reply

			#update customer
			query = "UPDATE `tabCustomer` SET `customer_name`='{}' WHERE `name`='{}'".format(customerName,phoneNo)
			customer_update = frappe.db.sql(query,as_dict=1)

			# frappe.db.sql("""UPDATE `tabCustomer` SET `customer_name`='"""+customerName+"""' WHERE `name`='"""+phoneNo+"""'""")
			reply['data'] = customer_list[0]
			reply["message"]="Welcome back"
		else:
			# frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+customerName+"""', 'India','Individual', 'Individual')""")
			customer = frappe.get_doc({
					"doctype": "Customer",
					"name":phoneNo,
					"customer_name": phoneNo,
					"customer_type": "Individual",  # Could be "Company" or "Individual"
					"customer_group": "Commercial", # Must exist in your system
					"territory": "All Territories", # Must exist in your system
				})

			# Insert into DB
			customer.insert(ignore_permissions=True)
			# Commit changes
			frappe.db.commit()

			query = "SELECT name,customer_name,gender,customer_type,image,disabled,mobile_no,email_id FROM `tabCustomer` WHERE `name`='{}'".format(phoneNo)
			customer_list = frappe.db.sql(query,as_dict=1)
			if len(customer_list)!=0:
				reply['data'] = customer_list[0]

			d = frappe.get_doc({
				"doctype": "DefaultValue",
				"parent": "" + phoneNo,
				"parenttype": "User Permission",
				"parentfield": "system_defaults",
				"defkey": "Customer",
				"defvalue": "" + phoneNo
			})
			d.insert(ignore_permissions=True)
			
			p = frappe.get_doc({"docstatus":0,"doctype":"User Permission","name":"New User Permission 1","__islocal":1,"__unsaved":1,"owner":"Administrator","apply_for_all_roles":0,"__run_link_triggers":0,"user":"" + phoneNo,"allow":"Customer","for_value":"" + phoneNo})
			p.insert(ignore_permissions=True)
			reply["message"]="Customer created"
			reply["status_code"]=200
		
		frappe.local.response['http_status_code'] = 200
		return reply
	except Exception as e:
		frappe.log_error(f"User sign up {phoneNo}",str(e))
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]=500
		reply["message"]=str(e)
		reply["message_trackeable"]=traceback.format_exc()
		return reply