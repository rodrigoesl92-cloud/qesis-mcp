# The 'os' library helps us handle file paths safely on Windows
import os

# 1. Define the exact path to your lessons ledger inside the qesis-mcp folder
ledger_path = r'C:\Users\Lenovo\qesis-mcp\ops\LESSONS_LEDGER.md'

def update_memory_ledger():
    print("ARCHITECT Agent: Appending today's execution to the memory ledger...")
    
    # 2. This is the exact text we are appending to the ledger.
    # The triple quotes (""") allow us to write multiple lines of text easily.
    ledger_entry = """
L-068 · 2026-08-03 · Gemini deployed prompt -> Rule: All agents must validate data pipelines.
- [SCOUT/COUNSEL]: Missing license audit generated for 45 documents.
- [ANALYST]: Promoted Row 1 headers across 32 data warehouse tables.
- [ARCHITECT]: Formatted STIR dashboard HTML and resolved design system violations.
- [HUMAN-IN-THE-LOOP]: Rotated ENTSO-E keys and deployed GCP Vault.
"""
    try:
        # Ensure the 'ops' directory exists just in case it was accidentally deleted
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        
        # 3. We open the file in 'a' (append) mode. 
        # Append mode is critical! It adds to the end of the file without deleting the old memory.
        with open(ledger_path, 'a', encoding='utf-8') as file:
            file.write(ledger_entry)
            
        print("Success: System memory updated! The ecosystem will now remember this execution.")
        
    except Exception as e:
        # If anything goes wrong, print the exact error
        print(f"Error updating the ledger: {e}")

# This line ensures the script runs the function when called from PowerShell
if __name__ == "__main__":
    update_memory_ledger()