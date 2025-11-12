import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.oauth.auth import OAuthManager

def test_meta_oauth():
    auth = OAuthManager()
    auth.authenticate()


if __name__ == "__main__":
    test_meta_oauth()


"""
http://localhost:8080/callback#access_token=EAAEM5p9aBgABPZBg8fjEZA0GIt4vCZAmPh5UoJ6UdiyV0kxmfVXKlXx10TW0yE8pkJ8pE7jPZCdlxl66DoV0ahBozvr2eSGbkZCBkJtmtDQRRqkzAiYPZCK6QDTbSLWlPGeXlXbLsZBTeas4XuSVIAosSk7gtKoqT4y8d3XtX6RF6tY0P92pJTCc6LZATbbxMmyB0j8hubkWsbZAgHJ5kdV3lT6nXtYjJ0r84BnfDE5R40nbJ49sstaAfXpCFZB4bjJqXn8Ga5Iuq9DuiSzJMIHPDMX4i3o7gndnHZBj60ZD&data_access_expiration_time=1770722952&expires_in=5448
"""