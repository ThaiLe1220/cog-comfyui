#!/usr/bin/env python3
import os
import glob

print("🔍 === DEBUGGING MODEL FILE LOCATIONS ===")

# Define expected model files and their correct directories
expected_files = {
    "GGUF Models": {
        "directory": "/src/ComfyUI/models/unet/",
        "files": [
            "Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf",
            "Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf",
        ],
    },
    "LoRA Models": {
        "directory": "/src/ComfyUI/models/loras/",
        "files": [
            "lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
            "Wan2.1_T2V_14B_FusionX_LoRA.safetensors",
        ],
    },
    "VAE Model": {
        "directory": "/src/ComfyUI/models/vae/",
        "files": ["wan_2.1_vae.safetensors"],
    },
    "Text Encoder": {
        "directory": "/src/ComfyUI/models/text_encoders/",
        "files": ["umt5_xxl_fp8_e4m3fn_scaled.safetensors"],
    },
    "Upscaler": {
        "directory": "/src/ComfyUI/models/upscale_models/",
        "files": ["RealESRGAN_x2.pth"],
    },
    "RIFE": {
        "directory": "/src/ComfyUI/models/animatediff_models/",
        "files": ["rife47.pth"],
    },
}

# All ComfyUI model directories to search
all_model_dirs = [
    "/src/ComfyUI/models/unet/",
    "/src/ComfyUI/models/loras/",
    "/src/ComfyUI/models/vae/",
    "/src/ComfyUI/models/text_encoders/",
    "/src/ComfyUI/models/upscale_models/",
    "/src/ComfyUI/models/animatediff_models/",
    "/src/ComfyUI/models/checkpoints/",
    "/src/ComfyUI/models/clip/",
    "/src/ComfyUI/models/controlnet/",
    "/src/ComfyUI/models/diffusion_models/",
]

print("1. 📁 CHECKING EXPECTED LOCATIONS")
print("=" * 50)

for category, info in expected_files.items():
    print(f"\n{category}:")
    directory = info["directory"]

    if os.path.exists(directory):
        print(f"  ✅ Directory exists: {directory}")
        actual_files = os.listdir(directory)

        for expected_file in info["files"]:
            if expected_file in actual_files:
                file_path = os.path.join(directory, expected_file)
                size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                print(f"  ✅ Found: {expected_file} ({size:.1f} MB)")
            else:
                print(f"  ❌ Missing: {expected_file}")

        if actual_files:
            print(f"  📋 All files in {directory}:")
            for file in actual_files:
                print(f"      - {file}")
        else:
            print(f"  📋 Directory is empty")
    else:
        print(f"  ❌ Directory missing: {directory}")

print("\n\n2. 🔍 SEARCHING FOR MODELS IN ALL DIRECTORIES")
print("=" * 50)

# Create a list of all expected model files
all_expected_files = []
for info in expected_files.values():
    all_expected_files.extend(info["files"])

for model_file in all_expected_files:
    print(f"\nSearching for: {model_file}")
    found_locations = []

    for directory in all_model_dirs:
        if os.path.exists(directory):
            full_path = os.path.join(directory, model_file)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path) / (1024 * 1024)  # Size in MB
                found_locations.append(f"{directory} ({size:.1f} MB)")

    if found_locations:
        for location in found_locations:
            print(f"  ✅ Found at: {location}")
    else:
        print(f"  ❌ Not found in any ComfyUI model directory")

print("\n\n3. 📊 DIRECTORY CONTENTS SUMMARY")
print("=" * 50)

for directory in all_model_dirs:
    if os.path.exists(directory):
        files = os.listdir(directory)
        if files:
            print(f"\n{directory} ({len(files)} files):")
            for file in sorted(files):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    print(f"  - {file} ({size:.1f} MB)")
        else:
            print(f"\n{directory}: (empty)")
    else:
        print(f"\n{directory}: (does not exist)")

print("\n🔍 === DEBUG COMPLETE ===")
