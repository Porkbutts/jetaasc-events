#!/usr/bin/env python3
"""
Analyze JET Program placement locations in Japan
Creates a bubble map showing where JETAASC subscribers were placed
"""

import csv
import re
from collections import Counter
import json
import argparse
import os

# Japanese prefecture coordinates (capital cities)
PREFECTURE_COORDS = {
    'Hokkaido': (43.0642, 141.3469, 'Hokkaido'),
    'Aomori': (40.8244, 140.7400, 'Aomori'),
    'Iwate': (39.7036, 141.1527, 'Iwate'),
    'Miyagi': (38.2688, 140.8721, 'Miyagi'),
    'Akita': (39.7186, 140.1024, 'Akita'),
    'Yamagata': (38.2404, 140.3633, 'Yamagata'),
    'Fukushima': (37.7500, 140.4678, 'Fukushima'),
    'Ibaraki': (36.3418, 140.4468, 'Ibaraki'),
    'Tochigi': (36.5658, 139.8836, 'Tochigi'),
    'Gunma': (36.3912, 139.0608, 'Gunma'),
    'Saitama': (35.8617, 139.6455, 'Saitama'),
    'Chiba': (35.6050, 140.1233, 'Chiba'),
    'Tokyo': (35.6762, 139.6503, 'Tokyo'),
    'Kanagawa': (35.4478, 139.6425, 'Kanagawa'),
    'Niigata': (37.9026, 139.0236, 'Niigata'),
    'Toyama': (36.6953, 137.2113, 'Toyama'),
    'Ishikawa': (36.5947, 136.6256, 'Ishikawa'),
    'Fukui': (36.0652, 136.2216, 'Fukui'),
    'Yamanashi': (35.6642, 138.5684, 'Yamanashi'),
    'Nagano': (36.6513, 138.1810, 'Nagano'),
    'Gifu': (35.3912, 136.7223, 'Gifu'),
    'Shizuoka': (34.9769, 138.3831, 'Shizuoka'),
    'Aichi': (35.1802, 136.9066, 'Aichi'),
    'Mie': (34.7303, 136.5086, 'Mie'),
    'Shiga': (35.0045, 135.8686, 'Shiga'),
    'Kyoto': (35.0116, 135.7681, 'Kyoto'),
    'Osaka': (34.6937, 135.5023, 'Osaka'),
    'Hyogo': (34.6913, 135.1830, 'Hyogo'),
    'Nara': (34.6851, 135.8329, 'Nara'),
    'Wakayama': (34.2260, 135.1675, 'Wakayama'),
    'Tottori': (35.5039, 134.2381, 'Tottori'),
    'Shimane': (35.4723, 133.0505, 'Shimane'),
    'Okayama': (34.6618, 133.9344, 'Okayama'),
    'Hiroshima': (34.3853, 132.4553, 'Hiroshima'),
    'Yamaguchi': (34.1859, 131.4714, 'Yamaguchi'),
    'Tokushima': (34.0658, 134.5593, 'Tokushima'),
    'Kagawa': (34.3401, 134.0434, 'Kagawa'),
    'Ehime': (33.8416, 132.7657, 'Ehime'),
    'Kochi': (33.5597, 133.5311, 'Kochi'),
    'Fukuoka': (33.5904, 130.4017, 'Fukuoka'),
    'Saga': (33.2494, 130.2988, 'Saga'),
    'Nagasaki': (32.7448, 129.8737, 'Nagasaki'),
    'Kumamoto': (32.7898, 130.7417, 'Kumamoto'),
    'Oita': (33.2382, 131.6126, 'Oita'),
    'Miyazaki': (31.9077, 131.4202, 'Miyazaki'),
    'Kagoshima': (31.5602, 130.5581, 'Kagoshima'),
    'Okinawa': (26.2124, 127.6809, 'Okinawa'),
}

# Alternate spellings/formats
PREFECTURE_ALIASES = {
    'Tokyo Metropolitan Government東京都': 'Tokyo',
    'Hyogo Pref.兵庫県': 'Hyogo',
    'Oita Pref.大分県': 'Oita',
    'Yamanashi Pref.山梨県': 'Yamanashi',
    'Osaka Pref.大阪府': 'Osaka',
    'Fukuoka Pref.福岡県': 'Fukuoka',
    'Nagano Pref.長野県': 'Nagano',
    'Aichi Pref.愛知県': 'Aichi',
    'Kyoto Pref.京都府': 'Kyoto',
    'Saitama Pref.埼玉県': 'Saitama',
    'Chiba Pref.千葉県': 'Chiba',
    'Kanagawa Pref.神奈川県': 'Kanagawa',
}

def normalize_prefecture(pref):
    """Normalize prefecture name"""
    if not pref or pref.strip() == '' or pref == 'N/A':
        return None

    pref = pref.strip().strip('"')

    # Check aliases first
    if pref in PREFECTURE_ALIASES:
        return PREFECTURE_ALIASES[pref]

    # Check if it's a known prefecture
    for known in PREFECTURE_COORDS.keys():
        if known.lower() in pref.lower() or pref.lower() in known.lower():
            return known

    return None

def main():
    parser = argparse.ArgumentParser(description='Generate JET placement heatmap')
    parser.add_argument('csv_path', help='Path to subscribed audience CSV file')
    parser.add_argument('-o', '--output', default='jet_placement_map.html', help='Output HTML file path')
    args = parser.parse_args()

    csv_path = args.csv_path
    output_path = args.output

    prefectures = Counter()
    locations = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        mapped = 0

        for row in reader:
            total += 1
            pref_raw = row.get('JET Prefecture', '')
            pref = normalize_prefecture(pref_raw)

            if pref and pref in PREFECTURE_COORDS:
                mapped += 1
                prefectures[pref] += 1

                lat, lng, name = PREFECTURE_COORDS[pref]
                key = (lat, lng)
                if key not in locations:
                    locations[key] = {'count': 0, 'name': name, 'lat': lat, 'lng': lng}
                locations[key]['count'] += 1

    # Print summary
    print(f"\n=== JET Placement Analysis ===")
    print(f"Total subscribers: {total}")
    print(f"With JET placement data: {mapped} ({mapped*100//total}%)")
    print(f"Prefectures represented: {len(prefectures)}")

    print(f"\n--- Top Prefectures ---")
    for pref, count in prefectures.most_common(20):
        print(f"  {pref}: {count}")

    # Generate HTML
    generate_html(prefectures, locations, total, mapped, output_path)
    print(f"\n✓ Generated: {output_path}")

def generate_html(prefectures, locations, total, mapped, output_path):
    """Generate interactive HTML with Leaflet bubble map of Japan"""

    loc_data = [
        {'lat': v['lat'], 'lng': v['lng'], 'count': v['count'], 'name': v['name']}
        for v in locations.values()
    ]

    pref_data = list(prefectures.most_common(15))

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JETAASC - JET Placement Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
        }}
        .header {{
            padding: 1.5rem 2rem;
            text-align: center;
        }}
        h1 {{ color: #fff; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #888; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            padding: 1rem 2rem;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: #16213e;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            text-align: center;
            min-width: 120px;
        }}
        .stat-number {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #e63946;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        #map {{
            height: 550px;
            width: 100%;
            border-top: 1px solid #333;
            border-bottom: 1px solid #333;
        }}
        .chart-section {{
            padding: 2rem;
            max-width: 800px;
            margin: 0 auto;
        }}
        .chart-container {{
            background: #16213e;
            padding: 1.5rem;
            border-radius: 12px;
        }}
        .chart-container h2 {{
            margin-bottom: 1rem;
            font-size: 1.1rem;
            color: #e63946;
        }}
        .legend {{
            padding: 1rem 2rem;
            text-align: center;
            color: #888;
            font-size: 0.9rem;
        }}
        .legend-item {{
            display: inline-flex;
            align-items: center;
            margin: 0 1rem;
        }}
        .legend-circle {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🇯🇵 JET Placement Map</h1>
        <p class="subtitle">Where {mapped} JETAASC subscribers were placed in Japan</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{total:,}</div>
            <div class="stat-label">Total Subscribers</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{mapped:,}</div>
            <div class="stat-label">With Placement Data</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{len(prefectures)}</div>
            <div class="stat-label">Prefectures</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{prefectures.most_common(1)[0][0]}</div>
            <div class="stat-label">Top Prefecture</div>
        </div>
    </div>

    <div class="legend">
        <span class="legend-item"><span class="legend-circle" style="background:#00b4d8"></span> 1-15</span>
        <span class="legend-item"><span class="legend-circle" style="background:#8ac926"></span> 16-25</span>
        <span class="legend-item"><span class="legend-circle" style="background:#ffbe0b"></span> 26-35</span>
        <span class="legend-item"><span class="legend-circle" style="background:#ff6b35"></span> 36-50</span>
        <span class="legend-item"><span class="legend-circle" style="background:#e63946"></span> 50+</span>
    </div>

    <div id="map"></div>

    <div class="chart-section">
        <div class="chart-container">
            <h2>Top Prefectures</h2>
            <canvas id="prefChart"></canvas>
        </div>
    </div>

    <script>
        // Initialize map centered on Japan
        const map = L.map('map').setView([36.5, 138.0], 5);

        // Dark map tiles
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }}).addTo(map);

        // Location data
        const locations = {json.dumps(loc_data)};

        // Color scale based on count
        function getColor(count) {{
            if (count >= 50) return '#e63946';
            if (count >= 36) return '#ff6b35';
            if (count >= 26) return '#ffbe0b';
            if (count >= 16) return '#8ac926';
            return '#00b4d8';
        }}

        // Add circles for each location
        locations.forEach(loc => {{
            const radius = Math.sqrt(loc.count) * 8000;
            const color = getColor(loc.count);
            L.circle([loc.lat, loc.lng], {{
                color: color,
                fillColor: color,
                fillOpacity: 0.5,
                weight: 2,
                radius: Math.max(radius, 15000)
            }}).addTo(map)
              .bindPopup(`<strong>${{loc.name}}</strong><br>${{loc.count}} JET${{loc.count > 1 ? 's' : ''}} placed here`);
        }});

        // Bar chart
        const prefLabels = {json.dumps([p[0] for p in pref_data])};
        const prefValues = {json.dumps([p[1] for p in pref_data])};

        const colors = [
            '#e63946', '#f15a24', '#ff6b35', '#ff8c42', '#ffbe0b',
            '#d4d700', '#8ac926', '#52b788', '#40916c', '#2d6a4f',
            '#1b4332', '#00b4d8', '#0096c7', '#0077b6', '#023e8a'
        ];

        new Chart(document.getElementById('prefChart'), {{
            type: 'bar',
            data: {{
                labels: prefLabels,
                datasets: [{{
                    data: prefValues,
                    backgroundColor: colors,
                    borderRadius: 6,
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{
                        grid: {{ color: '#333' }},
                        ticks: {{ color: '#888' }}
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#eee' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    with open(output_path, 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
