"""
pHash — Perceptual hashing for image comparison.
No ML, no GPU. Just DCT + average comparison.

Usage:
    hash1 = phash('image1.jpg')
    hash2 = phash('image2.jpg')
    similarity = hamming_distance(hash1, hash2)  # 0 = identical, > 20 = different
"""
import struct
from io import BytesIO
from math import log2
from urllib.request import Request, urlopen

try:
    from PIL import Image
except ImportError:
    Image = None


def _ensure_pil():
    if Image is None:
        raise ImportError("Pillow not installed. Run: pip install Pillow")


# Shared requests session for Rakumart-compatible image downloads
_IMAGE_SESSION = None

def _get_image_session():
    """Get or create a requests session with Rakumart cookies."""
    global _IMAGE_SESSION
    if _IMAGE_SESSION is None:
        import requests
        _IMAGE_SESSION = requests.Session()
        # Establish Rakumart session state first (unlocks alicdn images)
        try:
            _IMAGE_SESSION.get(
                'https://www.rakumart.com.br/',
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=15, verify=False
            )
        except Exception:
            pass  # Session may still work
    return _IMAGE_SESSION


def load_image(source) -> 'Image.Image':
    """Load image from path, URL, or bytes."""
    _ensure_pil()
    if isinstance(source, str) and source.startswith(('http://', 'https://')):
        try:
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            sess = _get_image_session()
            resp = sess.get(source, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.rakumart.com.br/',
                'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            }, timeout=30, verify=False)
            if resp.status_code == 200:
                return Image.open(BytesIO(resp.content)).convert('RGB')
        except ImportError:
            pass  # fall through to urllib
        # Fallback: use urllib (may not work for alicdn)
        req = Request(source, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as resp:
            return Image.open(BytesIO(resp.read())).convert('RGB')
    elif isinstance(source, bytes):
        return Image.open(BytesIO(source)).convert('RGB')
    else:
        return Image.open(source).convert('RGB')


def phash(image_source, hash_size=16):
    """
    Compute perceptual hash of an image.
    Returns a tuple of bits (0/1).
    hash_size=16 -> 256 bits. Standard.
    """
    img = load_image(image_source)
    
    # Resize to hash_size x hash_size
    img = img.resize((hash_size, hash_size), Image.LANCZOS)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Get pixels
    pixels = list(img.getdata())
    
    # Compute DCT (simplified: use pixel values directly)
    # For a real DCT, we'd need numpy. But for a quick hash,
    # comparing pixel values against the median works well enough.
    
    # Use median as threshold (more robust than mean for varied images)
    sorted_pixels = sorted(pixels)
    median = sorted_pixels[len(sorted_pixels) // 2]
    
    # Generate hash: 1 if pixel > median, else 0
    bits = tuple(1 if p > median else 0 for p in pixels)
    return bits


def phash_int(image_source, hash_size=16):
    """Compute phash as integer (bit-packed)."""
    bits = phash(image_source, hash_size)
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


def hamming_distance(hash1, hash2):
    """Number of differing bits. 0 = identical."""
    if len(hash1) != len(hash2):
        raise ValueError("Hash lengths differ")
    return sum(1 for a, b in zip(hash1, hash2) if a != b)


def similarity_percent(hash1, hash2):
    """0-100% similarity. 100% = identical."""
    total = len(hash1)
    diff = hamming_distance(hash1, hash2)
    return round((1 - diff / total) * 100, 1)


def phash_from_url(url, hash_size=16):
    """Compute phash from URL, returns integer + similarity helper."""
    h = phash_int(url, hash_size)
    return {
        'url': url,
        'hash': h,
        'hash_size': hash_size,
    }


def phash_regions(image_source, grid=(2, 2), hash_size=8):
    """Multi-region perceptual hash.
    Split image into grid (e.g. 2x2=4 regions), compute pHash for each.
    Returns list of int hashes, one per region.
    This captures layout/structure better than a single global hash."""
    _ensure_pil()
    img = load_image(image_source).convert('RGB')
    w, h = img.size
    cols, rows = grid
    region_w, region_h = w // cols, h // rows
    hashes = []
    for row in range(rows):
        for col in range(cols):
            region = img.crop((col * region_w, row * region_h,
                               (col + 1) * region_w, (row + 1) * region_h))
            # Compute phash on region
            region = region.resize((hash_size, hash_size), Image.LANCZOS).convert('L')
            pixels = list(region.getdata())
            sorted_px = sorted(pixels)
            median = sorted_px[len(sorted_px) // 2]
            bits = tuple(1 if p > median else 0 for p in pixels)
            result = 0
            for b in bits:
                result = (result << 1) | b
            hashes.append(result)
    return hashes


def phash_regions_similarity(hashes_a, hashes_b):
    """Compare two lists of region hashes. Returns 0-1 similarity.
    Each region compared by hamming distance, averaged."""
    if not hashes_a or not hashes_b:
        return 0.0
    n = min(len(hashes_a), len(hashes_b))
    total_sim = 0.0
    for i in range(n):
        a, b = hashes_a[i], hashes_b[i]
        xor = a ^ b
        dist = bin(xor).count('1')
        max_dist = 256  # hash_size * hash_size bits
        sim = 1 - (dist / max_dist)
        total_sim += sim
    return total_sim / n


def dhash(image_source, hash_size=16):
    """Difference hash — more discriminating than pHash for product images.
    Compares adjacent pixels (gradients) rather than median threshold.
    Returns a tuple of bits (0/1), size = hash_size * hash_size bits."""
    _ensure_pil()
    img = load_image(image_source)
    # Resize to hash_size+1 x hash_size (need +1 for differences)
    img = img.resize((hash_size + 1, hash_size), Image.LANCZOS).convert('L')
    pixels = list(img.getdata())
    # Compute horizontal gradients
    bits = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            bits.append(1 if left > right else 0)
    return tuple(bits)


def dhash_int(image_source, hash_size=16):
    """Compute dhash as integer (bit-packed)."""
    bits = dhash(image_source, hash_size)
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


# Quick test
if __name__ == '__main__':
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if url:
        result = phash_from_url(url)
        print(f"URL: {result['url'][:60]}")
        print(f"Hash: {result['hash']} ({result['hash_size']}x{result['hash_size']} bits)")
    else:
        print("Usage: python3 phash.py <image_url>")
        print("Testing with sample...")
        # Test with two different Rakumart images
        url1 = "https://cbu01.alicdn.com/img/ibank/O1CN01QLsDgN1xo17Biti7W_!!2216752846489-0-cib.jpg"
        h1 = phash_int(url1)
        print(f"Hash of test image: {h1}")
        print(f"Hash bits: {bin(h1)}")
