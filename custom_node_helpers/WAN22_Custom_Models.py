from custom_node_helper import CustomNodeHelper
import os
import requests
from urllib.parse import urlparse

class WAN22_Custom_Models(CustomNodeHelper):
    """
    Custom helper to download WAN2.2 GGUF models and associated weights
    """
    
    # Define all models we need to download
    MODELS_TO_DOWNLOAD = [
        {
            "url": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/HighNoise/Wan2.2-T2V-A14B-HighNoise-Q2_K.gguf",
            "dest": "ComfyUI/models/unet/Wan2.2-T2V-A14B-HighNoise-Q2_K.gguf",
            "name": "WAN2.2 High Noise GGUF"
        },
        {
            "url": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/LowNoise/Wan2.2-T2V-A14B-LowNoise-Q2_K.gguf", 
            "dest": "ComfyUI/models/unet/Wan2.2-T2V-A14B-LowNoise-Q2_K.gguf",
            "name": "WAN2.2 Low Noise GGUF"
        },
        {
            "url": "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
            "dest": "ComfyUI/models/loras/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
            "name": "LightX2V LoRA"
        },
        {
            "url": "https://huggingface.co/vrgamedevgirl84/Wan14BT2VFusioniX/resolve/main/FusionX_LoRa/Wan2.1_T2V_14B_FusionX_LoRA.safetensors",
            "dest": "ComfyUI/models/loras/Wan2.1_T2V_14B_FusionX_LoRA.safetensors", 
            "name": "FusionX LoRA"
        },
        {
            "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
            "dest": "ComfyUI/models/vae/wan_2.1_vae.safetensors",
            "name": "WAN2.1 VAE"
        },
        {
            "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            "dest": "ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            "name": "UMT5 Text Encoder"
        },
        {
            "url": "https://huggingface.co/ai-forever/Real-ESRGAN/resolve/a86fc6182b4650b4459cb1ddcb0a0d1ec86bf3b0/RealESRGAN_x2.pth",
            "dest": "ComfyUI/models/upscale_models/RealESRGAN_x2.pth",
            "name": "Real-ESRGAN x2"
        }
    ]
    
    @staticmethod
    def prepare(**kwargs):
        """
        Download all WAN2.2 models if they don't exist
        This runs before ComfyUI server starts
        """
        print("🚀 Checking WAN2.2 custom models...")
        
        for model_info in WAN22_Custom_Models.MODELS_TO_DOWNLOAD:
            if not os.path.exists(model_info["dest"]):
                print(f"📥 Downloading {model_info['name']}...")
                WAN22_Custom_Models.download_model(
                    model_info["url"], 
                    model_info["dest"],
                    model_info["name"]
                )
            else:
                print(f"✅ {model_info['name']} already exists")
        
        print("🎉 All WAN2.2 custom models ready!")
    
    @staticmethod
    def download_model(url, dest_path, name):
        """
        Download a model from URL to destination path
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Download with streaming for large files
            print(f"   Downloading from: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress indicator for large files
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024 * 50) == 0:  # Every 50MB
                                print(f"   Progress: {percent:.1f}% ({downloaded // (1024*1024)}MB/{total_size // (1024*1024)}MB)")
            
            print(f"✅ Downloaded {name} to {dest_path}")
            
        except Exception as e:
            print(f"❌ Error downloading {name}: {e}")
            # Remove partial file if it exists
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise
    
    @staticmethod
    def add_weights(weights_to_download, node):
        """
        Add weights based on node requirements
        This is called during workflow processing
        """
        # Check if node uses any of our custom models
        # Node is a Node object, use the type() method to get class_type
        try:
            node_class = node.type()
        except:
            # Fallback in case of any issues
            node_class = ''
        
        # If it's a GGUF loader node, no additional action needed
        # The models are already downloaded in prepare()
        if 'GGUF' in node_class or 'Unet' in node_class:
            # Models are already handled by prepare()
            pass
    
    @staticmethod
    def check_for_unsupported_nodes(node):
        """
        Check for any unsupported node configurations
        """
        # No specific checks needed for our models
        pass