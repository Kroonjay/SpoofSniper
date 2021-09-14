import os
import base64
import hmac
import hashlib
from datetime import datetime
import requests
import logging
from .models import ErrorLog
from pprint import pformat



#Build the API signature
def build_signature(customer_id, shared_key, date, content_length, method, content_type, resource):
  x_headers = 'x-ms-date:' + date
  string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
  bytes_to_hash = str.encode(string_to_hash,'utf-8')  
  decoded_key = base64.b64decode(shared_key)
  encoded_hash = (base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest())).decode()
  authorization = "SharedKey {}:{}".format(customer_id,encoded_hash)
  return authorization


#Build and send a request to the Log Analytics Workspace via the API
def post_alert(body, log_type):
  customer_id = os.getenv("LOG_ANALYTICS_CUSTOMER_ID")
  workspace_shared_key = os.getenv("LOG_ANALYTICS_SHARED_KEY")
  method = 'POST'
  content_type = 'application/json'
  resource = '/api/logs'
  rfc1123date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
  if not body:
    return False
  content_length = len(body)
  signature = build_signature(customer_id, workspace_shared_key, rfc1123date, content_length, method, content_type, resource)
  uri = f'https://{customer_id}.ods.opinsights.azure.com{resource}?api-version=2016-04-01'

  headers = {
      'content-type': content_type,
      'Authorization': signature,
      'Log-Type': log_type,
      'x-ms-date': rfc1123date
  }
  
  response = requests.post(uri, data=body, headers=headers)
  if (response.status_code == 200):
      return True
  else:
      log_str = f"Couldn't Post Alert to Log Analytics Workspace.  Status: {response.status_code} \n Text:{response.text}"
      logging.error(log_str)
      return False

def report_error(result, module="AdminAudits", error_type=None, error_message=None, data=None):
    error_log = ErrorLog(module=module, result=result, errorType=error_type, errorMessage=error_message, data=data, createdAt = datetime.utcnow())
    logging.error(f"Maiasaura Error - Details: \n {pformat(error_log.dict(exclude={'createdAt'}))}")
    logging.info(error_log.json(exclude={'data'}))
    post_alert(error_log.json(exclude={'data'}), log_type="MaiasauraError")