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
    # vessel types consist of an array of strings, artery/vein, for a particular cord
    # calculated from stage 3
    def predict_sua(vessel_types):
        counts = Counter(vessel_types)
        if counts["Artery"] == 1 and counts["Vein"] == 1:
            return "SUA"
        elif counts["Artery"] == 2 and counts["Vein"] == 1:
            return "Normal"
        else:
            return "Uncertain"

    ## Run Stage 1 ## 
    image, logits, pred_mask  = stage1.run_model(image)
    ## Get the crops from stage 1 ##
    cord_instances = stage1.make_all_instance_crops(
        image=image,
        pred_mask=pred_mask,

        foreground_class=1,
        min_area=2000,
    )
    polygons = []
    ## For each crop in stage 1 ##
    for c_instance in cord_instances:
        ## Run Stage 2 ## 
        image, logits, pred_mask = stage2.run_model(c_instance["crop"])
        ## Make the vessel crops for each cord instance ##
        vessel_instances = stage2.make_all_instance_crops(
                image=image,
                pred_mask=pred_mask,
                foreground_class=1,
                min_area=2000,
            )
        # polygons code
        ox, oy = c_instance["crop_origin"]
        # will contain ["artery", "artery", "vein"] or otherwise
        vessel_info = []
        vessel_types = []
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
                "type": vessel_type,
                "confidence": float(confidence),  
            })


        polygons.append({
            "polygon": c_instance["polygon"],
            "diameter": c_instance["feret_diameter_px"],
            "start_end_points": (c_instance["feret_p1"], c_instance["feret_p2"]),
            "vessels": vessel_info,

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
        
    #########################
    output["polygons"] = polygons
    output["number_of_cords"] = len(cord_instances)
    output["sua"] = diagnostic(cord_instances) == "SUA"
    output["diagnostic"] = diagnostic(cord_instances)

    return output
