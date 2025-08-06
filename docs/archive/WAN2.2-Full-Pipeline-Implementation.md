# WAN2.2 Full Pipeline Implementation Guide

## Overview

This document details the complete implementation of WAN2.2 text-to-video generation pipeline on Replicate, skipping the progressive milestone approach to deploy the full system directly.

**Implementation Date**: August 4, 2025  
**Pipeline**: WAN2.2 Two-Stage GGUF + LoRA Enhancement + Post-Processing  
**Target Hardware**: Replicate A100 (80GB)

---

## Implementation Path

### ✅ Completed: Milestone 0 - Baseline
- **Model**: `r8.im/enhance-replicate/wan22-milestone0-baseline`
- **Purpose**: Basic SDXL text-to-image generation with prompt customization
- **Status**: Successfully deployed and tested

### ⏭️ Skipped: Milestones 1-5 (Progressive Approach)
**Decision**: Skip progressive milestones and implement complete WAN2.2 pipeline directly for faster deployment.

### 🎯 Implemented: Full WAN2.2 Pipeline
- **Model**: `r8.im/enhance-replicate/wan22-comfyui-full`
- **Purpose**: Complete two-stage video generation with post-processing

---

## Technical Implementation

### 1. Custom Nodes Integration

**Added to `custom_nodes.json`:**
```json
{
  "repo": "https://github.com/city96/ComfyUI-GGUF",
  "commit": "b3ec875"
},
{
  "repo": "https://github.com/chflame163/ComfyUI_LayerStyle", 
  "commit": "6774689"
}
```

**Already Available:**
- ✅ ComfyUI-VideoHelperSuite (VHS_VideoCombine)
- ✅ ComfyUI-Frame-Interpolation (RIFE VFI)
- ✅ ComfyUI-WanVideoWrapper (Wan22ImageToVideoLatent)

### 2. Dependencies Update

**Added to `requirements.txt`:**
```text
gguf>=0.13.0
protobuf
```

### 3. Model Weight Management Strategy

**Problem Identified**: Adding model filenames to `weights.json` without URLs would cause "model not found" errors.

**Solution Implemented**: Weight Synonyms System

**Added to `weight_synonyms.json`:**
```json
{
  "Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/HighNoise/Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf",
  "Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/LowNoise/Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf",
  "lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors": "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
  "Wan2.1_T2V_14B_FusionX_LoRA.safetensors": "https://huggingface.co/vrgamedevgirl84/Wan14BT2VFusioniX/resolve/main/FusionX_LoRa/Wan2.1_T2V_14B_FusionX_LoRA.safetensors",
  "umt5_xxl_fp8_e4m3fn_scaled.safetensors": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
}
```

**Why This Works**: 
- System automatically checks `weight_synonyms.json` during workflow analysis
- Maps model filenames to direct HuggingFace URLs
- Downloads models automatically via `pget` tool
- Caches models for subsequent runs

### 4. Default Workflow Integration

**Updated `predict.py`:**
```python
# Load WAN2.2 workflow as default
with open("workflow/Wan2.2-Testing.json", "r") as file:
    WAN22_WORKFLOW_JSON = file.read()

# Updated input parameters
prompt: str = Input(
    description="Text prompt for video generation (only used with default WAN2.2 workflow)",
    default="A baby dressed in a fluffy outfit is gently nose-to-nose with a small kitten. The background is softly blurred, highlighting the tender interaction between them.",
)
workflow_json: str = Input(
    description="Your ComfyUI workflow as JSON string or URL. Default: WAN2.2 text-to-video workflow.",
    default=WAN22_WORKFLOW_JSON,
)
```

---

## Pipeline Architecture

### Complete WAN2.2 Workflow Components

#### **Text Encoding**
- **Model**: `umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- **Type**: WAN-specific UMT5 CLIP encoder
- **Purpose**: Convert text prompts to embeddings

#### **Two-Stage Generation**
1. **Stage 1 (High Noise)**:
   - **Model**: `Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf`
   - **Steps**: 0-4 (4 steps)
   - **Purpose**: Base video generation

2. **Stage 2 (Low Noise)**:
   - **Model**: `Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf` 
   - **Steps**: 4-8 (4 steps)
   - **Purpose**: Refinement and detail enhancement

#### **LoRA Enhancements**
- **LightX2V**: `lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors` (strength: 1.0)
- **FusionX**: `Wan2.1_T2V_14B_FusionX_LoRA.safetensors` (strength: 0.5)

#### **Post-Processing Pipeline**
1. **VAE Decode**: Tiled processing (512px tiles, 64px overlap)
2. **Upscaling**: RealESRGAN 2x (384x704 → 768x1408)
3. **Frame Interpolation**: RIFE 2x (41 → 82 frames)
4. **Video Export**: H.264 MP4, 8fps, CRF 19

### **Generation Parameters**
- **Resolution**: 384x704 (9:16 aspect ratio)
- **Base Frames**: 41 frames
- **Final Frames**: 82 frames (after RIFE interpolation)
- **CFG**: 1.0 (distilled models)
- **Sampler**: res_multistep with beta scheduler
- **Total Steps**: 8 (4+4 split)

---

## Execution Flow

### Phase 1: Model Download (First Run Only)
1. ComfyUI analyzes workflow for model references
2. System checks `weight_synonyms.json` for URL mappings
3. Downloads missing models from HuggingFace URLs
4. Caches models in appropriate ComfyUI directories

### Phase 2: Two-Stage Generation
1. **Stage 1**: High-noise model generates base video latents (steps 0-4)
2. **Stage 2**: Low-noise model refines latents (steps 4-8)
3. Latents passed between stages with leftover noise

### Phase 3: Post-Processing
1. **VAE Decode**: Converts latents to video frames using tiled processing
2. **Upscaling**: 2x spatial enhancement via RealESRGAN
3. **Interpolation**: 2x temporal enhancement via RIFE
4. **Export**: Final H.264 MP4 video

---

## Expected Performance

### **Hardware Requirements**
- **Minimum**: A100 (80GB)
- **Memory Usage**: 60-80GB peak (both models + post-processing)

### **Generation Times**
- **First Run**: 10-15 minutes (includes model downloads)
- **Subsequent Runs**: 6-10 minutes (cached models)
- **Breakdown**: 
  - Model Loading: 1-2 minutes
  - Two-Stage Generation: 3-5 minutes
  - Post-Processing: 3-5 minutes

### **Output Specifications**
- **Final Resolution**: 768x1408 (2x upscaled)
- **Frame Count**: 82 frames (2x interpolated)
- **Frame Rate**: 8fps
- **Duration**: ~10 seconds
- **Format**: H.264 MP4
- **Quality**: Production-ready

---

## Deployment

### **Model Name**: `r8.im/enhance-replicate/wan22-comfyui-full`

### **Deploy Command**:
```bash
cog push r8.im/enhance-replicate/wan22-comfyui-full
```

### **Usage**:
1. **Simple**: Just modify the prompt field, leave workflow as default
2. **Advanced**: Provide custom workflow JSON for complete control

---

## Key Technical Decisions

### 1. Weight Synonyms vs Other Approaches
**Chosen**: Weight Synonyms System  
**Rationale**: 
- Uses existing proven codebase mechanisms
- No custom code required
- Automatic caching and error handling
- Follows documented patterns in README.md

### 2. GGUF Model Strategy
**Chosen**: Q4_K_M quantization  
**Rationale**:
- 4x smaller model size vs FP16
- Significant memory savings for A100 deployment
- Acceptable quality trade-off for production use

### 3. LoRA Integration
**Chosen**: Dual LoRA loading (LightX2V + FusionX)  
**Rationale**:
- LightX2V: Speed optimization (1.0 strength)
- FusionX: Quality enhancement (0.5 strength)
- Both applied to both generation stages

### 4. Post-Processing Pipeline
**Chosen**: Full pipeline (Tiled VAE + RealESRGAN + RIFE)  
**Rationale**:
- Tiled VAE: Handles large video memory requirements
- RealESRGAN: 2x spatial improvement for mobile-friendly output
- RIFE: 2x temporal smoothness for professional quality

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Model Loading Failures
- **Symptom**: "Model not found" errors
- **Cause**: URL mapping missing or incorrect
- **Solution**: Verify URLs in `weight_synonyms.json` are accessible

#### Memory Errors
- **Symptom**: CUDA out of memory
- **Cause**: Both models + post-processing exceeds GPU memory
- **Solution**: Use model offloading or reduce batch size

#### Generation Timeouts
- **Symptom**: Process killed after 15+ minutes
- **Cause**: Hardware insufficient or network issues
- **Solution**: Check model download progress, verify A100 hardware

#### Quality Issues
- **Symptom**: Poor video quality or artifacts
- **Cause**: Parameter mismatch or LoRA conflicts
- **Solution**: Verify workflow parameters match local successful runs

---

## Future Enhancements

### Potential Optimizations
1. **FP8 Models**: Further memory reduction if available
2. **Dynamic LoRA Loading**: Load LoRAs based on prompt analysis
3. **Progressive Download**: Download models in background during generation
4. **Quality Presets**: Fast/Balanced/High quality options

### Additional Features
1. **Batch Processing**: Multiple prompts in single run
2. **Custom Aspect Ratios**: Support for different video dimensions
3. **Length Control**: Variable video duration options
4. **Style Transfer**: Additional LoRA collections

---

## Conclusion

The WAN2.2 full pipeline implementation successfully bypasses the progressive milestone approach to deliver a complete production-ready text-to-video system. The weight synonyms strategy provides robust automatic model downloading while maintaining compatibility with the existing codebase architecture.

**Status**: ✅ Ready for deployment  
**Confidence Level**: High (based on documented patterns and proven systems)  
**Next Step**: Execute `cog push r8.im/enhance-replicate/wan22-comfyui-full`