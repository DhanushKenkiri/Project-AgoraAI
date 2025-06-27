# This script creates a Lambda layer for your dependencies
import os
import subprocess
import zipfile

# Create directories for the layer
os.makedirs("layer/python", exist_ok=True)

# Install dependencies into the layer directory
subprocess.check_call(
    f"pip install -r requirements.txt -t layer/python",
    shell=True
)

# Create a zip file of the layer
with zipfile.ZipFile("layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("layer"):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(
                file_path, 
                os.path.relpath(file_path, "layer")
            )

print("Created layer.zip - upload this as a Lambda layer and attach it to your function")
