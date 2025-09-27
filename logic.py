import cv2
import numpy as np
from PIL import Image
import random

def analyze_wound(pil_image):
    """
    This is the main analysis function. It finds the wound, isolates it,
    calculates its area, and analyzes its color.
    """
    # Convert PIL image to OpenCV format
    open_cv_image = np.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    # --- Step 1: Find the largest contour (the wound) ---
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    # Use adaptive thresholding for better results in varied lighting
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    wound_area = 0
    processed_image = open_cv_image.copy()
    wound_color_analysis = {"redness": 0, "unhealthy_tissue": 0}

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        
        # --- Step 2: Calculate Area ---
        wound_area = cv2.contourArea(largest_contour)

        # --- Step 3: Draw contour and area on the image ---
        cv2.drawContours(processed_image, [largest_contour], -1, (0, 255, 0), 3)
        # Put the area text on the image
        text = f"Area: {wound_area:.2f} px"
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.rectangle(processed_image, (10, 30-h-5), (10+w+5, 30+5), (0,0,0), -1)
        cv2.putText(processed_image, text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # --- Step 4: Isolate the wound and analyze color ---
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [largest_contour], -1, 255, -1)
        # Calculate the average color of the wound area
        mean_color = cv2.mean(open_cv_image, mask=mask)[:3]
        
        # Simple logic for infection risk based on redness
        # BGR format, so Red is index 2
        if mean_color[2] > 150: # High red component
            wound_color_analysis["redness"] = round(mean_color[2])
            
    # Convert processed image back to PIL format
    final_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))

    return final_image, wound_area, wound_color_analysis

def get_detailed_report(wound_area, color_analysis):
    """
    Generates a more detailed, less random report based on area and color.
    """
    # Healing Score Logic: Smaller area = better score
    # Normalize score (e.g., assuming max area is 50000 px)
    healing_score = max(0, 100 - (wound_area / 50000) * 100)
    
    infection_risk = "Low"
    description = "The wound appears to be healing well. The tissue is closing, and inflammation is minimal."

    if color_analysis["redness"] > 160: # Threshold for significant redness
        infection_risk = "High"
        description = "Significant redness detected, which may indicate inflammation or potential infection. Monitor closely."
        healing_score -= 20 # Penalize score for redness
    elif color_analysis["redness"] > 140:
        infection_risk = "Medium"
        description = "Moderate redness is present. Continue to observe for signs of infection."
        healing_score -= 10

    report = {
        "description": description,
        "healing_score": max(0, round(healing_score)),
        "infection_risk": infection_risk,
        "wound_area": round(wound_area, 2)
    }
    return report