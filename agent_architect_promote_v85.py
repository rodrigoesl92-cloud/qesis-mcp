# 'json' allows us to read structured data files, 'os' handles file paths
import json
import os

# 1. UPDATED PATH: We now point exactly to where the detective script found the file
json_path = r'C:\Users\Lenovo\sovereign-infra\ops\analysis\D-103_fsqca_rerun.json'
lineage_path = r'C:\Users\Lenovo\qesis-mcp\ops\VINTAGE_LINEAGE.md'

def promote_v85_candidate():
    print("ARCHITECT Agent: Fetching D-103 fsQCA rerun data for human verification...")
    
    # 2. Check if the JSON file actually exists
    if not os.path.exists(json_path):
        print(f"Error: The analysis file was not found at {json_path}")
        return
        
    # 3. Read and display the JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print("\n--- JSON Data Preview ---")
            
            # We use json.dumps with 'indent=4' to make the data highly readable
            # We only print the first 1000 characters so we don't flood your screen
            formatted_data = json.dumps(data, indent=4)
            print(formatted_data[:1000])
            print("\n... (data truncated for terminal readability) ...")
            print("-------------------------\n")
            
    except Exception as e:
        print(f"Error reading the JSON file: {e}")
        return
        
    # 4. Human-in-the-Loop (Article 14) Verification
    # The script pauses here and waits for your keyboard input
    print("HUMAN-IN-THE-LOOP GATE: Article 14 Compliance")
    approval = input("Does the math look valid? Approve promotion to Canonical v8.5? (y/n): ")
    
    # 5. Process the decision
    if approval.strip().lower() == 'y':
        # Create the registry entry
        lineage_entry = "\n- VINTAGE BUMP: v8.5 · D-103 fsQCA Rerun verified. Promoted to canonical.\n"
        
        try:
            # Ensure the directory exists, then append the record
            os.makedirs(os.path.dirname(lineage_path), exist_ok=True)
            with open(lineage_path, 'a', encoding='utf-8') as lineage_file:
                lineage_file.write(lineage_entry)
            
            print("\nSUCCESS: VINTAGE_LINEAGE.md has been updated.")
            print("Phase 2 complete. Welcome to Phase 3: Infrastructure Digital Twin.")
        except Exception as e:
            print(f"Error updating the lineage file: {e}")
    else:
        # If you type anything other than 'y', it safely aborts
        print("\nPromotion aborted by operator. Standing by.")

# Run the function
if __name__ == "__main__":
    promote_v85_candidate()