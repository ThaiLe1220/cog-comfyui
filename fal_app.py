import fal
from fal.container import ContainerImage
from pathlib import Path

PWD = Path(__file__).resolve().parent


class SimpleComfyUIApp(
    fal.App,
    kind="container",
    image=ContainerImage.from_dockerfile(f"{PWD}/Dockerfile.fal"),
    machine_type="fal-ai/h100-40gb",
):
    def setup(self):
        """Initialize the app"""
        print("🚀 ComfyUI app starting up...")

        # Test that everything is working
        import sys

        sys.path.append("/src")
        from comfyui import ComfyUI

        print("✅ ComfyUI imported successfully")

        # Check custom nodes
        import os

        custom_nodes = os.listdir("/src/ComfyUI/custom_nodes")
        print(f"✅ Found {len(custom_nodes)} custom nodes")

        print("🎉 Setup complete!")

    @fal.endpoint("/test")
    def test_endpoint(self) -> dict:
        """Simple test endpoint"""
        return {
            "status": "success",
            "message": "ComfyUI is working on fal.ai!",
            "custom_nodes_count": len(os.listdir("/src/ComfyUI/custom_nodes")),
        }


# Create the app instance
app = SimpleComfyUIApp()
