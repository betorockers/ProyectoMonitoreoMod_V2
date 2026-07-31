import base64
import json
import re
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

priv = Ed25519PrivateKey.generate()
pub = priv.public_key()
pub_b64 = base64.b64encode(pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)).decode('ascii')

pem_private = priv.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
with open('private_key.pem', 'wb') as f:
    f.write(pem_private)

with open('config/licensing.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'LICENSE_PUBLIC_KEY_B64\s*=\s*\\?\n?\s*\"[^\"]+\"', 'LICENSE_PUBLIC_KEY_B64 = \\\n    \"' + pub_b64 + '\"', content)

with open('config/licensing.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('---NEW VALID SERIALS FOR THE NEW PUBLIC KEY---')
def enc(d): return base64.urlsafe_b64encode(d).decode('ascii').rstrip('=')

for i in range(1, 4):
    p = json.dumps({'schema_version':1, 'app_id':'ANVIC-NETWORK-SENTINEL', 'edition':'PRO', 'license_type':'PERPETUAL', 'license_id':'DEV-PRO-PERP-000' + str(i), 'customer_name':'Developer', 'is_perpetual':True, 'expires_at':None, 'features':[]}, sort_keys=True, separators=(',', ':')).encode('utf-8')
    sig = priv.sign(p)
    print('ANS1.' + enc(p) + '.' + enc(sig) + '\n')
