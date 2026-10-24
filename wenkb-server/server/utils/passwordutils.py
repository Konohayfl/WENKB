import base64
import hashlib
import hmac
import secrets

ALGORITHM = 'pbkdf2_sha256'
ITERATIONS = 310_000


def hash_password(password):
  salt = secrets.token_bytes(16)
  digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
  salt_text = base64.urlsafe_b64encode(salt).decode('ascii').rstrip('=')
  digest_text = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
  return f'{ALGORITHM}${ITERATIONS}${salt_text}${digest_text}'


def verify_password(password, encoded):
  try:
    algorithm, iterations, salt_text, digest_text = encoded.split('$', 3)
    if algorithm != ALGORITHM:
      return False
    if not 1 <= int(iterations) <= 2_000_000:
      return False
    salt = base64.urlsafe_b64decode(salt_text + '=' * (-len(salt_text) % 4))
    expected = base64.urlsafe_b64decode(digest_text + '=' * (-len(digest_text) % 4))
    actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(iterations))
    return hmac.compare_digest(actual, expected)
  except (AttributeError, TypeError, ValueError):
    return False
