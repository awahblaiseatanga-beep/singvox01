import sys
import subprocess

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_and_import('PyPDF2')

import PyPDF2

pdf_path = r"d:\Singvox\Singvox\.agents\skills\blender-rig-audit\references\SignVox_Blender_From_First_Principles_Research_Guide.pdf"

try:
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"\n\n--- PAGE {i+1} ---\n\n"
            text += page.extract_text()
            
    with open(r"d:\Singvox\Singvox\tools\extracted_guide.txt", "w", encoding="utf-8") as out:
        out.write(text)
        
    print("PDF SUCCESSFULLY EXTRACTED")
except Exception as e:
    print(f"PDF EXTRACTION FAILED: {e}")
