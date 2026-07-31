"""Configuracion central del subsistema de licencias."""

APP_LICENSE_ID = "ANVIC-NETWORK-SENTINEL"
LICENSE_SCHEMA_VERSION = 1
LICENSE_REGISTRY_ROOT = r"Software\ANVIC\AnvicNetworkSentinel\Licensing"
LICENSE_TIME_SKEW_SECONDS = 60 * 60 * 12
LICENSE_SERIAL_PREFIX = "ANS1"

# Clave publica embebida en la aplicacion para validar licencias firmadas.
# La clave privada de emision NO forma parte del producto y debe permanecer
# fuera del build final.
LICENSE_PUBLIC_KEY_B64 = \
    "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUNvd0JRWURLMlZ3QXlFQWJIYlNyR1lIRXZzeDIyc2g5UzQvc0FCWlB2NkpzK0ZGVUFCUDY4em16cjQ9Ci0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQo="


LICENSE_TYPES = ("PERPETUAL", "ANNUAL", "TRIAL")
LICENSE_EDITIONS = ("STANDARD", "ADVANCED", "PRO")
