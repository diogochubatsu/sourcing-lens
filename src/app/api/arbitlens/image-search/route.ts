import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function POST(request: NextRequest) {
  const startTime = Date.now();

  try {
    const contentType = request.headers.get('content-type') || '';

    let imagePathOrUrl: string;

    if (contentType.includes('multipart/form-data')) {
      const formData = await request.formData();
      const imageFile = formData.get('image') as File;
      if (!imageFile) {
        return NextResponse.json({ error: 'No image file provided' }, { status: 400 });
      }

      const bytes = await imageFile.arrayBuffer();
      const buffer = Buffer.from(bytes);
      const tempDir = os.tmpdir();
      const ext = imageFile.name.split('.').pop() || 'jpg';
      const tempFile = path.join(tempDir, `arbitlens_img_${Date.now()}.${ext}`);
      fs.writeFileSync(tempFile, buffer);
      imagePathOrUrl = tempFile;
    } else {
      const body = await request.json();
      imagePathOrUrl = body.image_url;
      if (!imagePathOrUrl) {
        return NextResponse.json({ error: 'Missing image_url in JSON body' }, { status: 400 });
      }
    }

    const script = path.join(SCRIPT_DIR, 'match_pg.py');
    const args = ['-u', script, '--limit', '20'];

    if (imagePathOrUrl.startsWith('http')) {
      args.push('--image-url', imagePathOrUrl);
    } else {
      args.push('--embed-image', imagePathOrUrl);
    }

    const output = execFileSync('python3', args, {
      cwd: process.cwd(),
      timeout: 60000,
      encoding: 'utf-8',
      maxBuffer: 5 * 1024 * 1024,
      env: { ...process.env },
    });

    const matches = JSON.parse(output);

    // Clean up temp file
    if (!imagePathOrUrl.startsWith('http')) {
      try { fs.unlinkSync(imagePathOrUrl); } catch {}
    }

    // Transform to ImageSearchResponse format
    const products = (Array.isArray(matches) ? matches : []).map((m: any) => ({
      platform: m.platform || '',
      product_name: m.title || '',
      price_low: m.price || null,
      price_high: null,
      price_currency: 'BRL',
      price_brl: m.price || null,
      image_url: m.image_url || '',
      product_url: m.product_url || '',
      seller_name: '',
      seller_rating: null,
      monthly_sales: null,
      moq: null,
      review_count: null,
      rating: null,
      match_score: m.similarity || m.score || 0,
      category: m.category || '',
    }));

    return NextResponse.json({
      query_image: imagePathOrUrl.startsWith('http') ? imagePathOrUrl : 'uploaded',
      products,
      total_products: products.length,
      search_type: 'clip_visual',
      search_time_ms: Date.now() - startTime,
    });
  } catch (error: any) {
    console.error('Image search error:', error.message);

    // Clean up temp file on error
    try {
      if (error.stdout) {
        // Try to extract temp file from args
      }
    } catch {}

    if (error.killed) {
      return NextResponse.json({ error: 'Image search timed out' }, { status: 408 });
    }

    return NextResponse.json({
      error: error.message || 'Image search failed',
      query_image: '',
      products: [],
      total_products: 0,
      search_type: 'clip_visual',
      search_time_ms: Date.now() - startTime,
    }, { status: 500 });
  }
}
