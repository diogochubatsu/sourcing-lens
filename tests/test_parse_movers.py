#!/usr/bin/env python3
"""Test the Movers & Shakers parser with a synthetic HTML fixture."""

import sys
from pathlib import Path

# Add scripts dir to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from scrape_amazon_movers import parse_movers_page, _parse_bsr_change, parse_price_br


def test_bsr_change_parser():
    """Test the BSR change (% gain) extraction."""
    assert _parse_bsr_change("+123%") == 123
    assert _parse_bsr_change("123%") == 123
    assert _parse_bsr_change("-5%") == -5
    assert _parse_bsr_change("Subiu 456%") == 456
    assert _parse_bsr_change("Gain of 789%") == 789
    assert _parse_bsr_change("+1,234%") is None  # Too large for our 4-digit limit
    assert _parse_bsr_change("No percent here") is None
    assert _parse_bsr_change("") is None
    assert _parse_bsr_change(None) is None
    print("  ✓ bsr_change parser: all passed")


def test_price_parser():
    """Test Brazilian price parsing."""
    assert parse_price_br("R$ 1.234,56") is not None
    assert float(parse_price_br("R$ 1.234,56")) == 1234.56
    assert float(parse_price_br("R$ 99,90")) == 99.90
    assert float(parse_price_br("R$ 1.000")) == 1000.00
    assert parse_price_br("Grátis") is None
    assert parse_price_br("") is None
    print("  ✓ price parser: all passed")


def test_parse_synthetic_html():
    """
    Parse a minimal synthetic Movers & Shakers page.
    This tests the HTML parsing pathways without needing a live page.
    """
    html = """<!DOCTYPE html>
<html>
<head><title>Amazon.com.br Produtos em alta</title></head>
<body>
<div id="zg">
  <div id="zg-right-col">
    <div class="a-section a-spacing-none" data-asin="B0EXAMPLE001">
      <a href="/dp/B0EXAMPLE001">
        <h2>Produto Teste Um</h2>
      </a>
      <span class="p13n-sc-price">R$ 49,90</span>
      <img src="https://images-amazon.com/media/test1.jpg" />
      <i class="a-icon-alt">4,5 de 5 estrelas</i>
      <a class="a-size-small" href="/product-reviews/B0EXAMPLE001">1.234</a>
      <span class="a-color-success">+87%</span>
    </div>
    <div class="a-section a-spacing-none" data-asin="B0EXAMPLE002">
      <a href="/dp/B0EXAMPLE002">
        <span class="_cDEzb_p13n-sc-css-line-clamp-3_g3dy1">Segundo Produto</span>
      </a>
      <span class="_cDEzb_p13n-sc-price_3mJ9Z">R$ 129,90</span>
      <img src="https://images-amazon.com/media/test2.jpg" srcset="https://images-amazon.com/media/test2_large.jpg 2x" />
      <i class="a-icon-alt">3,8 de 5 estrelas</i>
      <a class="a-size-small" href="/product-reviews/B0EXAMPLE002">567</a>
      <span class="a-color-price">+42%</span>
      <span class="zg-bdg-text">#15</span>
    </div>
    <div class="a-section a-spacing-none" data-asin="B0EXAMPLE003">
      <a href="/dp/B0EXAMPLE003" title="Terceiro Produto de Teste">
        <span></span>
      </a>
      <img src="https://media-amazon.com/images/test3.jpg" />
      <!-- No price, no rating, no BSR change -->
    </div>
  </div>
</div>
</body>
</html>"""

    products = parse_movers_page(html, "amazon_br", "movers_and_shakers")
    
    # Check counts
    print(f"  Parsed {len(products)} products")
    assert len(products) == 3, f"Expected 3 products, got {len(products)}"

    # Product 1: full data
    p1 = [p for p in products if p["platform_id"] == "B0EXAMPLE001"][0]
    assert p1["title"] == "Produto Teste Um"
    assert float(p1["price"]) == 49.90
    assert p1["bsr_change"] == 87
    assert p1["review_avg"] == 4.5
    assert p1["review_count"] == 1234
    assert "images-amazon.com" in p1["image_url"]
    assert p1["category"] == "movers_and_shakers"
    assert p1["platform"] == "amazon_br"
    print(f"  ✓ Product 1 ({p1['platform_id']}): title={p1['title']}, "
          f"price={p1['price']}, bsr_change={p1['bsr_change']}%, "
          f"rating={p1['review_avg']}, reviews={p1['review_count']}")

    # Product 2: with BSR rank, srcset image
    p2 = [p for p in products if p["platform_id"] == "B0EXAMPLE002"][0]
    assert p2["bsr_change"] == 42
    assert p2["bsr_rank"] == 15
    assert "test2_large.jpg" in p2["image_url"]
    print(f"  ✓ Product 2 ({p2['platform_id']}): title={p2['title']}, "
          f"price={p2['price']}, bsr_change={p2['bsr_change']}%, "
          f"bsr_rank={p2['bsr_rank']}")

    # Product 3: minimal data, title from link
    p3 = [p for p in products if p["platform_id"] == "B0EXAMPLE003"][0]
    assert p3["title"] == "Terceiro Produto de Teste"  # from title attribute
    assert p3["price"] is None
    assert p3["bsr_change"] is None
    print(f"  ✓ Product 3 ({p3['platform_id']}): title={p3['title']}, "
          f"price={p3['price']}, bsr_change={p3['bsr_change']}")

    print("  ✓ All synthetic HTML tests passed!")


if __name__ == "__main__":
    print("Running Movers & Shakers parser tests...")
    test_bsr_change_parser()
    test_price_parser()
    test_parse_synthetic_html()
    print("\nAll tests passed!")
