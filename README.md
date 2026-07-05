# Proactive Safe System Velocity Auditing Framework — Tbilisi

This repository contains the complete end-to-end Spatial AI and Computer Vision pipeline developed for the ADB Road Safety Challenge. Moving away from reactive "blackspot" analysis, this framework proactively calculates a biomechanical **Speed Safety Score (SSS)** across Tbilisi's road grid to design out structural risks before fatalities occur.

---

## 🚀 Project Deliverables

### [Deliverable 1: Analytical Model](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/tree/main/1_Analytical_Model)
*   **Description:** This directory contains the complete technical methodology and source code executing our multi-phase spatial pipeline. It includes the logic for automated OpenStreetMap centerline processing, localized 150-meter Vulnerable Road User (VRU) buffer generation, and the **PyTorch ResNet-18 Convolutional Neural Network (CNN)** code designed to extract crosswalk infrastructure gaps from high-resolution aerial imagery.
*   **Key Contents:** 
    *   `tbilisi_safety.py`: Base network and land-use vector calculation script.
    *   `tbilisi_vision.py`: Image segmentation pipeline architecture for crosswalk pattern detection.
    *   `methodology.md`: Full detailed technical approach, validation limits, and international replication protocols.

### [Deliverable 2: Speed Safety Score Classification](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/tree/main/2_Speed_Safety_Score)
*   **Description:** This folder hosts our automated classification engine and fusion script. It calculates the absolute velocity gap ($\Delta V = V_{legal} - V_{safe}$) for every 30-meter road segment and assigns an exponential decay safety metric based on kinetic energy survival limits.
*   **Key Contents:**
    *   `tbilisi_fusion.py`: Production script executing spatial joins between crosswalk data arrays and segment vectors.
    *   **Classification Hierarchy:**
        *   🔴 **Tier 1 Critical Hazard (Red):** $\Delta V \ge 30 \text{ km/h}$ (Severe speed mismatches or multi-lane crossing deficits).
        *   🟡 **Tier 2 Moderate Mismatch (Amber):** $15 \text{ km/h} \le \Delta V < 30 \text{ km/h}$ (Corridors requiring traffic calming).
        *   🟢 **Compliant Segment (Green):** $\Delta V < 15 \text{ km/h}$ (Safe velocity profiles aligned with human tolerance).

### [Deliverable 3: Geospatial Visualization Dashboard](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/tree/main/3_Geospatial_Visualization)
*   **Description:** The final actionable mapping layer ready for immediate deployment inside Geographic Information Systems (QGIS / ArcGIS). It provides city officials and transport ministries with an empirical, micro-targeted investment map.
*   **Key Contents:**
    *   `tbilisi_speed_safety_analysis.geojson`: Complete, attribute-rich geospatial data vector file mapping all calculated risk metrics.
    *   `tbilisi_safety_map.jpg`: Standardized traffic-light theme visualization mapping the spatial concentration of Tier 1 hazards flanking Tbilisi's urban core.

---

## 👥 Our Team & Motivation
Our team represents a strategic partnership between grassroots **road safety advocacy** and **advanced statistical data modeling**. We joined forces for this challenge to bridge the historical gap between passionate traffic safety campaigns and scalable, high-precision quantitative frameworks—giving development banks and municipal engineers the scientific tools needed to achieve Vision Zero.
