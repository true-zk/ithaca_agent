import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.tools.webtools import fetch_pictures_from_web


def test_fetch_product_picture():
    """Test fetch product picture tool"""
    print("=" * 60)
    print("Testing fetch product picture tool")
    print("=" * 60)
    res = fetch_pictures_from_web.invoke({"url": "https://www.taptap.cn/"})
    print(res)


if __name__ == "__main__":
    test_fetch_product_picture()