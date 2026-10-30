import json
import re
import os
import glob

def load_vnf_catalog(json_path):
    """
    Loads the VNF catalog from the JSON file and returns a dictionary
    that maps the VNF ID to its hardware value.
    
    :param json_path: Path to the catalogoVNF.json file
    :return: Dictionary { 'vnf_name': hardware_int }
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    vnf_map = {}
    for vnf in catalog:
        vnf_id = vnf.get("id")
        hardware = vnf.get("hardware")
        if vnf_id and hardware is not None:
            vnf_map[vnf_id] = hardware
            
    return vnf_map

def enrich_intent_with_hardware(intent_text, vnf_map):
    """
    Searches the intent text for the VNF names present in the catalog
    and replaces them with the formatted string <identifier, hardware>.
    
    :param intent_text: String containing the original intent text
    :param vnf_map: Dictionary returned by load_vnf_catalog()
    :return: String with the modified intent text
    """
    enriched_text = intent_text
    
    # Sort VNF names by length in descending order.
    # This prevents bugs in case a VNF name is a substring of another.
    vnf_ids = sorted(vnf_map.keys(), key=len, reverse=True)
    
    for vnf_id in vnf_ids:
        hardware = vnf_map[vnf_id]
        # Use \b to make sure to replace only whole words and not parts of other words
        pattern = r'\b' + re.escape(vnf_id) + r'\b'
        replacement = f"<{vnf_id}, {hardware}>"
        
        # Perform the replacement in the text
        enriched_text = re.sub(pattern, replacement, enriched_text)
        
    return enriched_text

def process_intent_file(intent_path, json_path):
    """
    Reads a single intent file, applies the replacement, and returns the modified text.
    
    :param intent_path: Path to the intent text file
    :param json_path: Path to the JSON catalog file
    :return: Modified intent text
    """
    vnf_map = load_vnf_catalog(json_path)
    
    with open(intent_path, 'r', encoding='utf-8') as f:
        intent_text = f.read()
        
    return enrich_intent_with_hardware(intent_text, vnf_map)

def process_intent_folder(intent_dir, json_path):
    """
    Reads all text files (.txt) inside the specified folder,
    skipping any catalogs, and returns a dictionary with the results.
    
    :param intent_dir: Path to the folder containing the intents (e.g. 'intent')
    :param json_path: Path to the JSON catalog file
    :return: Dictionary { 'filename.txt': 'modified_text' }
    """
    vnf_map = load_vnf_catalog(json_path)
    results = {}
    
    # Search for all .txt files in the folder
    search_pattern = os.path.join(intent_dir, "*.txt")
    for file_path in glob.glob(search_pattern):
        filename = os.path.basename(file_path)
        
        # Avoid processing the original catalog file if it is in the same folder
        if "catalogo" in filename.lower():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            intent_text = f.read()
            
        results[filename] = enrich_intent_with_hardware(intent_text, vnf_map)
        
    return results

# ==========================================
# USAGE EXAMPLE (if executed directly)
# ==========================================
if __name__ == "__main__":
    # Calculate the absolute path based on where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    CATALOG_JSON = os.path.join(script_dir, "..", "dataset", "catalogoVNF.json")
    
    # Test 1: Processing a test string
    print("--- STRING TEST ---")
    
    try:
        catalog_map = load_vnf_catalog(CATALOG_JSON)
        example_text = "The operator requests to deploy a mailGatewayVF and subsequently a sandboxScannerVF."
        example_result = enrich_intent_with_hardware(example_text, catalog_map)
        print("Original:", example_text)
        print("Modified:", example_result)
    except FileNotFoundError:
        print(f"Error: Unable to find the file '{CATALOG_JSON}'.")
        print("Ensure that catalogoVNF.json exists in the dataset folder.")
