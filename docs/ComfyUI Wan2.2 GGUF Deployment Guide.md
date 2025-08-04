# ComfyUI Wan2.2 GGUF Deployment Guide
## Progressive Milestone Approach

### Overview
This guide takes you from a basic ComfyUI deployment to a fully optimized Wan2.2 GGUF text-to-video pipeline on Replicate, using strict progressive milestones to minimize risk and maximize learning.

---

## Milestone 0: Baseline Deployment
**Goal**: Deploy vanilla cog-comfyui to Replicate with zero modifications  
**Duration**: 2-3 hours  
**Risk Level**: Minimal  

### Prerequisites
- [x] MacOS with Docker installed
- [x] Replicate account created
- [x] Cog installed (`brew install replicate/tap/cog`)
- [x] Repository cloned: `git clone --recurse-submodules https://github.com/replicate/cog-comfyui.git`

### Step-by-Step Instructions

#### Step 0.1: Verify Local Setup
```bash
cd cog-comfyui
ls -la  # Verify all files present
cog --version  # Should show cog version
```

#### Step 0.2: Test Local Build (Optional but Recommended)
```bash
# This tests if the container builds correctly
cog build
```
**Expected**: Build completes without errors (may take 10-20 minutes)

#### Step 0.3: Deploy to Replicate
```bash
# Replace with your username
cog push r8.im/enhance-replicate/comfyui-test-baseline
```
**Expected**: Deployment succeeds, you get a model URL

#### Step 0.4: Test Basic Functionality
1. Go to your model page on Replicate
2. Use the default example workflow
3. Generate any image

### Success Criteria
- [x] Model deploys successfully
- [x] Can generate images via web interface
- [x] Can call via API
- [x] No error messages in logs

### Troubleshooting
- **Build fails**: Check Docker memory allocation (increase to 8GB+)
- **Push fails**: Verify `cog login` authentication
- **Model doesn't work**: Check Replicate console logs

### Next Steps
Once Milestone 0 passes, proceed to Milestone 1.

---

## Milestone 1: Add GGUF Support
**Goal**: Add ComfyUI-GGUF custom node without using it yet  
**Duration**: 1-2 hours  
**Risk Level**: Low  

### Prerequisites
- [x] Milestone 0 completed successfully
- [x] Baseline model working

### Step-by-Step Instructions

#### Step 1.1: Backup Current State
```bash
git add .
git commit -m "Milestone 0 - Baseline working"
git branch milestone-0
```

#### Step 1.2: Add GGUF Node to Custom Nodes
Edit `custom_nodes.json`, add this entry at the end before the closing bracket:
```json
,{
  "repo": "https://github.com/city96/ComfyUI-GGUF",
  "commit": "main"
}
```

#### Step 1.3: Add GGUF Dependencies
Edit `cog.yaml`, add under `python_packages`:
```yaml
- "gguf>=0.6.0"
```

#### Step 1.4: Install Nodes Locally (Testing)
```bash
./scripts/install_custom_nodes.py
```
**Expected**: ComfyUI-GGUF installs without errors

#### Step 1.5: Deploy Updated Version
```bash
cog push r8.im/enhance-replicate/comfyui-test-gguf
```

#### Step 1.6: Verify GGUF Nodes Available
1. Access ComfyUI interface via Replicate
2. Check that "bootleg" category exists in node menu
3. Verify "Unet Loader (GGUF)" node is available

### Success Criteria
- [x] Deployment succeeds with GGUF nodes added
- [x] GGUF nodes visible in ComfyUI interface
- [x] Can still run non-GGUF workflows (backward compatibility)
- [x] No new error messages

### Rollback Plan
```bash
git checkout milestone-0
cog push r8.im/enhance-replicate/comfyui-test-baseline
```

### Next Steps
Proceed to Milestone 2 - First GGUF Test

---

## Milestone 2: First GGUF Test
**Goal**: Successfully load and use a simple GGUF model  
**Duration**: 2-3 hours  
**Risk Level**: Medium  

### Prerequisites
- [x] Milestone 1 completed
- [x] GGUF nodes available in interface

### Step-by-Step Instructions

#### Step 2.1: Choose Test GGUF Model
We'll use a simple, well-tested GGUF model first:
- **Model**: FLUX.1-dev GGUF (available in many places)
- **URL**: `https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q4_K_M.gguf`

#### Step 2.2: Create Test Workflow
Create `test_workflow_gguf.json`:
```json
{
  "1": {
    "inputs": {
      "unet_name": "https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q4_K_M.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Load GGUF Model"
    }
  },
  "2": {
    "inputs": {
      "text": "a beautiful landscape"
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "Positive Prompt"
    }
  }
}
```

#### Step 2.3: Test GGUF Loading
1. Upload workflow to your deployed model
2. Run with simple prompt: "a red apple"
3. Monitor logs for GGUF loading messages

#### Step 2.4: Compare Performance
- Run same prompt with regular model
- Run same prompt with GGUF model
- Note differences in:
  - Generation time
  - Memory usage (check logs)
  - Output quality

### Success Criteria
- [x] GGUF model loads without errors
- [x] Generates images successfully
- [x] Memory usage lower than regular models
- [x] Output quality acceptable

### Common Issues & Solutions
- **"Model not found"**: Check URL accessibility
- **"Out of memory"**: GGUF should use LESS memory - check model size
- **"Invalid GGUF format"**: Try different quantization level

### Performance Expectations
- **Loading time**: Should be similar or slightly faster
- **Generation time**: May be slightly slower (acceptable trade-off)
- **Memory usage**: Should be significantly lower
- **Quality**: Slight quality reduction is expected and acceptable

### Next Steps
Proceed to Milestone 3 - Your Wan2.2 Models

---

## Milestone 3: Wan2.2 Basic T2V
**Goal**: Generate videos using your Wan2.2 GGUF models  
**Duration**: 3-4 hours  
**Risk Level**: Medium-High  

### Prerequisites
- [x] Milestone 2 completed
- [x] GGUF loading confirmed working

### Your Model URLs
```
High Noise: https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/HighNoise/Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf
Low Noise: https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/LowNoise/Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf
VAE: wan_2.1_vae.safetensors (already supported)
```

### Step-by-Step Instructions

#### Step 3.1: Create Basic Wan Workflow
Create `wan_basic_workflow.json` (simplified version of your working workflow):
```json
{
  "1": {
    "inputs": {
      "unet_name": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/HighNoise/Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Load Wan GGUF"
    }
  },
  "2": {
    "inputs": {
      "vae_name": "wan_2.1_vae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "3": {
    "inputs": {
      "text": "A baby dressed in a fluffy outfit is gently nose-to-nose with a small kitten"
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "Positive Prompt"
    }
  }
}
```

#### Step 3.2: Test Single-Stage Generation
1. Use only the High Noise model first
2. Test with your original prompt
3. Generate 5-second video
4. Verify output format and quality

#### Step 3.3: Validate Model Loading
Check logs for:
- GGUF model download progress
- Memory allocation messages
- No error messages during loading

#### Step 3.4: Output Analysis
Compare with your RTX 3090 results:
- Video length and frame rate
- Visual quality
- Generation time
- Any artifacts or issues

### Success Criteria
- [x] Wan2.2 GGUF model loads successfully
- [x] Generates video output
- [x] Video plays correctly
- [x] Quality comparable to local RTX 3090 output
- [x] No memory errors or crashes

### Performance Benchmarks
Expected on A100 (80GB):
- **Loading time**: 2-3 minutes (first run, then cached)
- **Generation time**: 3-5 minutes for 5-second video
- **Memory usage**: 40-50GB peak
- **Output**: 432x768, 29 frames

### Troubleshooting Guide
- **Model fails to load**: Check URL accessibility, file size
- **Out of memory**: Try L40S hardware instead of A100
- **Poor quality**: This is expected at this milestone (we add LoRAs next)
- **No video output**: Check VAE compatibility

### Next Steps
Proceed to Milestone 4 - Add LoRA Enhancement

---

## Milestone 4: LoRA Integration
**Goal**: Add your custom LoRAs to enhance video quality  
**Duration**: 2-3 hours  
**Risk Level**: Medium  

### Prerequisites
- [x] Milestone 3 completed
- [x] Basic Wan2.2 video generation working

### Your LoRA URLs
```
LightX2V: https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors
FusionX: https://huggingface.co/vrgamedevgirl84/Wan14BT2VFusioniX/resolve/main/FusionX_LoRa/Wan2.1_T2V_14B_FusionX_LoRA.safetensors
```

### Step-by-Step Instructions

#### Step 4.1: Test LoRA Compatibility
⚠️ **Critical Test**: GGUF + LoRA compatibility is experimental
1. Create minimal test workflow with one LoRA
2. Check if it loads without errors
3. If errors occur, document them for troubleshooting

#### Step 4.2: Add LoRAs to Workflow
Extend your `wan_basic_workflow.json`:
```json
{
  "4": {
    "inputs": {
      "lora_name": "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
      "strength_model": 1.0,
      "model": ["1", 0]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "LightX2V LoRA"
    }
  },
  "5": {
    "inputs": {
      "lora_name": "https://huggingface.co/vrgamedevgirl84/Wan14BT2VFusioniX/resolve/main/FusionX_LoRa/Wan2.1_T2V_14B_FusionX_LoRA.safetensors",
      "strength_model": 0.5,
      "model": ["4", 0]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "FusionX LoRA"
    }
  }
}
```

#### Step 4.3: Progressive LoRA Testing
**Test 1**: Single LoRA (LightX2V only)
- Strength: 1.0
- Compare quality vs Milestone 3 output

**Test 2**: Dual LoRA (Both LoRAs)
- LightX2V: 1.0 strength
- FusionX: 0.5 strength
- Monitor for any conflicts

#### Step 4.4: Quality Comparison
Generate same prompt with:
1. No LoRAs (Milestone 3 baseline)
2. Single LoRA
3. Dual LoRAs
4. Compare quality, style, and consistency

### Success Criteria
- [x] LoRAs load without errors
- [x] Video quality improves noticeably
- [x] No artifacts introduced by LoRAs
- [x] Generation completes successfully
- [x] Output matches local RTX 3090 results

### Known Issues & Workarounds
- **GGUF + LoRA incompatibility**: If LoRAs fail to load, this is a known limitation
- **Workaround**: May need to use non-quantized base models
- **Memory issues**: LoRAs add memory overhead
- **Quality conflicts**: Some LoRAs may not work well together

### Fallback Plan
If LoRAs fail with GGUF models:
1. Document the specific error
2. Consider using FP16 versions of base models
3. Or proceed to Milestone 5 without LoRAs as proof of concept

### Next Steps
Proceed to Milestone 5 - Two-Stage Generation

---

## Milestone 5: Two-Stage Generation
**Goal**: Implement your sophisticated high-noise → low-noise pipeline  
**Duration**: 3-4 hours  
**Risk Level**: High  

### Prerequisites
- [x] Milestone 4 completed (or documented why LoRAs failed)
- [x] Single-stage generation working reliably

### Conceptual Overview
Your workflow uses:
1. **Stage 1**: High-noise model (steps 0-4) with initial generation
2. **Stage 2**: Low-noise model (steps 4-8) for refinement
3. **Latent passing**: Stage 1 output feeds into Stage 2

### Step-by-Step Instructions

#### Step 5.1: Create Two-Stage Workflow
This is a complex workflow - create `wan_two_stage_workflow.json`:
```json
{
  "high_noise_model": {
    "inputs": {
      "unet_name": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/HighNoise/Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf"
    },
    "class_type": "UnetLoaderGGUF"
  },
  "low_noise_model": {
    "inputs": {
      "unet_name": "https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF/resolve/main/LowNoise/Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf"
    },
    "class_type": "UnetLoaderGGUF"
  },
  "stage_1_sampler": {
    "inputs": {
      "steps": 8,
      "start_at_step": 0,
      "end_at_step": 4,
      "return_with_leftover_noise": "enable"
    },
    "class_type": "KSamplerAdvanced"
  },
  "stage_2_sampler": {
    "inputs": {
      "steps": 8,
      "start_at_step": 4,
      "end_at_step": 10000,
      "return_with_leftover_noise": "disable"
    },
    "class_type": "KSamplerAdvanced"
  }
}
```

#### Step 5.2: Test Stage Coordination
**Critical**: Verify latent handoff between stages
1. Check that Stage 1 produces latent output with noise
2. Verify Stage 2 receives and processes this correctly
3. Monitor memory usage during transition

#### Step 5.3: Parameter Fine-Tuning
Adjust from your working RTX 3090 settings:
- **Noise seeds**: Use your successful values
- **CFG scales**: Match your working configuration
- **Step distributions**: 0-4 → 4-8 split as in original

#### Step 5.4: Quality Validation
Compare outputs:
1. **Single-stage** (Milestone 4) vs **Two-stage** (Milestone 5)
2. **Local RTX 3090** vs **Replicate cloud**
3. Look for improved details, smoother motion, better coherence

### Success Criteria
- [x] Both GGUF models load simultaneously
- [x] Stage 1 completes and passes latents to Stage 2
- [x] Stage 2 refines the output successfully
- [x] Overall quality superior to single-stage
- [x] Generation time reasonable (under 10 minutes)

### Performance Expectations
- **Memory usage**: 60-80GB peak (both models loaded)
- **Generation time**: 5-8 minutes total
- **Quality improvement**: Noticeably sharper, more coherent
- **File size**: Same as single-stage output

### Troubleshooting
- **Memory errors**: Consider using smaller hardware or CPU offloading
- **Stage handoff fails**: Check latent dimensions and noise levels
- **Quality regression**: Verify parameter matching with local setup
- **Timeout errors**: Increase model timeout settings

### Next Steps
Proceed to Milestone 6 - Full Pipeline with Post-Processing

---

## Milestone 6: Full Production Pipeline
**Goal**: Complete pipeline with RIFE interpolation and RealESRGAN upscaling  
**Duration**: 4-5 hours  
**Risk Level**: High  

### Prerequisites
- [x] Milestone 5 completed
- [x] Two-stage generation working reliably

### Pipeline Overview
Your complete workflow:
1. **Text Input** → **Two-stage generation** (Milestone 5)
2. **VAE Decode** → **Tiled processing**
3. **RealESRGAN** → **2x upscaling**
4. **RIFE** → **3x frame interpolation** (29 → 87 frames)
5. **Video Export** → **16fps H.264 MP4**

### Step-by-Step Instructions

#### Step 6.1: Add Post-Processing Nodes
The good news: These are already in your `custom_nodes.json`:
- ✅ `ComfyUI-VideoHelperSuite` (for RIFE)
- ✅ `ComfyUI_UltimateSDUpscale` (for upscaling)

#### Step 6.2: Complete Workflow Implementation
Create `wan_full_pipeline_workflow.json` incorporating:
- Your two-stage generation (Milestone 5)
- VAE tiled decoding
- RealESRGAN upscaling
- RIFE frame interpolation
- Video export settings

#### Step 6.3: Memory Management Strategy
Critical for full pipeline:
```json
{
  "memory_purge_1": {
    "inputs": {
      "purge_cache": true,
      "purge_models": true
    },
    "class_type": "LayerUtility: PurgeVRAM"
  }
}
```
Add purge nodes between intensive operations.

#### Step 6.4: Sequential Testing
**Test 1**: Two-stage + VAE decode only
**Test 2**: Add upscaling
**Test 3**: Add frame interpolation
**Test 4**: Add video export
**Test 5**: Full pipeline end-to-end

#### Step 6.5: Performance Optimization
- **Tiled processing**: 512px tiles, 64px overlap
- **Temporal processing**: 64 frames, 8 overlap
- **Memory purging**: After each major step
- **Model caching**: Keep frequently used models loaded

### Success Criteria
- [x] Complete pipeline executes without errors
- [x] Final video: 16fps, higher resolution, smooth motion
- [x] Quality matches or exceeds RTX 3090 output
- [x] Total generation time under 15 minutes
- [x] Memory usage stays within hardware limits

### Expected Output Specifications
- **Resolution**: 864x1536 (upscaled from 432x768)
- **Frame count**: 87 frames (interpolated from 29)
- **Frame rate**: 16fps
- **Duration**: ~5.4 seconds
- **Format**: H.264 MP4
- **Quality**: Near-production ready

### Final Validation Checklist
- [ ] Input prompt processing works correctly
- [ ] Two-stage generation produces quality base video
- [ ] VAE decoding handles video correctly
- [ ] Upscaling improves visual quality without artifacts
- [ ] Frame interpolation creates smooth motion
- [ ] Video export produces playable file
- [ ] Total cost per generation is reasonable
- [ ] Pipeline is reliable and repeatable

### Production Readiness
Once Milestone 6 passes:
- Document optimal parameters
- Create cost analysis
- Set up monitoring and logging
- Consider API customization for your specific needs

---

## Troubleshooting & Support

### Common Issues Across All Milestones

#### Deployment Issues
- **Cog build fails**: Increase Docker memory to 8GB+
- **Push timeouts**: Check internet connection, large model uploads
- **Model won't start**: Check Replicate logs for Python errors

#### Performance Issues
- **Out of memory**: Try smaller hardware tier or add memory purging
- **Generation too slow**: Consider FP8 models instead of FP16
- **Poor quality**: Verify model URLs and parameters match local setup

#### GGUF-Specific Issues
- **LoRA incompatibility**: Known limitation, may need non-quantized models
- **Model loading errors**: Verify GGUF format and version compatibility
- **Unexpected behavior**: GGUF quantization can change model behavior slightly

### Rollback Strategy
Each milestone includes Git branching:
```bash
# If any milestone fails:
git checkout milestone-N-working  # Go back to last working state
cog push r8.im/enhance-replicate/model-rollback  # Deploy rollback version
```

### Getting Help
1. **Check Replicate logs** first - most issues show clear error messages
2. **Compare with working RTX 3090 setup** - parameter mismatches are common
3. **Test individual components** - isolate which part is failing
4. **Community resources**: ComfyUI Discord, GGUF GitHub issues

### Success Metrics Summary
By the end of all milestones, you should have:
- ✅ **Reliable deployment process** (can update and deploy confidently)
- ✅ **Cost-effective video generation** (GGUF models reduce compute costs)
- ✅ **Production-quality output** (matches or exceeds local RTX 3090)
- ✅ **Scalable architecture** (can handle multiple requests)
- ✅ **Full understanding** of the pipeline (can debug and optimize)

---

## Appendix

### Hardware Recommendations by Milestone
- **Milestones 0-2**: A10G (24GB) - $0.003/sec
- **Milestones 3-4**: L40S (48GB) - $0.008/sec  
- **Milestones 5-6**: A100 (80GB) - $0.014/sec

### Cost Estimates
- **Development/Testing**: $50-100 total across all milestones
- **Production per video**: $0.15-0.25 (5-second video)
- **Monthly costs**: Depends on usage volume

### Timeline Summary
- **Week 1**: Milestones 0-3 (Foundation + basic video)
- **Week 2**: Milestones 4-6 (Enhancement + full pipeline)
- **Total**: 2 weeks to production-ready system

This progressive approach minimizes risk while building understanding at each step. Good luck with your deployment!