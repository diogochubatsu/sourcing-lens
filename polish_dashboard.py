#!/usr/bin/env python3
"""Polish ArbitLens dashboard for v0.1 release."""
import re

with open('app/frontend/index.html') as f:
    html = f.read()

# ── 1. Clean bash warnings ──
html = re.sub(r'^/usr/bin/bash: warning.*\n?', '', html, flags=re.MULTILINE)

# ── 2. Update header with v0.1 release note ──
old_header = '''        <div class="header">
            <h1>arbt.ly</h1>
            <div class="subtitle">Market Intelligence Dashboard</div>
            <div class="meta">Brazil — Amazon BR + Mercado Livre</div>
        </div>'''
new_header = '''        <div class="header">
            <h1>arbt.ly</h1>
            <div class="subtitle">Market Intelligence Dashboard</div>
            <div class="meta">v0.1 — Core categories with verified data across Amazon BR, Amazon US & Mercado Livre</div>
        </div>'''
html = html.replace(old_header, new_header)

# ── 3. Replace tabs section with 4 core + More dropdown ──
old_tabs = '''        <div class="tabs">
            <button class="tab active" onclick="filterCategory('microfone', this)">🎤 Wireless Mics</button>
            <button class="tab" onclick="filterCategory('ring_light', this)">💡 Ring Lights</button>
            <button class="tab" onclick="filterCategory('headphone', this)">🎧 Headphones</button>
            <button class="tab" onclick="filterCategory('phone_holder', this)">📱 Phone Holders</button>
            <button class="tab" onclick="filterCategory('tripod', this)">📐 Tripods</button>
            <button class="tab" onclick="filterCategory('beach_towel_clip', this)">🏖️ Towel Clips</button>
            <button class="tab" onclick="filterCategory('led_panel', this)">💡 LED Panels</button>
            <button class="tab" onclick="filterPlatform('amazon_us', this)">🇺🇸 Amazon USA</button>
            <button class="tab" onclick="filterCategory('home_organization', this)">🏠 Home Org</button>
            <button class="tab" onclick="filterCategory('sports', this)">⚽ Sports</button><button class="tab" onclick="filterCategory('bluetooth_speaker', this)">🔊 Bluetooth Speakers</button>
                <button class="tab" onclick="filterCategory('smartwatch', this)">⌚ Smartwatches</button>
                
        </div>'''
new_tabs = '''        <div class="tabs">
            <button class="tab active" onclick="filterCategory('microfone', this)">🎤 Wireless Mics</button>
            <button class="tab" onclick="filterCategory('headphone', this)">🎧 Headphones</button>
            <button class="tab" onclick="filterCategory('led_panel', this)">💡 LED Panels</button>
            <button class="tab" onclick="filterCategory('tripod', this)">📐 Tripods</button>
            <div class="tab dropdown-parent" style="position:relative;">
                <button class="tab" style="border:1px solid #ddd;" onclick="toggleMoreDropdown(event)">📦 More ▾</button>
                <div id="more-dropdown" style="display:none;position:absolute;top:100%;left:0;background:#fff;border:1px solid #ddd;border-radius:12px;padding:8px;box-shadow:0 4px 16px rgba(0,0,0,0.12);z-index:100;min-width:200px;margin-top:4px;">
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('ring_light', this);closeMoreDropdown()">💡 Ring Lights</button>
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('phone_holder', this);closeMoreDropdown()">📱 Phone Holders</button>
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('beach_towel_clip', this);closeMoreDropdown()">🏖️ Towel Clips</button>
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('home_organization', this);closeMoreDropdown()">🏠 Home Org</button>
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('sports', this);closeMoreDropdown()">⚽ Sports</button>
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('bluetooth_speaker', this);closeMoreDropdown()">🔊 Bluetooth Speakers</button>
                    <button class="tab" style="display:block;width:100%;text-align:left;border:none;border-radius:8px;padding:8px 12px;margin:2px 0;" onclick="filterCategory('smartwatch', this);closeMoreDropdown()">⌚ Smartwatches</button>
                </div>
            </div>
        </div>'''
html = html.replace(old_tabs, new_tabs)

# ── 4. Update stats bar to show 4 core category counts ──
old_stats_render = '''            // Stats
            document.getElementById('stats-bar').innerHTML = 
                '<div class="stat"><div class="num" style="color:#22c55e">' + amazon.length + '</div><div class="label">Amazon BR</div></div>' +
                '<div class="stat"><div class="num" style="color:#fbbf24">' + ml.length + '</div><div class="label">Mercado Livre</div></div>' +
                '<div class="stat"><div class="num" style="color:#22c55e">' + (amazon[0] ? amazon[0].sales_30d + '+/mo' : '—') + '</div><div class="label">Top Amazon/mo</div></div>' +
                '<div class="stat"><div class="num" style="color:#fbbf24">' + (ml[0] && ml[0].sales_30d ? ml[0].sales_30d + '+' : '—') + '</div><div class="label">Top ML Total</div></div>';'''

new_stats_render = '''            // Stats — 4 core categories overview
            var coreCategories = ['microfone', 'headphone', 'led_panel', 'tripod'];
            var coreLabels = ['🎤 Mics', '🎧 Headphones', '💡 LED Panels', '📐 Tripods'];
            var coreStatsHtml = '';
            for (var ci = 0; ci < coreCategories.length; ci++) {
                var cat = coreCategories[ci];
                var catProds = window.allProducts ? window.allProducts.filter(function(p) { return p.category === cat; }) : [];
                var catTotal = catProds.length;
                coreStatsHtml += '<div class="stat"><div class="num" style="color:#1a1a1a">' + catTotal + '</div><div class="label">' + coreLabels[ci] + '</div></div>';
            }
            document.getElementById('stats-bar').innerHTML = coreStatsHtml;'''

html = html.replace(old_stats_render, new_stats_render)

# ── 5. Add dropdown toggle JS and close-on-click-outside ──
# Find the init() function and add the dropdown functions before it
old_init_start = '''        async function init() {'''
new_init_start = '''        // More dropdown toggle
        function toggleMoreDropdown(event) {
            event.stopPropagation();
            var dd = document.getElementById('more-dropdown');
            dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
        }
        function closeMoreDropdown() {
            document.getElementById('more-dropdown').style.display = 'none';
        }
        document.addEventListener('click', function(e) {
            var dd = document.getElementById('more-dropdown');
            if (dd && !e.target.closest('.dropdown-parent')) {
                dd.style.display = 'none';
            }
        });
        
        async function init() {'''
html = html.replace(old_init_start, new_init_start)

# ── 6. Update filterCategory to handle dropdown items ──
# The old filterCategory already works fine since dropdown items also call it.
# But we should ensure when a dropdown item is clicked, its tab gets highlighted.
# The current code does document.querySelectorAll('.tab').forEach... then tries to find the tab.
# For dropdown items which are div.tab elements, el.classList.add('active') works.
# But the existing non-dropdown tabs need to lose active. Let me also update filterCategory
# to not break on the dropdown tab.

# Update filterCategory to handle dropdown selection properly
old_filter = '''        function filterCategory(category, el) {
            document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
            if (el) el.classList.add('active');
            else document.querySelector('.tab[onclick*="' + category + '\"]').classList.add('active');
            window.currentCategory = category;
            renderCurrentCategory();
        }'''
new_filter = '''        function filterCategory(category, el) {
            // Deactivate all tabs and More dropdown items
            document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
            document.querySelectorAll('#more-dropdown .tab').forEach(function(t) { t.classList.remove('active'); });
            if (el) el.classList.add('active');
            window.currentCategory = category;
            renderCurrentCategory();
        }'''
html = html.replace(old_filter, new_filter)

# ── 7. Update default category in init ──
html = html.replace(
    "            window.currentCategory = 'microfone';",
    "            window.currentCategory = 'microfone';  // v0.1 default core category"
)

# ── 8. Update match summary categories count ──
# The renderMatches function counts categories from matches, that's fine as-is

# ── 9. Update the platform filter note ──
html = html.replace(
    "                document.getElementById('ml-table').innerHTML = '<tr><td colspan=\"7\" style=\"text-align:center; padding:20px; color:#888;\">Switch to a category tab to see Mercado Livre products</td></tr>';",
    "                document.getElementById('ml-table').innerHTML = '<tr><td colspan=\"7\" style=\"text-align:center; padding:20px; color:#888;\">Select a category tab to see Mercado Livre products</td></tr>';"
)

# ── Write back ──
with open('app/frontend/index.html', 'w') as f:
    f.write(html)

print("✅ Dashboard polished for v0.1")
