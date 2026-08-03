# The 'os' library allows Python to navigate your Windows file system
import os

# 1. We list all the main folders in your ecosystem to ensure a thorough search
folders_to_search = [
    r'C:\Users\Lenovo\qesis-mcp',
    r'C:\Users\Lenovo\peeringdb_dump_20260210_221401',
    r'C:\Users\Lenovo\pdb',
    r'C:\Users\Lenovo\qesis-mcp-archive',
    r'C:\Users\Lenovo\sovereign-infra',
    r'C:\Users\Lenovo\OneDrive\Documents\INITIUM\Master IR & GE\Final Master Thesis'
]

def find_analysis_file():
    print("Initiating search for D-103_fsqca_rerun.json...")
    
    # The exact name of the file we are looking for
    target_file = 'D-103_fsqca_rerun.json'
    found_paths = []
    
    # 2. Iterate through each of the main project folders
    for folder in folders_to_search:
        # Check if the folder exists on your computer
        if os.path.exists(folder):
            # os.walk crawls through the folder and all of its sub-folders
            for root, subfolders, files in os.walk(folder):
                # 3. If the file is in the current folder, save its full path
                if target_file in files:
                    full_path = os.path.join(root, target_file)
                    found_paths.append(full_path)
                    
    # 4. Display the results clearly in the terminal
    if len(found_paths) > 0:
        print(f"\n--- SUCCESS! Found the file at: ---")
        for path in found_paths:
            print(f"-> {path}")
        print("\nPlease copy this path so we can update our verification script!")
    else:
        print("\nError: The file was not found in any of the ecosystem folders.")
        print("Is it possible the file hasn't been downloaded or generated yet?")

# Execute the search function
if __name__ == "__main__":
    find_analysis_file()