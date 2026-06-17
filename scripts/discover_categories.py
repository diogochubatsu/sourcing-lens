#!/usr/bin/env python3
"""Category Discovery — Auto-discover category mappings from product URLs.

Usage:
    python3 scripts/discover_categories.py --url https://www.amazon.com.br/dp/B093LHRL42
    python3 scripts/discover_categories.py --asin B093LHRL42 --platform amazon_br
"""
import sys
import os
import re
import argparse
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute_returning
from scripts.category_mapper import add_mapping

# Load env
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip()

AMAZON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9',
}


def discover_from_amazon(url):
    """Discover category from Amazon product page."""
    try:
        resp = requests.get(url, headers=AMAZON_HEADERS, timeout=30)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Get title
        title_el = soup.select_one('#productTitle, #title span')
        title = title_el.get_text(strip=True) if title_el else ''
        
        # Get category from breadcrumb
        breadcrumb = soup.select('#wayfinding-breadcrumbs_container a, .a-breadcrumb li a')
        categories = [a.get_text(strip=True) for a in breadcrumb]
        
        # Get image
        img_el = soup.select_one('#landingImage, #imgBlkFront')
        img_url = img_el.get('data-old-hires') or img_el.get('src', '') if img_el else ''
        
        # Get best sellers URL from category
        bestsellers_link = soup.select_one('a[href*="bestsellers"]')
        bestsellers_url = bestsellers_link.get('href', '') if bestsellers_link else ''
        
        # Extract node ID from bestsellers URL
        node_match = re.search(r'/(\d+)', bestsellers_url)
        node_id = node_match.group(1) if node_match else ''
        
        return {
            'title': title,
            'categories': categories,
            'image_url': img_url,
            'bestsellers_url': f'https://www.amazon.com.br{bestsellers_url}' if bestsellers_url.startswith('/') else bestsellers_url,
            'node_id': node_id,
        }
    except Exception as e:
        print(f"Error: {e}")
        return None


def discover_from_ml(url):
    """Discover category from ML product page."""
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Get title
        title_el = soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        
        # Get category from breadcrumb
        breadcrumb = soup.select('.andes-breadcrumb a, [class*="breadcrumb"] a')
        categories = [a.get_text(strip=True) for a in breadcrumb]
        
        # Get image
        img_el = soup.select_one('img[data-src], img[src*="mlstatic"]')
        img_url = img_el.get('data-src') or img_el.get('src', '') if img_el else ''
        
        return {
            'title': title,
            'categories': categories,
            'image_url': img_url,
        }
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Category Discovery')
    parser.add_argument('--url', type=str, help='Product URL to discover from')
    parser.add_argument('--asin', type=str, help='Amazon ASIN')
    parser.add_argument('--platform', choices=['amazon_br', 'amazon_us', 'ml'])
    args = parser.parse_args()
    
    if args.url:
        if 'amazon' in args.url:
            platform = 'amazon_br' if '.com.br' in args.url else 'amazon_us'
            result = discover_from_amazon(args.url)
        elif 'mercadolivre' in args.url:
            platform = 'ml'
            result = discover_from_ml(args.url)
        else:
            print("Unsupported URL")
            return
    elif args.asin and args.platform:
        platform = args.platform
        if platform == 'amazon_br':
            url = f'https://www.amazon.com.br/dp/{args.asin}'
        elif platform == 'amazon_us':
            url = f'https://www.amazon.com/dp/{args.asin}'
        else:
            print("ASIN only works for Amazon")
            return
        result = discover_from_amazon(url)
    else:
        parser.print_help()
        return
    
    if not result:
        print("Could not discover product info")
        return
    
    print(f"\nDiscovered from {platform}:")
    print(f"  Title: {result['title']}")
    print(f"  Categories: {' > '.join(result['categories'])}")
    print(f"  Image: {result.get('image_url', '-')[:80]}")
    
    if result.get('bestsellers_url'):
        print(f"  Best Sellers URL: {result['bestsellers_url']}")
    
    # Suggest internal category based on keywords
    title_lower = result['title'].lower()
    suggestions = []
    
    if any(w in title_lower for w in ['microfone', 'lapela', 'mic']):
        suggestions.append(('Audio', 'Microphones', 'Lapela'))
    if any(w in title_lower for w in ['fone', 'headphone', 'earbuds']):
        suggestions.append(('Audio', 'Headphones', 'Geral'))
    if any(w in title_lower for w in ['speaker', 'caixa', 'som']):
        suggestions.append(('Audio', 'Speakers', 'Geral'))
    if any(w in title_lower for w in ['tripod', 'tripé']):
        suggestions.append(('Photography', 'Tripods', 'Geral'))
    if any(w in title_lower for w in ['led', 'light', 'anel', 'ring']):
        suggestions.append(('Lighting', 'Ring Lights', 'Geral'))
    if any(w in title_lower for w in ['watch', 'smartwatch', 'relógio']):
        suggestions.append(('Tech', 'Wearables', 'Smartwatch'))
    
    if suggestions:
        print(f"\nSuggested internal categories:")
        for l1, l2, l3 in suggestions:
            print(f"  {l1}/{l2}/{l3}")
            
            # Ask to add mapping
            add = input(f"  Add mapping for {platform}? [y/N] ").strip().lower()
            if add == 'y':
                node_id = result.get('node_id', '')
                bestsellers_url = result.get('bestsellers_url', '')
                cat_name = ' > '.join(result['categories']) if result['categories'] else ''
                
                mapping_id = add_mapping(
                    our_l1=l1,
                    our_l2=l2,
                    our_l3=l3,
                    platform=platform,
                    platform_id=node_id,
                    platform_name=cat_name,
                    bestsellers_url=bestsellers_url,
                    confidence=0.7
                )
                if mapping_id:
                    print(f"  Added mapping id={mapping_id}")


if __name__ == '__main__':
    main()
