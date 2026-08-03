# The 're' library allows us to use Regular Expressions for advanced text searching
import re
import os

# 1. Define the exact path to your dashboard HTML file
html_path = r'C:\Users\Lenovo\qesis-mcp\STIR_Governance_Dashboard.html'

def format_dashboard_html():
    print("ARCHITECT Agent initiating HTML formatting...")
    
    # Verify the file exists before we attempt to edit it
    if not os.path.exists(html_path):
        print(f"Critical Error: The file was not found at {html_path}")
        print("Please check if the file is in a different folder.")
        return

    try:
        # 2. Open and read the original HTML content
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            
        # 3. Replace all em dashes (—) with standard hyphens (-)
        html_content = html_content.replace('—', '-')
        
        # 4. Wrap <canvas> tags inside <div class="chart__canvas">
        # This Regex pattern captures the opening tag, everything inside it, and the closing tag
        canvas_pattern = r'(<canvas.*?</canvas>)'
        replacement_wrapper = r'<div class="chart__canvas">\1</div>'
        
        # Apply the Regex replacement to the entire HTML document
        new_html_content = re.sub(canvas_pattern, replacement_wrapper, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # 5. Write the corrected HTML back to the file
        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(new_html_content)
            
        print("-" * 40)
        print("Operation complete! HTML formatting applied successfully.")
        print("- Em dashes removed.")
        print("- Canvas elements wrapped in .chart__canvas containers.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Execute the function when the script is run
if __name__ == "__main__":
    format_dashboard_html()