'''
This code here links the three stages of the pipeline to make an informed decision

Input -> An Image

Output -> A dictionary with ->
{
Diagnostic: Yes/No
Number of cords detected:
Vessel Polygon = [[Artery, Polygon, Area, Longest Width], [Vein, Polygon, Area, Longest Width]]
Model Confidence: 
Number of Arteries Per Cord: 
Number of Veins Per Cord: 
'''
import os
os.environ["OMP_NUM_THREADS"] = "1"
### This may change depending on the format of the image the API passes in:
import importlib.util
import numpy as np
from collections import Counter
import sys

def load_module(name, path):
    module_dir = os.path.dirname(os.path.abspath(path))
    if module_dir in sys.path:
        sys.path.remove(module_dir)
    sys.path.insert(0, module_dir)
    
    # Clear cached modules from previous stage to avoid conflicts
    for key in list(sys.modules.keys()):
        if key in ("myunet", "dataset", "loader"):
            del sys.modules[key]
    
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

BASE = os.path.dirname(os.path.abspath(__file__))

stage1 = load_module("stage1_utilities", os.path.join(BASE, "stage_1_cordseg/utilities.py"))
stage2 = load_module("stage2_utilities", os.path.join(BASE, "stage_2_vesselseg/utilities.py"))
stage2f = load_module("stage2_featureextractor", os.path.join(BASE, "stage_2_vesselseg/featureextractor.py"))
stage3 = load_module("stage3_predict", os.path.join(BASE, "stage_3_classifier/predict.py"))



def run_pipeline(image):
    # this function will determine sua 
    def predict_sua(vessel_types):
        counts = Counter(vessel_types)
        if counts["Artery"] == 1 and counts["Vein"] == 1:
            return "SUA"
        elif counts["Artery"] == 2 and counts["Vein"] == 1:
            return "Normal"
        else:
            return "Uncertain"


    ## Run Stage 1 ## 
    image, logits, pred_mask, cord_confidence_map  = stage1.run_model(image)
    ## Get the crops from stage 1 ##
    cord_instances = stage1.make_all_instance_crops(
        image=image,
        pred_mask=pred_mask,
        confidence_map=cord_confidence_map,

        foreground_class=1,
        min_area=2000,
    )
    # [["Cord Polygon", [[Polygon 1, Area, Max Diam], [Polygon 2, Area, Max Diam], [Polygon 3, Area, Max Diam]], "Cord Polygon", [Polygon 1, Polygon 2, Polygon 3]]
    polygons = []
    ## For each crop in stage 1 ##
    for c_instance in cord_instances:
        ## Run Stage 2 ## 
        image, logits, pred_mask, vessel_confidence_map = stage2.run_model(c_instance["crop"])
        ## Make the vessel crops for each cord instance ##
        vessel_instances = stage2.make_all_instance_crops(
                image=image,
                pred_mask=pred_mask,
                confidence_map=vessel_confidence_map,
                foreground_class=1,
                min_area=2000,
            )
        # polygons code
        ox, oy = c_instance["crop_origin"]
        # will contain ["artery", "artery", "vein"] or otherwise
        vessel_info = []
        vessel_types = []
        vessel_confidences = []
        for v_instance in vessel_instances:
            ## Compute the polygon vectors ##############
            polygon = v_instance["polygon"]
            polygon_global = [
                coord + ox if i % 2 == 0 else coord + oy
                for i, coord in enumerate(polygon)
            ]
            v_instance["polygon_global"] = polygon_global
            ## Run Stage 3 ##############################
            v_instance_feature = stage2f.get_combined_features(v_instance).reshape(1, -1)
            vessel_type, confidence = stage3.predict_artery_vein(v_instance_feature)
            ############################################
            vessel_types.append(vessel_type)
            vessel_info.append({
                "polygon": polygon_global,
                "area": v_instance["area"],
                "type": vessel_type,
                "heatmap": v_instance.get("heatmap", None),
            })
            vessel_confidences.append({
                "vessel_seg_confidence": v_instance.get("confidence", 0.0),
                "classification_confidence": float(confidence),
            })
        #############################################
        # calculate per cord confidence
        cord_seg_conf = c_instance.get("confidence", 0.0)
        vessel_seg_conf = np.mean([v["vessel_seg_confidence"] for v in vessel_confidences]) if vessel_confidences else 0.0
        classification_conf = np.mean([v["classification_confidence"] for v in vessel_confidences]) if vessel_confidences else 0.0
        cord_confidence = round((cord_seg_conf * 0.4 + vessel_seg_conf * 0.35 + classification_conf * 0.25), 2)
        #############################################
        polygons.append({
            "polygon": c_instance["polygon"],
            "vessels": vessel_info,
            "diameter": max(c_instance["width"], c_instance["height"]),
            "confidence": cord_confidence,
            "heatmap": c_instance.get("heatmap", None),
        })
        ## Make Diagnostic ##############################
        c_instance["diagnostic"] = predict_sua(vessel_types)
        
        print(vessel_types)
    return cord_instances, polygons

def calculate_outputs(cord_instances, polygons):
    output = {}
    ### Helper functions ###
    def diagnostic(cord_instances):
        from collections import Counter
    
        # if any cord is SUA with high confidence, trust it
        for c in cord_instances:
            if c["diagnostic"] == "SUA" and c.get("confidence", 0) > 0.9:
                return "SUA"
            
        diagnostics = [c["diagnostic"] for c in cord_instances]
        counts = Counter(diagnostics)
        most_common, count = counts.most_common(1)[0]
        if count > len(diagnostics) / 2:
            return most_common
        return "Uncertain"
        
    def overall_confidence(polygons):
        if not polygons:
            return 0.0
        return round(np.mean([p["confidence"] for p in polygons]), 2)

    #########################
    output["polygons"] = polygons
    output["number_of_cords"] = len(cord_instances)
    output["sua"] = diagnostic(cord_instances) == "SUA"
    output["diagnostic"] = diagnostic(cord_instances)
    output["confidence"] = overall_confidence(polygons)

    return output
