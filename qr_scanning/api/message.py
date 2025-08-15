from __future__ import unicode_literals
import frappe # type: ignore
from frappe import _ # type: ignore
import re
import json
from frappe.core.doctype.sms_settings.sms_settings import send_sms # type: ignore
import requests # type: ignore
import re
# from urlparse import urlparse

@frappe.whitelist(allow_guest=True)
def send_message(phone,message):

    try:
        send_sms_msg91([phone],message)
    except Exception as e:
        return e

@frappe.whitelist(allow_guest=True)
def send_sms_msg91(receiver_list,OTP):

    for item in receiver_list:
        url = "https://control.msg91.com/api/v5/flow"
        payload = {"template_id":"675ab7acd6fc05752b651c02","short_url":"0"}
        headers = {'content-type': "application/json","accept":"application/json","authkey":"424660AsEdRRWusbhi667545aaP1"}


        payload = json.dumps({
        "template_id": "675ab7acd6fc05752b651c02",
        "short_url": "0",
        "recipients": [
            {
            "mobiles": "91{}".format(item),
            "var1": OTP
            }
        ]
        })
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text