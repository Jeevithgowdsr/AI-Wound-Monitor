import cv2
import numpy as np
from PIL import Image
import random
import requests
import io

# --- Optional: External API key for better wound recognition ---
DEEP_AI_KEY = "YOUR_API_KEY"  # Replace with your actual API key

def analyze_with_api(pil_image):
    """
    Use external API (DeepAI or similar) for wound detection if OpenCV fails.
    """
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    buffered.seek(0)

    response = requests.post(
        "https://api.deepai.org/api/image-similarity",  # Replace with actual wound detection API
        files={"image": buffered},
        headers={"api-key": DEEP_AI_KEY}
    )
    result = response.json()
    # You can parse result to extract wound_area, redness etc.
    return result

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

    # --- Improved preprocessing for better recognition ---
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # Use adaptive thresholding for varied lighting
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 4
    )

    # Morphological operations to clean noise
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

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

        # Smooth mask to reduce jagged edges
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Calculate average color of wound area
        mean_color = cv2.mean(open_cv_image, mask=mask)[:3]

        # Simple logic for infection risk based on redness
        if mean_color[2] > 150:  # Red channel
            wound_color_analysis["redness"] = round(mean_color[2])
    else:
        # --- Optional: fallback to API if no wound detected ---
        api_result = analyze_with_api(pil_image)
        # Map API result to wound_area and redness (adjust as needed)
        wound_area = api_result.get("wound_area", 0)
        wound_color_analysis["redness"] = api_result.get("redness", 0)

    # Convert processed image back to PIL format
    final_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))

    return final_image, wound_area, wound_color_analysis

def get_detailed_report(wound_area, color_analysis):
    """
    Generates a more detailed, less random report based on area and color.
    """
    # Healing Score Logic: Smaller area = better score
    healing_score = max(0, 100 - (wound_area / 50000) * 100)
    
    infection_risk = "Low"
    description = "The wound appears to be healing well. The tissue is closing, and inflammation is minimal."

    if color_analysis["redness"] > 160:
        infection_risk = "High"
        description = "Significant redness detected, which may indicate inflammation or potential infection. Monitor closely."
        healing_score -= 20
    elif color_analysis["redness"] > 140:
        infection_risk = "Medium"
        description = "Moderate redness is present. Continue to observe for signs of infection."
        healing_score -= 10

    # Add short wound description based on area
    if wound_area < 2000:
        short_desc = " Small wound, minimal tissue damage."
    elif wound_area < 10000:
        short_desc = " Moderate wound, some inflammation observed."
    else:
        short_desc = " Large wound, significant tissue involvement. Monitor closely."
    description += short_desc

    report = {
        "description": description,
        "healing_score": max(0, round(healing_score)),
        "infection_risk": infection_risk,
        "wound_area": round(wound_area, 2)
    }
    return report
