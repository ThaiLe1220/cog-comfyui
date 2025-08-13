# 🚀 Replicate Deployment Guide for Custom cog-comfyui

## Overview

This guide shows how to deploy and test your customized cog-comfyui (with WAN2.2 custom nodes and models) on the Replicate platform after successful local development.

---

## 🚀 Replicate Deployment Steps

### 1. Push to Replicate
```bash
# Deploy your custom model to Replicate
cog push r8.im/your-username/custom-comfyui-wan22

# Alternative: Use your actual Replicate username
cog push r8.im/huyai/cog-comfyui-wan22
```

### 2. Test via Replicate Web Interface
Once deployed, test at: `https://replicate.com/your-username/custom-comfyui-wan22`

**Input parameters:**
- `workflow_json`: Paste your `examples/api_workflows/Wan22_basic_gguf.json` content
- `return_temp_files`: `true` (to see intermediate files)
- `force_reset_cache`: `false` (unless you want to re-download models)

### 3. Test via Replicate API
```bash
# Install Replicate Python client
pip install replicate

# Test with Python script
python -c "
import replicate
import json

# Load your workflow
with open('examples/api_workflows/Wan22_basic_gguf.json', 'r') as f:
    workflow = json.load(f)

# Run prediction
output = replicate.run(
    'your-username/custom-comfyui-wan22',
    input={
        'workflow_json': json.dumps(workflow),
        'return_temp_files': True
    }
)
print('Output:', output)
"
```

### 4. Test via cURL
```bash
# Get your API token from https://replicate.com/account/api-tokens
export REPLICATE_API_TOKEN=your_token_here

# Run prediction
curl -s -X POST \
  -H "Authorization: Token $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "your-model-version-id",
    "input": {
      "workflow_json": "'"$(cat examples/api_workflows/Wan22_basic_gguf.json | tr -d '\n')"'",
      "return_temp_files": true
    }
  }' \
  https://api.replicate.com/v1/predictions
```

---

## ⚠️ Expected First-Run Behavior

**On Replicate's first execution:**
1. **Cold Start**: ~5-10 minutes for container initialization
2. **Model Download**: Your custom helper will download all 17GB of models
3. **Execution**: Then run your workflow (~85 seconds)
4. **Total First Run**: ~15-20 minutes

**Subsequent runs:**
- Models are cached on Replicate's infrastructure
- Should execute in ~85 seconds (same as local)

---

## 🔍 Monitoring Deployment

### Check Build Status
```bash
# Monitor the build process
cog push r8.im/your-username/custom-comfyui-wan22 --follow
```

### Replicate Logs
- View real-time logs in Replicate web interface
- Look for your custom helper messages:
  ```
  🚀 Checking WAN2.2 custom models...
  📥 Downloading WAN2.2 High Noise GGUF...
  ```

---

## 💡 Pro Tips for Replicate

### Optimize Cold Starts
Consider pre-warming by adding commonly used models to `weights.json` and uploading via:
```bash
python scripts/push_weights.py your-model.gguf
```

### Monitor Costs
- First run: ~$5-10 (due to 17GB download + processing)
- Subsequent runs: ~$1-2 per execution
- Consider model size vs. cost trade-off

### Test Incremental
Start with a smaller workflow to verify deployment before running the full WAN2.2 pipeline.

---

## 🧪 Testing Checklist

Before deploying to production:

- [ ] Local `cog predict` works successfully
- [ ] All custom nodes load without errors
- [ ] All 7 models download correctly (17GB total)
- [ ] WAN2.2 workflow executes in ~85 seconds
- [ ] Generated output is correct (animated WEBP)
- [ ] `weights.json` includes all custom models
- [ ] No hardcoded local paths in workflows

---

## 🚨 Troubleshooting Common Issues

### Build Failures
```bash
# Check for missing dependencies
cog build --debug

# Verify custom_nodes.json syntax
python -c "import json; json.load(open('custom_nodes.json'))"
```

### Model Download Issues on Replicate
- Ensure HuggingFace URLs use `/resolve/main/` format
- Check if models are accessible publicly
- Verify `custom_node_helpers/WAN22_Custom_Models.py` has correct URLs

### Workflow Execution Errors
- Use `return_temp_files: true` to debug intermediate files
- Check Replicate logs for specific error messages
- Ensure workflow JSON is in API format (not UI format)

### Cost Optimization
- Use quantized models (GGUF) to reduce memory usage
- Consider splitting large workflows into smaller chunks
- Monitor usage in Replicate dashboard

---

## 📊 Expected Performance Metrics

### Local vs Replicate Comparison
| Metric | Local Development | Replicate First Run | Replicate Cached |
|--------|------------------|-------------------|------------------|
| Cold Start | 0s | 5-10 minutes | 30-60 seconds |
| Model Download | 17GB (one-time) | 17GB (one-time) | Cached |
| Execution Time | 84.69 seconds | ~85 seconds | ~85 seconds |
| Total Time | ~85 seconds | 15-20 minutes | ~2-3 minutes |

---

## 🎯 Success Indicators

Your deployment is successful when you see:

```
✅ Custom nodes loaded: ComfyUI-GGUF, ComfyUI_LayerStyle
✅ Models downloaded: 7 models (17GB total)
✅ Workflow executed: 84.69 seconds
✅ Output generated: ComfyUI_00001_.webp
```

Your custom cog-comfyui implementation is now ready for production use on Replicate!