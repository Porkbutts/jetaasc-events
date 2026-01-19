# JETAASC Audience Analytics Scripts

Scripts for generating interactive heatmaps from Mailchimp audience exports.

## Scripts

### `generate_residence_heatmap.py`

Generates an interactive map showing where subscribers currently live, based on the Address field in the CSV. Parses zip codes to map subscribers to specific neighborhoods/cities across the US.

**Features:**
- Neighborhood-level granularity for LA, San Diego, Orange County, and Arizona
- Color-coded bubbles by subscriber density
- Interactive Leaflet map with dark theme
- Bar chart of top states

### `generate_jet_placement_heatmap.py`

Generates an interactive map of Japan showing where subscribers were placed during their JET Program tenure, based on the "JET Prefecture" field.

**Features:**
- All 47 Japanese prefectures supported
- Color-coded bubbles by placement count
- Interactive Leaflet map centered on Japan
- Bar chart of top prefectures

## Usage

Both scripts require a path to the Mailchimp subscribed audience CSV export.

```bash
# Generate residence heatmap
python3 generate_residence_heatmap.py <csv_path> [-o output.html]

# Generate JET placement heatmap
python3 generate_jet_placement_heatmap.py <csv_path> [-o output.html]
```

### Examples

```bash
# Using default output filenames
python3 generate_residence_heatmap.py ~/Downloads/subscribed_email_audience_export.csv
python3 generate_jet_placement_heatmap.py ~/Downloads/subscribed_email_audience_export.csv

# Custom output paths
python3 generate_residence_heatmap.py ~/Downloads/subscribed_email_audience_export.csv -o ~/Desktop/residence_map.html
python3 generate_jet_placement_heatmap.py ~/Downloads/subscribed_email_audience_export.csv -o ~/Desktop/japan_map.html
```

## Expected CSV Format

The scripts expect a Mailchimp audience export CSV with these columns:

| Column | Used By | Description |
|--------|---------|-------------|
| `Address` | residence heatmap | Full mailing address with city, state, zip |
| `JET Prefecture` | placement heatmap | Japanese prefecture name (e.g., "Hyogo", "Tokyo") |

## Hosting with Vercel

### First-time setup

1. Install Vercel CLI (if needed):
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

### Deploy a map

1. Create a directory for your deployment:
   ```bash
   mkdir ~/my-map && cd ~/my-map
   ```

2. Copy the HTML file as `index.html`:
   ```bash
   cp /path/to/output.html index.html
   ```

3. Deploy:
   ```bash
   vercel --yes
   ```

4. Vercel will output a URL like `https://my-map-abc123.vercel.app`

### Update an existing deployment

```bash
cd ~/my-map
cp /path/to/updated_output.html index.html
vercel --prod
```

### Delete a deployment

```bash
vercel rm <project-name>
```

Or delete from the Vercel dashboard at https://vercel.com

## Privacy Notes

The generated HTML files contain **no PII**. They only include:
- Aggregated subscriber counts per location
- Geographic coordinates (lat/lng)
- Area/neighborhood names

No email addresses, names, or street addresses are included in the output.

## Dependencies

- Python 3.6+
- No external Python packages required (uses only stdlib)

The generated HTML files load these libraries from CDN:
- [Leaflet](https://leafletjs.com/) - Interactive maps
- [Chart.js](https://www.chartjs.org/) - Bar charts
- [CARTO](https://carto.com/) - Dark map tiles
