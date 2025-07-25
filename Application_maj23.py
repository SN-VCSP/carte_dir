import folium
from folium.plugins import Draw, MeasureControl
import pandas as pd
from pyproj import Transformer
import os
import shutil
import base64

import os

# Dossier contenant les fichiers HTML
import os

html_dir = "cartes_agences"

meta_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
style_tag = """
<style>
button {
    font-size: 4px !important;
    padding: 10px 14px !important;
    touch-action: manipulation;
}
</style>
"""

for filename in os.listdir(html_dir):
    if filename.endswith(".html") and not filename.endswith("_mobile.html"):
        file_path = os.path.join(html_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "<head>" in content and "</head>" in content:
            content = content.replace("<head>", f"<head>\n{meta_tag}", 1)
            content = content.replace("</head>", f"{style_tag}\n</head>", 1)

            touch_script = """
<script>
L.Map.addInitHook(function () {
    this._container.addEventListener('touchstart', function () {}, { passive: true });
});
</script>
"""
            content = content.replace("</body>", f"{touch_script}\n</body>")

            new_filename = filename.replace(".html", "_mobile.html")
            new_file_path = os.path.join(html_dir, new_filename)
            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(content)

print("✅ Fichiers HTML adaptés pour mobile corrigés avec succès.")

# Coordinates of the main cities of Bouches-du-Rhône
villes_bdr = {
    "Marseille": (43.2965, 5.3698),
    "Aix-en-Provence": (43.5297, 5.4474),
    "Arles": (43.6766, 4.6278),
    "Martigues": (43.4058, 5.0480),
    "Salon-de-Provence": (43.6400, 5.0970),
    "Istres": (43.5167, 4.9833),
    "Vitrolles": (43.4600, 5.2489),
    "Miramas": (43.5833, 5.0000),
    "Fos-sur-Mer": (43.5333, 4.9333),
    "Chateauneuf-les-martigues": (43.38835, 5.1492),
    "Aubagne": (43.293046, 5.56842)
}

def ajouter_noms_villes_bdr(map_objet):
    for ville, (lat, lon) in villes_bdr.items():
        folium.map.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 11pt; color: white; font-family: Arial; font-weight: bold;">{ville}</div>'
            )
        ).add_to(map_objet)

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def ajouter_bouton_geolocalisation(map_objet, carte_nom_base):
    geoloc_html = f"""
    <div id="geoloc-controls" style="
        position: fixed;
        top: 50%;
        right: 10px;
        transform: translateY(-50%);
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
        font-family: Arial;
        font-size: 10pt;">
        <button onclick="activerGeolocalisation()" style="background-color: #007bff; color: white; border: none; padding: 5px 10px; margin: 2px; border-radius: 4px;">Ajouter Info-Bulle à ma position</button>
    </div>
    <script>
    var nomCarte = "{carte_nom_base}";

    function activerGeolocalisation() {{
        if (!navigator.geolocation) {{
            alert("La géolocalisation n'est pas supportée par votre navigateur.");
            return;
        }}
        navigator.geolocation.getCurrentPosition(function(position) {{
            var lat = position.coords.latitude;
            var lng = position.coords.longitude;
            var texte = prompt("Entrez le texte de l'info-bulle:");
            if (texte === null || texte.trim() === "") {{
                alert("Annotation annulée.");
                return;
            }}
            var map = {map_objet.get_name()};
            var marker = L.marker([lat, lng]).addTo(map);
            var bulles = JSON.parse(localStorage.getItem(nomCarte + "_bulles") || "[]");
            var index = bulles.length;
            var popupContent = texte + '<br><button onclick="supprimerBulle(' + index + ')">Supprimer cette info-bulle</button>';

            marker.bindPopup(popupContent).openPopup();
            enregistrerBulle(lat, lng, texte, "geoloc");
        }}, function(error) {{
            alert("Erreur de géolocalisation: " + error.message);
        }});
    }}

    function supprimerBulleGeoloc() {{
        alert("Veuillez utiliser le bouton 'Supprimer toutes les annotations' pour retirer cette info-bulle.");
    }}
    </script>
    """
    map_objet.get_root().html.add_child(folium.Element(geoloc_html))


# The rest of the user's script would go here, and at the appropriate places, we integrate the new function:
# For example, after creating the main map `m_all`, we add:
# ajouter_bouton_geolocalisation(m_all, "carte_toutes_agences")

# Similarly, for each agency map `m`, we add:
# ajouter_bouton_geolocalisation(m, f"carte_{safe_agence_name}")

# Updated function to add info-bubble and OSM/Esri toggle buttons

def ajouter_boutons_info_bulle_et_osm(map_objet, carte_nom_base):
    script_html = f"""
<div id="info-bulle-controls" style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    background-color: rgba(255, 255, 255, 0.9);
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 0 16px rgba(0,0,0,0.2);
    font-family: Arial;
    font-size: 12pt;">
<button onclick="activerAjoutInfoBulle()" style="background-color: #007bff; color: white;">Ajouter annotation</button>
<button onclick="changerFondCarte()" style="background-color: #28a745; color: white;">Passer à OpenStreetMap</button>
<button onclick="location.reload()" style="background-color: #6f42c1; color: white;">Recharger la carte</button>
<button onclick="supprimerToutesLesBulles()" style="background-color: #dc3545; color: white;">Supprimer toutes les annotations</button>
<button onclick="exporterBulles()" style="background-color: #ffc107; color: white;">Exporter les annotations</button>
<button onclick="document.getElementById('importFile').click()" style="background-color: #17a2b8; color: white;">Importer les annotations</button>
<input type="file" id="importFile" style="display: none;" accept=".json" onchange="importerBulles(event)">
</div>
 
<script>
var ajoutInfoBulleActif = false;
var compteurBulles = 0;
var maxBulles = 200;
var nomCarte = "{carte_nom_base}";
 
function activerAjoutInfoBulle() {{
    if (compteurBulles >= maxBulles) {{
        alert("Limite de 200 info-bulles atteinte.");
        return;
    }}
    alert("Cliquez sur la carte pour placer l'info-bulle.");
    ajoutInfoBulleActif = true;
}}
 
function changerFondCarte() {{
    var map = {map_objet.get_name()};
    var osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; https://www.openstreetmap.org/copyright contributors'
    }});
    map.eachLayer(function(layer) {{
        map.removeLayer(layer);
    }});
    osmLayer.addTo(map);
}}
 
function chargerBulles(map) {{
    var bulles = JSON.parse(localStorage.getItem(nomCarte + "_bulles") || "[]");
    bulles.forEach(function(bulle, index) {{
        var marker = L.marker([bulle.lat, bulle.lng]).addTo(map);
        var popupContent = bulle.texte + '<br><button onclick="supprimerBulle(' + index + ')">Supprimer</button>';
        marker.bindPopup(popupContent);
        compteurBulles++;
    }});
}}
 
function enregistrerBulle(lat, lng, texte) {{
    var bulles = JSON.parse(localStorage.getItem(nomCarte + "_bulles") || "[]");
    bulles.push({{lat: lat, lng: lng, texte: texte}});
    localStorage.setItem(nomCarte + "_bulles", JSON.stringify(bulles));
}}
 
function supprimerBulle(index) {{
    if (confirm("Supprimer cette info-bulle ?")) {{
        var bulles = JSON.parse(localStorage.getItem(nomCarte + "_bulles") || "[]");
        bulles.splice(index, 1);
        localStorage.setItem(nomCarte + "_bulles", JSON.stringify(bulles));
        location.reload();
    }}
}}
 
function supprimerToutesLesBulles() {{
    if (confirm("Êtes-vous sûr de vouloir supprimer toutes les info-bulles ?")) {{
        localStorage.removeItem(nomCarte + "_bulles");
        location.reload();
    }}
}}
 
function exporterBulles() {{
    var bulles = JSON.parse(localStorage.getItem(nomCarte + "_bulles") || "[]");
    var dataStr = JSON.stringify(bulles, null, 2); // Ajout d'indentation pour lisibilité
    var blob = new Blob([dataStr], {{ type: "application/json" }});
    var url = URL.createObjectURL(blob);
    var exportFileDefaultName = nomCarte + '_bulles.json';
 
    var linkElement = document.createElement('a');
    linkElement.setAttribute('href', url);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.setAttribute('type', 'application/json');
    document.body.appendChild(linkElement);
    linkElement.click();
    document.body.removeChild(linkElement);
}}
 
function importerBulles(event) {{
    var file = event.target.files[0];
    if (file) {{
        var reader = new FileReader();
        reader.onload = function(e) {{
            var bulles = JSON.parse(e.target.result);
            localStorage.setItem(nomCarte + "_bulles", JSON.stringify(bulles));
            location.reload();
        }}
        reader.readAsText(file);
    }}
}}
 
document.addEventListener("DOMContentLoaded", function() {{
    var map = {map_objet.get_name()};
    chargerBulles(map);
    map.on('click', function(e) {{
        if (!ajoutInfoBulleActif) return;
        var texte = prompt("Entrez le texte de l'info-bulle:");
        if (texte) {{
            var marker = L.marker(e.latlng).addTo(map);
            var popupContent = texte + '<br><button onclick="supprimerBulle(' + compteurBulles + ')">X</button>';
            marker.bindPopup(popupContent).openPopup();
            enregistrerBulle(e.latlng.lat, e.latlng.lng, texte);
            compteurBulles++;
        }}
        ajoutInfoBulleActif = false;
    }});
}});
</script>
    """
    map_objet.get_root().html.add_child(folium.Element(script_html))

def ajouter_interface_filtrage(map_objet):
   filter_html = """
<div id="filter-controls" style="
       position: fixed;
       bottom: 25px;
       right: 10px;
       z-index: 9999;
       background-color: rgba(255, 255, 255, 0.9);
       padding: 10px;
       border-radius: 8px;
       box-shadow: 0 0 15px rgba(0,0,0,0.2);
       font-family: Arial;
       font-size: 11pt;">
<strong>Masquer-Afficher:</strong><br>
<button onclick="toggleLayer('oui')" style="background-color: #95c415; color: white; border: none; padding: 5px 10px; margin: 2px; border-radius: 4px;">Fait (Oui)</button>
<button onclick="toggleLayer('non')" style="background-color: #aa9e9f; color: white; border: none; padding: 5px 10px; margin: 2px; border-radius: 4px;">Fait (Non)</button>
<button onclick="toggleLayer('all')" style="background-color: #6c757d; color: white; border: none; padding: 5px 10px; margin: 2px; border-radius: 4px;">Tous</button>
<button onclick="toggleLayer('none')" style="background-color: #343a40; color: white; border: none; padding: 5px 10px; margin: 2px; border-radius: 4px;">Aucun</button>
</div>
<script>
   function toggleLayer(option) {
       var ouiLayer = document.querySelectorAll('.fait-oui');
       var nonLayer = document.querySelectorAll('.fait-non');
       if (option === 'oui') {
           ouiLayer.forEach(e => e.style.display = 'block');
           nonLayer.forEach(e => e.style.display = 'none');
       } else if (option === 'non') {
           ouiLayer.forEach(e => e.style.display = 'none');
           nonLayer.forEach(e => e.style.display = 'block');
       } else if (option === 'all') {
           ouiLayer.forEach(e => e.style.display = 'block');
           nonLayer.forEach(e => e.style.display = 'block');
       } else if (option === 'none') {
           ouiLayer.forEach(e => e.style.display = 'none');
           nonLayer.forEach(e => e.style.display = 'none');
       }
   }
</script>
   """
   map_objet.get_root().html.add_child(folium.Element(filter_html))

def ajouter_texte_bas_gauche(map_objet, texte):
    html = f"""
<div style="
       position: fixed;
       bottom: 10px;
       left: 10px;
       z-index: 9999;
       background-color: rgba(255, 255, 255, 0.7);
       padding: 5px;
       font-size: 12pt;
       font-family: Arial;
       font-weight: bold;">
       {texte}
</div>
   """
    map_objet.get_root().html.add_child(folium.Element(html))
    
def ajouter_filigrane_image(map_objet, image_path):
   base64_image = image_to_base64(image_path)
   html = f"""
<div style="
       position: fixed;
       bottom: 40px;
       left: 10px;
       z-index: 9998;
       opacity: 0.5;
    ">
<img src="data:image/png;base64,{base64_image}" alt="Filigrane" style="height: 90px;">
</div>
   """
   map_objet.get_root().html.add_child(folium.Element(html))
# Load data
df = pd.read_csv("DIRMED_EUROVIA_13-JP.csv", delimiter=";")
df.columns = [
   "dateReferentiel", "route", "pr", "depPr", "concessionPr", "abs", "cumul",
   "x", "y", "z", "cote", "Gestionnaire", "Agence", "Fait", "Ausculte", "structure"]
df["x"] = df["x"].astype(str).str.replace(",", ".").astype(float)
df["y"] = df["y"].astype(str).str.replace(",", ".").astype(float)
transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
df["lon"], df["lat"] = transformer.transform(df["x"].values, df["y"].values)
agences_fixes = {
   "MARSEILLE": (902413.26, 6245981.16),
   "PDB": (860877.62, 6259777.08),
   "AIX": (892847.85, 6268323.78)
}
agence_coords = {}
for nom, (x, y) in agences_fixes.items():
   lon, lat = transformer.transform(x, y)
   agence_coords[nom] = (lat, lon)
output_dir = "cartes_agences"
logo_dir = os.path.join(output_dir, "Logos")
os.makedirs(logo_dir, exist_ok=True)
source_logo = "code_nasri/Logos/lg.png"
destination_logo = "Logos/lg.png" #os.path.join(logo_dir, "lg.png")
if os.path.exists(source_logo):
   shutil.copy(source_logo, destination_logo)
map_center = [df["lat"].mean(), df["lon"].mean()]
m_all = folium.Map(location=map_center, zoom_start=10, tiles="Esri.WorldImagery")
ajouter_noms_villes_bdr(m_all)
m_all.add_child(MeasureControl(primary_length_unit='meters'))
ajouter_bouton_geolocalisation(m_all, "carte_toutes_agences")
m_all.add_child(Draw(export=True))
for _, row in df.iterrows():
   fait = str(row["Fait"]).strip().lower()
   color = "#6fdb10" if fait == "oui" else "#ffffff"
   class_name = "fait-oui" if fait == "oui" else "fait-non"
   popup_text = f"""
<div style='
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    font-size: 12px;
    color: #333;
    background-color: #f9f9f9;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
    max-width: 250px;
'>
    <strong>Structure :</strong> {row['structure']}<br>
    <strong>Ausculte :</strong> {row['Ausculte']}
</div>
"""

   if str(row["Ausculte"]).strip().lower() == "oui":
       popup_text += f"<br><div id='structure-label-{row['pr']}' style='display: none;'>{row['structure']}</div>"
   folium.CircleMarker(
       location=[row["lat"], row["lon"]],
       radius=4,
       color=color,
       fill=True,
       fill_color=color,
       fill_opacity=0.05 if str(row["Ausculte"]).strip().lower() == "non" else 0.95,
       popup=popup_text,
       tooltip = f"{row['route']} - {row['pr']} ({row['cote']})",
       **{"className": class_name}
   ).add_to(m_all)
for route in df["route"].unique():
   route_data = df[df["route"] == route]
   if not route_data.empty:
       lat_mean = route_data["lat"].mean() + 0.005
       lon_mean = route_data["lon"].mean()
       folium.map.Marker(
           [lat_mean, lon_mean],
           icon=folium.DivIcon(
               html=f'<div style="font-size: 12pt; color: yellow; font-family: Arial; font-weight: bold;">{route}</div>'
           )
       ).add_to(m_all)
for nom, (lat, lon) in agence_coords.items():
   folium.Marker(
       location=[lat, lon],
       popup=f"Agence fixe: {nom}",
       tooltip=nom,
       icon=folium.Icon(color="blue", icon="building", prefix="fa")
   ).add_to(m_all)
ajouter_interface_filtrage(m_all)
ajouter_texte_bas_gauche(m_all, "Julie PERNIN DTE & Sofienn NASRI VCSP")
ajouter_filigrane_image(m_all, destination_logo)
ajouter_boutons_info_bulle_et_osm(m_all, "carte_toutes_agences")
m_all.save(f"{output_dir}/carte_toutes_agences.html")
for agence, group in df.groupby("Agence"):
   m = folium.Map(tiles="Esri.WorldImagery")
   ajouter_noms_villes_bdr(m)
   m.add_child(MeasureControl(primary_length_unit='meters'))
   m.add_child(Draw(export=True))
   for _, row in group.iterrows():
       fait = str(row["Fait"]).strip().lower()
       color = "#91ff00" if fait == "oui" else "#ffffff"
       class_name = "fait-oui" if fait == "oui" else "fait-non"
       popup_text = f"""
<div style='
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    font-size: 12px;
    color: #333;
    background-color: #f9f9f9;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
    max-width: 250px;
'>
    <strong>Structure :</strong> {row['structure']}<br>
    <strong>Ausculte :</strong> {row['Ausculte']}
</div>
"""

       if str(row["Ausculte"]).strip().lower() == "oui":
           popup_text += f"<br><div id='structure-label-{row['pr']}' style='display: none;'>{row['structure']}</div>"
       folium.CircleMarker(
           location=[row["lat"], row["lon"]],
           radius=4,
           color=color,
           fill=True,
           fill_color=color,
           fill_opacity=0.05 if str(row["Ausculte"]).strip().lower() == "non" else 0.95,
           popup=popup_text,
           tooltip = f"{row['route']} - {row['pr']} ({row['cote']})",
           **{"className": class_name}
       ).add_to(m)
   for route in group["route"].unique():
       route_data = group[group["route"] == route]
       if not route_data.empty:
           lat_mean = route_data["lat"].mean() + 0.005
           lon_mean = route_data["lon"].mean()
           folium.map.Marker(
               [lat_mean, lon_mean],
               icon=folium.DivIcon(
                   html=f'<div style="font-size: 12pt; color: yellow; font-family: Arial; font-weight: bold;">{route}</div>'
               )
           ).add_to(m)
   bounds = [[group["lat"].min(), group["lon"].min()], [group["lat"].max(), group["lon"].max()]]
   m.fit_bounds(bounds)
   if agence.upper() in agence_coords:
       lat, lon = agence_coords[agence.upper()]
       folium.Marker(
           location=[lat, lon],
           popup=f"Agence fixe: {agence}",
           tooltip=agence,
           icon=folium.Icon(color="blue", icon="building", prefix="fa")
       ).add_to(m)
   ajouter_interface_filtrage(m)
   ajouter_texte_bas_gauche(m, "Julie PERNIN DTE & Sofienn NASRI VCSP")
   ajouter_filigrane_image(m, destination_logo)
   safe_agence_name = "".join(c if c.isalnum() else "_" for c in agence)
   ajouter_boutons_info_bulle_et_osm(m, f"carte_{safe_agence_name}")
   ajouter_bouton_geolocalisation(m, f"carte_{safe_agence_name}")
   m.save(f"{output_dir}/carte_{safe_agence_name}.html")