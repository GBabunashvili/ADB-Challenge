import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
import numpy as np

def download_tbilisi_network():
    """
    Step 1 (Updated for OSMnx 2.x): Download Tbilisi's drivable road network 
    and project it to a local coordinate reference system (UTM 38N) for accurate metric tracking.
    """
    print("🤖 Step 1: Downloading Tbilisi street network from OSM...")
    place_name = "Tbilisi, Georgia"
    
    # Ingest the drivable network structure using updated API parameters
    graph = ox.graph_from_place(place_name, network_type='drive')
    
    # Project graph to UTM Zone 38N (EPSG:32638) to perform calculations in meters
    graph_projected = ox.project_graph(graph, to_crs="EPSG:32638")
    
    # Convert graph edges into a standard GeoPandas GeoDataFrame
    _, edges = ox.graph_to_gdfs(graph_projected, nodes=True, edges=True)
    return edges

def download_critical_facilities():
    """
    Step 2 (Updated for OSMnx 2.x): Pull points and polygons representing sensitive 
    infrastructure assets (Schools, Kindergartens, Hospitals) across Tbilisi using features_from_place.
    """
    print("🏥 Step 2: Fetching critical institutional facilities from OSM...")
    place_name = "Tbilisi, Georgia"
    
    # Define tags for targeting vulnerable road user (VRU) hotspots
    vru_tags = {
        'amenity': ['school', 'kindergarten', 'hospital', 'clinic'],
        'building': ['school', 'hospital', 'kindergarten']
    }
    
    # Download facility geometries and project to meters matching the road vectors
    facilities = ox.features_from_place(place_name, tags=vru_tags)
    facilities_projected = facilities.to_crs(epsg=32638)
    return facilities_projected

def segment_roads_30m(edges_gdf):
    """
    Step 3: Linear vector subdivision. Chop variable-length OSM road lines 
    into clean, standardized 30-meter segments to ensure fine-grained spatial tracking.
    """
    print("📏 Step 3: Splitting road network into uniform 30-meter segment vectors...")
    segmented_records = []
    segment_length = 30.0  # target length in meters
    
    for idx, row in edges_gdf.iterrows():
        geom = row['geometry']
        if not isinstance(geom, LineString):
            continue
            
        total_length = geom.length
        # Extract metadata metrics from OSM tags
        osm_id = row.get('osmid', 0)
        highway_type = row.get('highway', 'unclassified')
        lanes_tag = row.get('lanes', '2')
        
        # Handle cases where lanes tag is packaged as a list
        if isinstance(lanes_tag, list):
            lanes_tag = lanes_tag[0]
        try:
            lanes = int(float(lanes_tag))
        except ValueError:
            lanes = 2

        # Break the line string down at 30-meter intervals
        num_segments = int(np.ceil(total_length / segment_length))
        for i in range(num_segments):
            start_dist = i * segment_length
            end_dist = min((i + 1) * segment_length, total_length)
            
            # Extract the specific geometric substring
            seg_geom = geom.interpolate(start_dist).coords[:] + geom.interpolate(end_dist).coords[:]
            if len(seg_geom) >= 2:
                seg_line = LineString(seg_geom)
                segmented_records.append({
                    'osm_id': osm_id if not isinstance(osm_id, list) else osm_id[0],
                    'highway': highway_type if not isinstance(highway_type, list) else highway_type[0],
                    'lanes': lanes,
                    'geometry': seg_line
                })
                
    return gpd.GeoDataFrame(segmented_records, crs="EPSG:32638")

def parse_georgian_speed_laws(row):
    """
    Step 4: AI Statutory Translation. Map standard urban baselines dictated by the 
    Law of Georgia on Road Traffic against default road infrastructure layers.
    """
    highway = row['highway']
    # Baseline legal urban speed limit maximum in built-up settlements is 60 km/h
    base_limit = 60
    
    # Adjust for arterial networks or exceptions where Tbilisi City Hall typically increases limits
    if highway in ['trunk', 'motorway']:
        base_limit = 80  # E.g., Kakheti Highway, Right Bank express segments
    elif highway == 'residential':
        base_limit = 60  # Local residential side streets
        
    return base_limit

def calculate_speed_safety_model(segments_gdf, facilities_gdf):
    """
    Step 5: Safe System Mismatch Processing. Run proximity queries, compute safe thresholds,
    and output individual Speed Safety Scores (SSS).
    """
    print("🛡️ Step 5: Executing spatial proximity analytics and calculating Speed Safety Scores...")
    
    # Generate 150-meter bounding safety buffers around critical facilities
    facilities_buffer = facilities_gdf.copy()
    facilities_buffer['geometry'] = facilities_buffer['geometry'].buffer(150)
    
    # Dissolve overlapping facility buffers into a single polygon layer for fast tracking intersections
    vru_risk_zone = facilities_buffer.union_all()
    
    # Map legal speed profiles onto segments
    segments_gdf['legal_limit'] = segments_gdf.apply(parse_georgian_speed_laws, axis=1)
    
    # Initialize Safe System velocities matching legal baselines
    segments_gdf['v_safe'] = segments_gdf['legal_limit']
    
    # Loop over segments to run localized vulnerability checks
    for idx, row in segments_gdf.iterrows():
        geom = row['geometry']
        lanes = row['lanes']
        
        # Criterion A: Proximity to vulnerable road users
        if geom.intersects(vru_risk_zone):
            # Safe System Rule: Enforce 30 km/h cap if kids/patients share the corridor space
            segments_gdf.at[idx, 'v_safe'] = 30
            
        # Criterion B: Geometric friction scaling (High lane counts invite multi-threat collision forces)
        elif lanes >= 4 and row['v_safe'] > 50:
            # Drop multi-lane undivided urban boulevards to a maximum 50 km/h threshold safety floor
            segments_gdf.at[idx, 'v_safe'] = 50

    # Calculate Mismatch Metrics (Delta Velocity Gap)
    segments_gdf['delta_v'] = segments_gdf['legal_limit'] - segments_gdf['v_safe']
    
    # Apply exponential decay scoring mechanics (Gamma scale = 15.0)
    gamma = 15.0
    segments_gdf['speed_safety_score'] = 100 * np.exp(- (np.maximum(0, segments_gdf['delta_v']) / gamma))
    
    # Automate risk corridor isolation labels
    conditions = [
        (segments_gdf['delta_v'] >= 30),
        (segments_gdf['delta_v'] >= 15) & (segments_gdf['delta_v'] < 30),
        (segments_gdf['delta_v'] < 15)
    ]
    labels = ['Tier 1 Critical Hazard (Red)', 'Tier 2 Moderate Mismatch (Amber)', 'Compliant Segment (Green)']
    segments_gdf['risk_tier'] = np.select(conditions, labels, default='Compliant')
    
    return segments_gdf

# --- MAIN EXECUTION CHAIN ---
if __name__ == "__main__":
    # Ingest and Process
    raw_edges = download_tbilisi_network()
    critical_assets = download_critical_facilities()
    road_segments = segment_roads_30m(raw_edges)
    
    # Run Safe System Processing Loop
    safety_map_layer = calculate_speed_safety_model(road_segments, critical_assets)
    
    # Output spatial files back to standard tracking geometries
    print("💾 Step 6: Exporting processed layer to GeoJSON map file...")
    # Convert metric coordinate layer back to GPS-ready latitudes/longitudes (WGS84)
    final_output_layer = safety_map_layer.to_crs(epsg=4326)
    final_output_layer.to_file("tbilisi_speed_safety_analysis.geojson", driver="GeoJSON")
    
    print("\n✅ Processing Complete! Open 'tbilisi_speed_safety_analysis.geojson' in QGIS to visualize your safety scores.")
    print(final_output_layer[['highway', 'lanes', 'legal_limit', 'v_safe', 'speed_safety_score', 'risk_tier']].head())
    