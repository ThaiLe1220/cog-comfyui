import subprocess
import time
import os
from weights_manifest import WeightsManifest


class WeightsDownloader:
    supported_filetypes = [
        ".ckpt",
        ".safetensors",
        ".sft",
        ".pt",
        ".pth",
        ".bin",
        ".onnx",
        ".torchscript",
        ".engine",
        ".patch",
    ]

    def __init__(self):
        self.weights_manifest = WeightsManifest()
        self.weights_map = self.weights_manifest.weights_map

    def get_canonical_weight_str(self, weight_str):
        return self.weights_manifest.get_canonical_weight_str(weight_str)

    def get_weights_by_type(self, type):
        return self.weights_manifest.get_weights_by_type(type)

    def download_weights(self, weight_str):
        print(f"🔽 download_weights() called with: {weight_str}")

        # Priority 1: Check if file already exists in ComfyUI models directory (pre-downloaded via cog.yaml)
        if self.check_pre_downloaded_file(weight_str):
            print(f"✅ {weight_str} found pre-downloaded, skipping weights system")
            return

        # Priority 1.5: Special handling for known pre-downloaded Wan2.2 models
        wan22_predownloaded_models = [
            "lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
            "Wan2.1_T2V_14B_FusionX_LoRA.safetensors",
            "RealESRGAN_x2.pth",
            "rife47.pth",
            "wan_2.1_vae.safetensors",
        ]

        if weight_str in wan22_predownloaded_models:
            print(
                f"🎯 {weight_str} is a known pre-downloaded Wan2.2 model, assuming it exists"
            )
            return

        # Priority 2: Handle direct URLs from synonyms (e.g., HuggingFace URLs converted from model names)
        if weight_str.startswith(("http://", "https://")):
            self._download_from_url(weight_str)
            return

        # Priority 3: Use Replicate weights system for supported models
        print(f"🔍 Checking if {weight_str} exists in weights_map...")
        if weight_str in self.weights_map:
            self._download_from_weights_map(weight_str)
        else:
            raise ValueError(
                f"{weight_str} unavailable. For unsupported models, pre-download via cog.yaml. "
                f"Supported weights: https://github.com/replicate/cog-comfyui/blob/main/supported_weights.md"
            )

    def _download_from_url(self, url):
        """Download directly from URL with smart destination detection"""
        print(f"🌐 Detected URL, downloading directly: {url}")
        filename = url.split("/")[-1]
        dest_dir = self.determine_dest_from_url(url)
        dest_file = os.path.join(dest_dir, filename)
        print(f"📁 File: {filename} → {dest_dir}")

        os.makedirs(dest_dir, exist_ok=True)
        print(f"⏳ Downloading {filename} to {dest_dir}")
        start = time.time()
        subprocess.check_call(["curl", "-L", "-o", dest_file, url], close_fds=False)

        elapsed_time = time.time() - start
        file_size_bytes = os.path.getsize(dest_file)
        file_size_megabytes = file_size_bytes / (1024 * 1024)
        print(
            f"✅ {filename} downloaded to {dest_dir} in {elapsed_time:.2f}s, size: {file_size_megabytes:.2f}MB"
        )

    def _download_from_weights_map(self, weight_str):
        """Download from Replicate weights system"""
        if self.weights_manifest.is_non_commercial_only(weight_str):
            print(
                f"⚠️  {weight_str} is for non-commercial use only. Unless you have obtained a commercial license."
            )

        if isinstance(self.weights_map[weight_str], list):
            for weight in self.weights_map[weight_str]:
                self.download_if_not_exists(weight_str, weight["url"], weight["dest"])
        else:
            self.download_if_not_exists(
                weight_str,
                self.weights_map[weight_str]["url"],
                self.weights_map[weight_str]["dest"],
            )

    def check_pre_downloaded_file(self, weight_str):
        """Check if file exists in ComfyUI models directories (pre-downloaded via cog.yaml)"""
        print(f"🔍 Checking pre-downloaded file: {weight_str}")
        model_paths = [
            "/src/ComfyUI/models/unet",
            "/src/ComfyUI/models/loras",
            "/src/ComfyUI/models/text_encoders",
            "/src/ComfyUI/models/vae",
            "/src/ComfyUI/models/checkpoints",
            "/src/ComfyUI/models/diffusion_models",
            "/src/ComfyUI/models/clip",
            "/src/ComfyUI/models/upscale_models",
        ]

        for path in model_paths:
            full_path = os.path.join(path, weight_str)
            print(f"  📁 Checking: {full_path}")

            # Check if file exists
            if os.path.exists(full_path):
                print(f"  ✅ Found at: {full_path}")
                return True

            # Additional debug: list directory contents to see what's actually there
            if os.path.exists(path):
                try:
                    files_in_dir = os.listdir(path)
                    matching_files = [f for f in files_in_dir if weight_str in f]
                    if matching_files:
                        print(f"  📋 Similar files in {path}: {matching_files}")
                        # Check for exact match with case-insensitive comparison
                        for file in files_in_dir:
                            if file.lower() == weight_str.lower():
                                actual_path = os.path.join(path, file)
                                print(
                                    f"  ✅ Found case-insensitive match: {actual_path}"
                                )
                                return True
                except PermissionError:
                    print(f"  ⚠️ Permission denied accessing {path}")
                except Exception as e:
                    print(f"  ⚠️ Error reading {path}: {e}")

        print(f"  ❌ Not found in any model directory")
        return False

    def determine_dest_from_url(self, url):
        """Determine destination directory based on URL path"""
        print(f"🎯 Determining destination for URL: {url}")

        if "/text_encoders/" in url or "/text_encoder/" in url:
            dest = "/src/ComfyUI/models/text_encoders"
        elif "/unet/" in url:
            dest = "/src/ComfyUI/models/unet"
        elif "/vae/" in url:
            dest = "/src/ComfyUI/models/vae"
        elif "/loras/" in url or "/lora/" in url:
            dest = "/src/ComfyUI/models/loras"
        elif "/clip/" in url:
            dest = "/src/ComfyUI/models/clip"
        else:
            # Default fallback
            dest = "/src/ComfyUI/models/checkpoints"

        print(f"  📁 Destination: {dest}")
        return dest

    def check_if_file_exists(self, weight_str, dest):
        if dest.endswith(weight_str):
            path_string = dest
        else:
            path_string = os.path.join(dest, weight_str)
        return os.path.exists(path_string)

    def download_if_not_exists(self, weight_str, url, dest):
        if self.check_if_file_exists(weight_str, dest):
            print(f"✅ {weight_str} exists in {dest}")
            return
        WeightsDownloader.download(weight_str, url, dest)

    @staticmethod
    def download(weight_str, url, dest):
        if "/" in weight_str:
            subfolder = weight_str.rsplit("/", 1)[0]
            dest = os.path.join(dest, subfolder)
            os.makedirs(dest, exist_ok=True)

        print(f"⏳ Downloading {weight_str} to {dest}")
        start = time.time()

        # Check if URL points to archive or raw file
        if url.endswith((".tar", ".zip", ".tar.gz", ".tar.bz2")):
            # Archive file - use extraction flags
            subprocess.check_call(
                ["pget", "--log-level", "warn", "-xf", url, dest], close_fds=False
            )
        else:
            # Raw file - no extraction
            subprocess.check_call(
                ["pget", "--log-level", "warn", url, dest], close_fds=False
            )
        elapsed_time = time.time() - start
        try:
            file_size_bytes = os.path.getsize(
                os.path.join(dest, os.path.basename(weight_str))
            )
            file_size_megabytes = file_size_bytes / (1024 * 1024)
            print(
                f"✅ {weight_str} downloaded to {dest} in {elapsed_time:.2f}s, size: {file_size_megabytes:.2f}MB"
            )
        except FileNotFoundError:
            print(f"✅ {weight_str} downloaded to {dest} in {elapsed_time:.2f}s")

    def delete_weights(self, weight_str):
        if weight_str in self.weights_map:
            weight_path = os.path.join(self.weights_map[weight_str]["dest"], weight_str)
            if os.path.exists(weight_path):
                os.remove(weight_path)
                print(f"Deleted {weight_path}")
