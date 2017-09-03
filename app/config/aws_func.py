import base64
import hmac
from hashlib import sha1
import json
from datetime import datetime, timedelta

from config import config


# TODO: figure out how to proper convert datetime to whatever the below is.
expires = str(datetime.now() + timedelta(days=1))[:10] + 'T00:00:00Z'

# aws policy template
policy = {
    "expiration": expires,
    "conditions": [
        {"bucket": config.aws_bucket},
        ["starts-with", "$key", ""],
        {"acl": "public-read"},
        {"success_action_redirect": "http://localhost:5000/"},
        ["starts-with", "$Content-Type", "application/octet-stream"],
        ["content-length-range", 0, 10485760]
    ]
}

# policy encoded to base64
policy_encoded = base64.b64encode(json.dumps(policy).encode('utf-8'))

utf8 = 'utf-8'
aws_secret_key = config.aws_secret_key

def create_signature(aws_secret_key, policy_encoded):
    new_hmac = hmac.new(bytes(aws_secret_key, utf8), digestmod=sha1)
    new_hmac.update(bytes(policy_encoded, utf8))
    signature_base64 = base64.b64encode(new_hmac.digest())
    signature = str(signature_base64, utf8).strip()

    return [policy_encoded, signature]


signature = create_signature(aws_secret_key, policy_encoded.decode())
