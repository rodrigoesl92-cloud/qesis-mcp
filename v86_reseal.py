import json
import hashlib
from datetime import datetime, UTC

input_path = 'data/qesis_v8.json'
output_path = 'data/qesis_v8.6.json'

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated = False

    # Recursively hunt down the SAU anomaly footprint
    def patch_sau(node):
        global updated
        if isinstance(node, dict):
            if "cse_components" in node and isinstance(node["cse_components"], dict):
                comp = node["cse_components"]
                # Identify the node strictly by its exact numerical signature
                if comp.get("EMODnet") == 94.3 and comp.get("SubmarineMap") == 19.4:
                    # The 4-Line Update
                    comp["ITU_SCM_proxy"] = comp.pop("EMODnet")
                    comp["rule"] = "0.6*ITU_SCM_proxy + 0.4*SCM"
                    updated = True
            for v in node.values():
                patch_sau(v)
        elif isinstance(node, list):
            for item in node:
                patch_sau(item)

    patch_sau(data)

    if updated:
        # Generate the new v8.6 cryptographic seal
        json_string = json.dumps(data, sort_keys=True).encode('utf-8')
        new_sha = hashlib.sha256(json_string).hexdigest()
        
        # Append the new attestation if standard metadata exists
        if "metadata" in data:
            data["metadata"]["vintage"] = "v8.6"
            data["metadata"]["attestation_sha"] = new_sha
            data["metadata"]["updated_at"] = datetime.now(UTC).isoformat()
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print("\nSUCCESS: SAU provenance patched. v8.6 Index created.")
        print(f"NEW ATTESTATION SHA-256: {new_sha}\n")
    else:
        print("\nERROR: Could not find the exact SAU cse_components signature in the JSON.\n")

except FileNotFoundError:
    print(f"\nERROR: Could not find {input_path}. Ensure the 'data' folder exists in this directory.\n")