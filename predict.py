import os
import shutil
import tarfile
import zipfile
import mimetypes
import json
from PIL import Image
from typing import List, Optional
from cog import BasePredictor, Input, Path
from comfyui import ComfyUI
from weights_downloader import WeightsDownloader
from cog_model_helpers import optimise_images
from config import config
import requests


os.environ["DOWNLOAD_LATEST_WEIGHTS_MANIFEST"] = "true"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("video/webm", ".webm")

OUTPUT_DIR = "/tmp/outputs"
INPUT_DIR = "/tmp/inputs"
COMFYUI_TEMP_OUTPUT_DIR = "ComfyUI/temp"
ALL_DIRECTORIES = [OUTPUT_DIR, INPUT_DIR, COMFYUI_TEMP_OUTPUT_DIR]

IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".webp"]
VIDEO_TYPES = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

# Load WAN2.2 workflow as default
with open("workflow/workflow-wan22-wan21 (1).json", "r") as file:
    WAN22_WORKFLOW_JSON = file.read()

# Keep original as fallback
with open("examples/api_workflows/birefnet_api.json", "r") as file:
    EXAMPLE_WORKFLOW_JSON = file.read()


class Predictor(BasePredictor):
    def setup(self, weights: str):
        # Install custom nodes on first startup
        import subprocess

        if not os.path.exists("ComfyUI/custom_nodes/ComfyUI-GGUF"):
            print("🔧 Installing custom nodes...")
            subprocess.run(["python", "scripts/install_custom_nodes.py"], check=True)
            print("✅ Custom nodes installed")

        print("🔄 Initializing ComfyUI...")

        # Initialize ComfyUI client and start server
        self.comfyUI = ComfyUI("127.0.0.1:8188")
        print("✅ ComfyUI client initialized")

        # Start the ComfyUI server
        print("🚀 Starting ComfyUI server...")
        self.comfyUI.start_server(OUTPUT_DIR, INPUT_DIR)
        print("✅ ComfyUI server started")

        print("✅ ComfyUI setup complete")

        if bool(weights):
            self.handle_user_weights(weights)

    def handle_user_weights(self, weights: str):
        if hasattr(weights, "url"):
            if weights.url.startswith("http"):
                weights_url = weights.url
            else:
                weights_url = "https://replicate.delivery/" + weights.url
        else:
            weights_url = weights

        print(f"Downloading user weights from: {weights_url}")
        WeightsDownloader.download(
            "weights.tar", weights_url, config["USER_WEIGHTS_PATH"]
        )
        for item in os.listdir(config["USER_WEIGHTS_PATH"]):
            source = os.path.join(config["USER_WEIGHTS_PATH"], item)
            destination = os.path.join(config["MODELS_PATH"], item)
            if os.path.isdir(source):
                if not os.path.exists(destination):
                    print(f"Moving {source} to {destination}")
                    shutil.move(source, destination)
                else:
                    for root, _, files in os.walk(source):
                        for file in files:
                            if not os.path.exists(os.path.join(destination, file)):
                                print(f"Moving {os.path.join(root, file)}")
                                shutil.move(
                                    os.path.join(root, file),
                                    os.path.join(destination, file),
                                )
            else:
                if not os.path.exists(destination):
                    print(f"Moving {source} to {destination}")
                    shutil.move(source, destination)

    def filename_with_extension(self, input_file, prefix):
        extension = os.path.splitext(input_file.name)[1]
        return f"{prefix}{extension}"

    def handle_input_file(
        self,
        input_file: Path,
        filename: str = "image.png",
    ):
        shutil.copy(input_file, os.path.join(INPUT_DIR, filename))

    def predict(
        self,
        prompt: str = Input(
            description="Text prompt for video generation (only used with default WAN2.2 workflow)",
            default="A baby dressed in a fluffy outfit is gently nose-to-nose with a small kitten. The background is softly blurred, highlighting the tender interaction between them.",
        ),
        workflow_json: str = Input(
            description="Your ComfyUI workflow as JSON string or URL. Default: WAN2.2 text-to-video workflow.",
            default="",
        ),
        input_file: Path = Input(
            description="Input file (image or video) for workflows that require media input",
            default=None,
        ),
        return_temp_files: bool = Input(
            description="Return temporary files created during processing. Useful for debugging.",
            default=False,
        ),
        output_format: str = optimise_images.predict_output_format(),
        output_quality: int = optimise_images.predict_output_quality(),
        randomise_seeds: bool = Input(
            description="Automatically randomise seeds (seed, noise_seed, rand_seed)",
            default=True,
        ),
        force_reset_cache: bool = Input(
            description="Force reset the ComfyUI cache before running the workflow. Useful for debugging.",
            default=False,
        ),
    ) -> List[Path]:
        """Run a single prediction on the model"""
        self.comfyUI.cleanup(ALL_DIRECTORIES)

        if input_file:
            self.handle_input_file(input_file)

        workflow_json_content = workflow_json
        if workflow_json.startswith(("http://", "https://")):
            try:
                response = requests.get(workflow_json)
                response.raise_for_status()
                workflow_json_content = response.text
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to download workflow JSON from URL: {e}")

        # Check if we're using the default workflow (compare content, not just existence)
        default_wf_content = WAN22_WORKFLOW_JSON.strip()
        user_wf_content = (workflow_json_content or "").strip()
        using_default_workflow = (
            not workflow_json_content or user_wf_content == default_wf_content
        )

        print(f"Using default WAN2.2 workflow: {using_default_workflow}")
        print(f"User prompt: {prompt}")
        print(
            f"Workflow content length - Default: {len(default_wf_content)}, User: {len(user_wf_content)}"
        )

        wf = self.comfyUI.load_workflow(workflow_json_content or WAN22_WORKFLOW_JSON)

        # If using default WAN2.2 workflow, always replace the prompt with user input
        if using_default_workflow:
            if "6" in wf and "inputs" in wf["6"] and "text" in wf["6"]["inputs"]:
                original_prompt = wf["6"]["inputs"]["text"]
                wf["6"]["inputs"]["text"] = prompt
                print(f"Replaced prompt: '{original_prompt}' -> '{prompt}'")
            else:
                print("Warning: Could not find prompt node '6' in workflow to replace")
                print(f"Available nodes: {list(wf.keys())}")
                # Try to find any CLIPTextEncode node
                for node_id, node_data in wf.items():
                    if node_data.get(
                        "class_type"
                    ) == "CLIPTextEncode" and "text" in node_data.get("inputs", {}):
                        wf[node_id]["inputs"]["text"] = prompt
                        print(
                            f"Found and updated CLIPTextEncode node '{node_id}' with prompt: {prompt}"
                        )
                        break

        self.comfyUI.connect()

        if force_reset_cache or not randomise_seeds:
            self.comfyUI.reset_execution_cache()

        if randomise_seeds:
            self.comfyUI.randomise_seeds(wf)

        self.comfyUI.run_workflow(wf)

        output_directories = [OUTPUT_DIR]
        if return_temp_files:
            output_directories.append(COMFYUI_TEMP_OUTPUT_DIR)

        optimised_files = optimise_images.optimise_image_files(
            output_format, output_quality, self.comfyUI.get_files(output_directories)
        )
        return [Path(p) for p in optimised_files]
