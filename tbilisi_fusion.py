import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

def apply_crosswalk_safety_adjustments(safety_map_geojson_path, crosswalk_points_gdf, gamma=15.0):
    """
    Phase 4 Spatial Fusion Loop:
    Ingests the scored 30-meter segment map from Phase 2, maps out the detected crosswalk points,
    and applies a penalty reduction to the Speed Safety Score on corridors with crossing deficits.
    """
    print("🔄 Initializing Phase 4: Fusing Computer Vision detections with the road safety layer...")
    
    # 1. Ingest the previously generated GeoJSON safety map and project back to metric meters (UTM 38N)
    segments_gdf = gpd.read_file(safety_map_geojson_path).to_crs(epsg=32638)
    
    # Ensure the crosswalk layer matches the local metric reference grid
    crosswalks_projected = crosswalk_points_gdf.to_crs(epsg=32638)
    
    # 2. Generate a localized proximity buffer (e.g., 15 meters) around each segment centerline
    # to catch crosswalk points that sit directly on or immediately adjacent to the road
    segments_buffer = segments_gdf.copy()
    segments_buffer['geometry'] = segments_buffer['geometry'].buffer(15)
    
    print("🔍 Auditing infrastructure gaps across the network arrays...")
    # 3. Perform a spatial join to count how many crosswalk points fall within each road segment's buffer zone
    joined = gpd.sjoin(crosswalks_projected, segments_buffer, how='inner', predicate='intersects')
    crosswalk_counts = joined.groupby('index_right').size().to_dict()
    
    # 4. Map the crosswalk counts back onto our primary master segment layer
    segments_gdf['crosswalk_count'] = segments_gdf.index.map(crosswalk_counts).fillna(0).astype(int)
    
    # 5. Apply the Safe System infrastructure deficit adjustment
    for idx, row in segments_gdf.iterrows():
        # Target multi-lane arterials or high-risk institutional zones where crossings are non-negotiable
        if row['v_safe'] <= 50 and row['lanes'] >= 3:
            if row['crosswalk_count'] == 0:
                print(f"⚠️ Infrastructure Gap Identified on OSM Segment {row['osm_id']} (No crosswalks detected!)")
                
                # Safe System Rule: If a wide, high-volume road forces pedestrians to cross 
                # without infrastructure, drop the bio-mechanically safe threshold speed even lower
                adjusted_v_safe = 30 
                segments_gdf.at[idx, 'v_safe'] = adjusted_v_safe
                
    # 6. Recalculate the safety metrics using our new, adjusted velocity gap values
    segments_gdf['delta_v'] = segments_gdf['legal_limit'] - segments_gdf['v_safe']
    segments_gdf['speed_safety_score'] = 100 * np.exp(- (np.maximum(0, segments_gdf['delta_v']) / gamma))
    
    # Update automated risk tier classifications
    conditions = [
        (segments_gdf['delta_v'] >= 30),
        (segments_gdf['delta_v'] >= 15) & (segments_gdf['delta_v'] < 30),
        (segments_gdf['delta_v'] < 15)
    ]
    labels = ['Tier 1 Critical Hazard (Red)', 'Tier 2 Moderate Mismatch (Amber)', 'Compliant Segment (Green)']
    segments_gdf['risk_tier'] = np.select(conditions, labels, default='Compliant')
    
    return segments_gdf

# --- DEMONSTRATION RUN WINDOW ---
if __name__ == "__main__":
    # Mocking data layer variables for verification check:
    # Let's simulate a couple of crosswalk coordinates detected by our aerial camera framework
    # (These coordinates use local UTM Zone 38N coordinates matching central Tbilisi)
    mock_crosswalk_points = [
        Point(482100, 4621500), # Mock crossing point A
        Point(485400, 4623100)  # Mock crossing point B
    ]
    
    mock_crosswalks_gdf = gpd.GeoDataFrame(
        {'confidence': [0.92, 0.88]}, 
        geometry=mock_crosswalk_points, 
        crs="EPSG:32638"
    )
    
    # Path to the geojson layer file we built together earlier
    geojson_path = "tbilisi_speed_safety_analysis.geojson"
    
    try:
        # Run the fusion update processing loop
        updated_safety_map = apply_crosswalk_safety_adjustments(geojson_path, mock_crosswalks_gdf)
        
        # Save back to geojson format ready for QGIS rendering
        final_output = updated_safety_map.to_crs(epsg=4326)
        final_output.to_file("tbilisi_speed_safety_analysis.geojson", driver="GeoJSON")
        print("\n🎉 Success! Phase 4 Fusion complete. Your QGIS safety layer has been updated with crosswalk analytics.")
        
    except FileNotFoundError:
        print(f"🛑 Error: Could not find '{geojson_path}'. Make sure it's in your active directory folder!")