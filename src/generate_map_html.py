import json
import os

import folium
from geopy.geocoders import GoogleV3
from pyproj import Geod

geolocator = GoogleV3(api_key=os.environ['GOOGLE_GEOLOCATOR_API_KEY'])

# Load the provenance JSON data.
with open("./provenance_import.json", "r", encoding="utf-8") as f:
    provenance = json.load(f)

# Geocodes a list of provenance entries by converting their "location" field into latitude and longitude
# using GoogleV3 API. Filters out entries with missing or unresolvable locations.
# Returns a list of dictionaries including geocoordinates and associated metadata (owner, action, date, etc.).
def geocode_provenance(data):
    coords = []

    for entry in data:
        loc = entry.get("location")

        if not loc:
            continue

        geo = geolocator.geocode(loc)

        if not geo or not geo.latitude or not geo.longitude:
            continue

        coords.append({
            "location": loc,
            "lat": geo.latitude,
            "lon": geo.longitude,
            "owner": entry.get("owner"),
            "action": entry.get("action"),
            "date": entry.get("date"),
            "next_location_unknown": entry.get("next_location_unknown") or False
        })

    return coords

# Builds an interactive Folium map from a list of geocoded provenance entries.
# Places styled markers for each location, shows popups with event details, and draws geodesic paths
# between them to indicate chronological movement. Start and end points are specially styled.
def build_map(places):
    m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)

    # Set the map style
    folium.TileLayer(
        tiles='https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png',
        attr=(
            '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> '
            '&copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> '
            '&copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> '
            '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
        ),
        name='Stadia Stamen Terrain',
        control=False
    ).add_to(m)
    
    # Geodesic curve stuff
    geod = Geod(ellps='WGS84')

    # Markers on map overlap visually by order of placement, ensure the first and last are on top so that their icons are distinguishable.
    middle = places[1:-1]
    first = [places[0]] if places else []
    last = [places[-1]] if len(places) > 1 else []

    all_markers = middle + first + last

    for i, place in enumerate(all_markers):
        # Get correct index of place since we reordered array for the first and last markers
        actual_index = places.index(place)

        # Popup icon HTML. Because markers can overlap each marker's status shows the status for all entries at that location
        # Code could be improved by instead rendering all unique markers and then connecting them afterwards.
        popup_html = "<div style='width:fit-content; max-width:400px; white-space:normal;'>"
        popup_html += "<br><br>".join(
            f"""<b>{j+1}. {p['location']}</b><br>
            {p['action'].capitalize()}<br>
            {p['owner']}<br>
            <i>{p['date']}</i>"""
            for j, p in enumerate(places) if p['lon'] == place['lon'] and p['lat'] == place['lat']
        )
        popup_html += "</div>"

        # Create popup
        iframe = folium.IFrame(html=popup_html, width=200, height=100)
        popup = folium.Popup(iframe)

        if actual_index == 0:
            icon = folium.Icon(color="green", icon="location-dot", prefix="fa")
        elif actual_index == len(places) - 1:
            icon = folium.Icon(color="purple", icon="flag", prefix="fa")
        else:
            icon = folium.Icon(color="blue", icon="location-pin", prefix="fa")

        # Create marker
        folium.Marker(
            location=[place["lat"], place["lon"]],
            popup=popup,
            tooltip=f"Step {actual_index + 1}",
            icon=icon
        ).add_to(m)

        # Draw connecting lines in original order (unaffected)
        if actual_index > 0:
            prev = places[actual_index - 1]
            line_points = geod.npts(prev["lon"], prev["lat"], place["lon"], place["lat"], 50)
            folium_points = [[lat, lon] for lon, lat in line_points]
            folium_points.insert(0, [prev["lat"], prev["lon"]])
            folium_points.append([place["lat"], place["lon"]])
            folium.PolyLine(
                locations=folium_points,
                color="crimson",
                weight=4,
                opacity=0.9,
                dash_array="5,10" if prev["next_location_unknown"] else None
            ).add_to(m)

    return m

# Run everything
if __name__ == "__main__":
    # Calculate coordinates from text locations
    coords = geocode_provenance(provenance.get("entries"))

    # Build the map
    m = build_map(coords)

    # Add the legend to the map's HTML
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 20px; left: 20px; 
        z-index: 9999; 
        background-color: white; 
        border: 2px solid gray; 
        padding: 10px; 
        font-size: 14px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    ">
        <b>Legend</b><br>
        <svg height="10" width="40">
            <line x1="0" y1="5" x2="40" y2="5" style="stroke:crimson;stroke-width:3" />
        </svg> Solid Line: Documented provenance<br>
        <svg height="10" width="40">
            <line x1="0" y1="5" x2="40" y2="5" style="stroke:crimson;stroke-width:3;stroke-dasharray:6,6" />
        </svg> Dotted Line: Unknown provenance<br>
        <svg width="12" height="12" style="margin-right:4px;">
            <circle cx="6" cy="6" r="5" fill="#72B026" stroke="black" stroke-width="1"/>
        </svg> First known location<br>
        <svg width="12" height="12" style="margin-right:4px;">
            <circle cx="6" cy="6" r="5" fill="#D252B9" stroke="black" stroke-width="1"/>
        </svg> Last known location
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    tms_id = provenance.get("id")

    # Save the map to the HTML file
    m.save(f"./templates/{tms_id}_map.html")