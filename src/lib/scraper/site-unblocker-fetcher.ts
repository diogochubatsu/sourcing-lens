/**
 * SiteUnblockerFetcher — fetch 1688 product detail via Decodo Site Unblocker API
 * Uses curl to retrieve pages, then parses embedded window.context JSON.
 * Falls back to Puppeteer + residential proxy if needed.
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const SU_USER = process.env.DECODO_SITEUNBLOCKER_USER || 'U0000398789';
const SU_PASS = process.env.DECODO_SITEUNBLOCKER_PASS;
const SU_HOST = process.env.DECODO_SITEUNBLOCKER_HOST || 'unblock.decodo.com';
const SU_PORT = process.env.DECODO_SITEUNBLOCKER_PORT || '60000';

/**
 * Fetch raw HTML from 1688 via Site Unblocker
 */
function fetchHtml(offerId, opts = {}) {
  const { retry = 3, timeout = 30 } = opts;
  const url = `https://detail.1688.com/offer/${offerId}.html`;
  const curlCmd = [
    'curl', '-s', '-k', '-L', `--max-time=${timeout}`,
    `--proxy`, `http://${SU_USER}:${SU_PASS}@${SU_HOST}:${SU_PORT}`,
    '-H', 'X-SU-Geo: China',
    '-H', 'X-SU-Locale: zh-cn',
    url
  ].join(' ');

  return new Promise((resolve, reject) => {
    exec(curlCmd, { maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      if (err) return reject(err);
      if (!stdout || stdout.length < 1000) {
        return reject(new Error('Empty or too small response'));
      }
      resolve(stdout);
    });
  });
}

/**
 * Parse embedded window.context JSON from HTML
 * Returns structured object with product data
 */
function parseContextFromHtml(html) {
  // Find the big <script> that defines window.context = (function...)(window.contextPath, {...});
  const scriptMatch = html.match(/window\.contextPath\s*=\s*"\/default";\s*<script[^>]*>([\s\S]*?)<\/script>/);
  if (!scriptMatch) throw new Error('window.context script not found');

  const scriptContent = scriptMatch[1];
  // The JSON is the second argument to the IIFE: (window.contextPath, { ... })
  // Find matching braces after the comma
  const startIdx = scriptContent.indexOf('window.contextPath,{');
  if (startIdx === -1) {
    // Try alternative pattern
    const alt = scriptContent.match(/window\.context=\(function[^)]+\)\s*\(\s*window\.contextPath\s*,\s*(\{.*?\})\s*\);/s);
    if (alt) return JSON.parse(cleanJson(alt[1]));
    throw new Error('Cannot locate JSON blob');
  }
  const jsonStart = scriptContent.indexOf('{', startIdx);
  if (jsonStart === -1) throw new Error('No JSON object found');

  // Count braces to find end
  let depth = 0;
  let endIdx = -1;
  for (let i = jsonStart; i < scriptContent.length; i++) {
    if (scriptContent[i] === '{') depth++;
    else if (scriptContent[i] === '}') {
      depth--;
      if (depth === 0) { endIdx = i + 1; break; }
    }
  }
  if (endIdx === -1) throw new Error('Unclosed JSON object');

  const jsonStr = scriptContent.slice(jsonStart, endIdx);
  const cleaned = cleanJson(jsonStr);
  return JSON.parse(cleaned);
}

/**
 * Clean JavaScript-style JSON: remove trailing commas, comments
 */
function cleanJson(str) {
  return str
    .replace(/,\s*}/g, '}')   // trailing commas before }
    .replace(/,\s*]/g, ']')   // trailing commas before ]
    .replace(/\/\*[\s\S]*?\*\//g, '')  // block comments
    .replace(/\/\/.*$/gm, '');          // line comments
}

/**
 * Extract fields needed for factory_products update
 */
async function scrapeOffer(offerId) {
  const html = await fetchHtml(offerId);
  const ctx = parseContextFromHtml(html);
  const data = ctx.result?.data || {};

  const update = {};

  // 1) main_spec: attribute table — check for "attributes" or direct props
  // In many pages, attributes are in a separate container; we'll collect name/value pairs from skuInfoMap entries
  // which encode variant attributes; but product-level attributes may be in a different field.
  // We'll extract from "attributes" if exists; otherwise fallback to empty.
  if (data.attributes && Array.isArray(data.attributes)) {
    update.main_spec = JSON.stringify(data.attributes);
  } else if (data.props && Array.isArray(data.props)) {
    update.main_spec = JSON.stringify(data.props);
  } else {
    // Try to find any "attr" or "spec" named field with array of {name,value}
    const attrField = Object.entries(data).find(([k, v]) => Array.isArray(v) && v.length && typeof v[0] === 'object' && 'name' in v[0]);
    if (attrField) {
      update.main_spec = JSON.stringify(attrField[1]);
    } else {
      update.main_spec = null;
    }
  }

  // 2) specifications: detailed property table (often same as attributes; keep null until differentiated)
  update.specifications = null;

  // 3) models: SKU list with name, price, stock
  const skuInfoMap = data.skuInfoMap || {};
  const models = Object.entries(skuInfoMap).map(([specAttrs, info]) => ({
    name: specAttrs,
    price: info.price || null,
    stock: info.canBookCount || info.saleCount || null,
    skuId: info.skuId
  }));
  update.models = JSON.stringify(models);

  // 4) variant_prices: map spec props to price
  const variantMap = {};
  models.forEach(m => {
    if (m.price) variantMap[m.name] = m.price;
  });
  update.variant_prices = JSON.stringify(variantMap);

  // 5) video_url
  const video = data.video;
  if (video && video.videoId && video.videoId !== 0) {
    // construct video URL pattern if available
    update.video_url = `https://video.1688.com/${video.videoId}.mp4`;
  } else {
    update.video_url = null;
  }

  // Also capture all images for v1.5 enrichment
  // (images are stored separately, but we could add a field if needed)

  return { success: true, update };
}

module.exports = { scrapeOffer, fetchHtml, parseContextFromHtml };
