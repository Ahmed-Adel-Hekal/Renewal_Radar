from src.normalization import normalize_brand_name


def test_normalize_legal_suffix_and_case():
    assert normalize_brand_name("Acme Inc.") == "acme"


def test_normalize_spacing_and_casing():
    assert normalize_brand_name(" GLOW SKIN ") == "glowskin"


def test_normalize_ampersand():
    assert normalize_brand_name("River & Reed") == "riverandreed"


def test_normalize_blue_bottle_spacing():
    assert normalize_brand_name("Blue Bottle LLC") == "bluebottle"
    assert normalize_brand_name("BlueBottle") == "bluebottle"
