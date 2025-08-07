## Overview

This project visualizes the provenance of artifacts by geocoding their historical locations and displaying them on an interactive map. Each location is marked with details such as ownership, actions (e.g., acquired, loaned), and relevant dates. The final output is an HTML map with markers, geodesic lines, and a legend that differentiates confirmed provenance from uncertain paths.

The tool reduces the manual work of mapping provenance data by automating location lookups, path plotting, and HTML generation.

## Project Structure

The project consists of a single Python script and one primary input file:

- `generate_map_html.py` – Handles geocoding, map creation, and HTML export. Upon running, creates a file in src/templates that generates the HTML file to view the map.
- `provenance_import.json` – Contains the provenance data, including location, owner, action, and date for each entry. This data is used when generate_map_html.py is ran to create the html file.
- `provenance_json_ai_prompt.txt` - Contains a text file with an articulate AI prompt that provides instructions for an LLM to generate the `provenance_import.json` file. Note that the output may not be entirely correct or as-desired, and thus should still be reviewed to ensure its validity before generating the map. Replace the `INSERT ID HERE`, `INSERT TITLE HERE`, and `INSERT PROVENANCE HERE` text with the corresponding information.

In order to enable access to the Google geolocator API to support converting strings to location, set a `GOOGLE_GEOLOCATOR_API_KEY` environment variable.

## Intended Use

This script is designed to convert structured provenance data into a visual map. It can be run multiple times with different datasets, making it useful for curators, researchers, or historians tracking object histories. While tailored to one dataset, it can be easily adapted for other mapping needs. The maps can be viewed locally on a simple development server (localhost or 127.0.0.1). I used the VSCode live server extension, but a simple server could be set up to view HTML files as well. Attempting to simply open the HTML files may cause a stadiamaps authentication error (https://docs.stadiamaps.com/authentication/).

## Process Overview

1. **Data Input**  
   The file `provenance_import.json` must include:
   - `id`: The TMS ID of the artwork.
   - `entries`: An array of objects, each with:
     - `location` (string) – Geocodable place name.  
     - `owner` (string) – Current or previous owner.  
     - `action` (string) – Transfer action (e.g., acquired, loaned).  
     - `date` (string) – Event date.  
     - `next_location_unknown` (optional boolean) – Marks gaps in provenance, set as true if the next provenance entry has a gap between the current one (i.e. "..." in provenance entry).

2. **Geocoding (`geocode_provenance`)**  
   Locations are converted to latitude and longitude using the Google Maps API (via the `geopy` library). The coordinates and associated metadata are stored for map construction.

3. **Map Construction (`build_map`)**  
   - A Folium map is initialized with a custom tile layer. Note that this tile layer may not load unless the HTML is opened with a live server.
   - Markers are placed with color-coded icons:  
     - **Green:** First known location.  
     - **Blue:** Intermediate locations.  
     - **Purple:** Last known location.  
   - Popups display all relevant details for each step.

4. **Geodesic Path Drawing**  
   Using `pyproj.Geod`, curved lines connect sequential locations:  
   - Solid crimson lines indicate confirmed provenance.  
   - Dashed crimson lines represent unknown or uncertain paths.

5. **Legend and Output**  
   A custom HTML legend explains the color and line conventions.  
   The map is saved to `./templates/<ID>_map.html`, where `<ID>` matches the `id` field in the JSON file.
