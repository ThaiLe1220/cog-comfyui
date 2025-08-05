# WAN2.2 Text-to-Video ComfyUI Pipeline

> **🍴 This is a modified fork of [replicate/cog-comfyui](https://github.com/replicate/cog-comfyui)**  
> **🎬 Specialized for WAN2.2 text-to-video generation with optimized GGUF models, LoRA enhancements, and production-ready post-processing**

## What's Different in This Fork

This repository has been extensively modified to provide a complete **WAN2.2 text-to-video generation pipeline**:

### ✨ **Key Features**
- **Two-Stage GGUF Models**: High-noise + Low-noise Q4_K_M quantization for memory efficiency
- **LoRA Enhancements**: LightX2V (speed) + FusionX (quality) optimization layers  
- **Complete Post-Processing**: RealESRGAN 2x upscaling + RIFE 2x frame interpolation
- **Production Ready**: 768x1408 MP4 output, 82 frames, ~10 seconds

### 🔧 **Technical Improvements**
- Pre-downloaded models cached in Docker layers (20+ minute build time → 3 seconds)
- Fixed websocket dependencies and custom node compatibility
- Robust ComfyUI initialization with fallback patterns
- Comprehensive model verification system

### 🎯 **Default Workflow**
- **Input**: Text prompt (e.g., "A baby with a kitten in soft lighting")
- **Output**: High-quality MP4 video (768x1408, 8fps, production-ready)
- **Pipeline**: Two-stage generation → VAE decode → upscale → interpolate → export

---

## Quick Start

### Option 1: Use the Pre-built Model
Deploy directly on Replicate using the pre-configured WAN2.2 pipeline:
```bash
# Deploy to your Replicate account
cog push r8.im/your-username/wan22-t2v
```

### Option 2: Run Locally
```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/your-username/cog-comfyui.git
cd cog-comfyui

# Install custom nodes
./scripts/install_custom_nodes.py

# Test the pipeline
cog predict -i prompt="A serene lake at sunset with gentle ripples"
```

---

## Original cog-comfyui Documentation

*The following sections are from the original [replicate/cog-comfyui](https://github.com/replicate/cog-comfyui) template:*

You have 3 choices:

1. Create a private deployment (simplest, but you'll need to pay for setup and idle time)
2. Create and deploy a fork using Cog (most powerful but most complex)
3. Create a new model from the train tab (simple, your model can be public or private and you can bring your own weights)

### 1. Create a private deployment

Go to:

https://replicate.com/deployments/create

Select `fofr/any-comfyui-workflow` as the model you'd like to deploy. Pick your hardware and min and max instances, and you're ready to go. You'll be pinned to the version you deploy from. When `any-comfyui-workflow` is updated, you can test your workflow with it, and then deploy again using the new version.

You can read more about deployments in the Replicate docs:

https://replicate.com/docs/deployments

### 2. Create and deploy a fork using Cog

You can use this repository as a template to create your own model. This gives you complete control over the ComfyUI version, custom nodes, and the API you'll use to run the model.

You'll need to be familiar with Python, and you'll also need a GPU to push your model using [Cog](https://cog.run). Replicate has a good getting started guide: https://replicate.com/docs/guides/push-a-model

#### Example

The `kolors` model on Replicate is a good example to follow:

- https://replicate.com/fofr/kolors (The model with it's customised API)
- https://github.com/replicate/cog-comfyui-kolors (The new repo)

It was created from this repo, and then deployed using Cog. You can step through the commits of that repo to see what was changed and how, but broadly:

- this repository is used as a template
- the script [`scripts/prepare_template.py`](https://github.com/replicate/cog-comfyui/blob/main/scripts/prepare_template.py) is run first, to remove examples and unnecessary boilerplate
- `custom_nodes.json` is modified to add or remove custom nodes you need, making sure to also add or remove their dependencies from `cog.yaml`
- run `./scripts/install_custom_nodes.py` to install the custom nodes (or `./scripts/reset.py` to reinstall ComfyUI and all custom nodes)
- the workflow is added as `workflow_api.json`
- `predict.py` is updated with a new API and the `update_workflow` method is changed so that it modifies the right parts of the JSON
- the model is tested using `cog predict -i option_name=option_value -i another_option_name=another_option_value` on a GPU
- the model is pushed to Replicate using `cog push r8.im/your-username/your-model-name`

### 3. Create a new model from the train tab

Visit the train tab on Replicate:

https://replicate.com/fofr/any-comfyui-workflow/train

Here you can give public or private URLs to weights on HuggingFace and CivitAI. If URLs are private or need authentication, make sure to include an API key or access token.

Check the training logs to see what filenames to use in your workflow JSON.

---

## Developing locally

Clone this repository:

```sh
git clone --recurse-submodules https://github.com/replicate/cog-comfyui.git
```

Run the [following script](https://github.com/replicate/cog-comfyui/blob/main/scripts/install_custom_nodes.py) to install all the custom nodes:

```sh
./scripts/install_custom_nodes.py
```

You can view the list of nodes in [custom_nodes.json](https://github.com/replicate/cog-comfyui/blob/main/custom_nodes.json)

### Running the Web UI from your Cog container

1. **GPU Machine**: Start the Cog container and expose port 8188:
```sh
sudo cog run -p 8188 bash
```
Running this command starts up the Cog container and let's you access it

2. **Inside Cog Container**: Now that we have access to the Cog container, we start the server, binding to all network interfaces:
```sh
cd ComfyUI/
python main.py --listen 0.0.0.0
```

3. **Local Machine**: Access the server using the GPU machine's IP and the exposed port (8188):
`http://<gpu-machines-ip>:8188`

When you goto `http://<gpu-machines-ip>:8188` you'll see the classic ComfyUI web form!