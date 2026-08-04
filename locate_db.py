# The 'os' library allows Python to interact with your Windows operating system
import os

# 1. Define ALL the project directories you mentioned to ensure we don't miss anything.
folders_to_search = [
    r'C:\Users\Lenovo\qesis-mcp',
    r'C:\Users\Lenovo\peeringdb_dump_20260210_221401',
    r'C:\Users\Lenovo\pdb',
    r'C:\Users\Lenovo\qesis-mcp-archive',
    r'C:\Users\Lenovo\sovereign-infra',
    r'C:\Users\Lenovo\OneDrive\Documents\INITIUM\Master IR & GE\Final Master Thesis'
]

def find_databases():
    print("Initiating deep scan for database files (.sqlite or .db)...")
    print("Please wait a moment...")
    
    # Create an empty list to store the results
    found_databases = []
    
    # 2. Iterate through each of the main ecosystem folders
    for folder in folders_to_search:
        # Check if the folder actually exists on your computer
        if os.path.exists(folder):
            # os.walk() acts as a crawler, going through the folder and all its sub-folders
            for root, subfolders, files in os.walk(folder):
                for file in files:
                    # 3. If a file ends with the standard database extensions, we grab its path
                    if file.endswith('.sqlite') or file.endswith('.db'):
                        full_path = os.path.join(root, file)
                        found_databases.append(full_path)
                        
    # 4. Present the results clearly to the user
    if len(found_databases) > 0:
        print(f"\n--- SUCCESS! Found {len(found_databases)} database(s): ---")
        for db in found_databases:
            print(f"-> {db}")
        print("\nPlease copy the correct database path so we can fix the headers!")
    else:
        print("\nNo database files were found in these directories.")

# Execute the main function
if __name__ == "__main__":
    find_databases()