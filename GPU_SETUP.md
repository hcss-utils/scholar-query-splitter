# GPU Setup Guide for RTX 4090

## Quick Fix (Run without full GPU for now)

If you just want to run the tool immediately, it will still use GPU for KeyBERT but CPU for spaCy:

```bash
python main.py '(police OR "law enforcement") AND (strategic OR strategy)' --use-gpu
```

This will show a warning about spaCy GPU but will continue running.

## Full GPU Setup

### 1. Check your CUDA version

```bash
nvidia-smi
```

Look for "CUDA Version" in the output (usually 12.x for RTX 4090).

### 2. Install GPU requirements

```bash
# For CUDA 12.x (most common for RTX 4090)
pip install cupy-cuda12x

# Or if you have CUDA 11.x
pip install cupy-cuda11x
```

### 3. Install spaCy with GPU support

```bash
# Uninstall current spaCy
pip uninstall spacy -y

# Reinstall with CUDA support
pip install spacy[cuda12x]

# Download the model again
python -m spacy download en_core_web_sm
```

### 4. Verify GPU setup

```python
# Test script
python -c "import torch; print(f'PyTorch GPU: {torch.cuda.is_available()}')"
python -c "import spacy; spacy.require_gpu(); print('spaCy GPU: OK')"
```

## Alternative: Use Larger Models

For better accuracy with your RTX 4090:

```bash
# Download larger spaCy model
python -m spacy download en_core_web_lg

# Use it
python main.py 'your query' --use-gpu --spacy-model en_core_web_lg
```

## Troubleshooting

### CuPy installation fails
- Make sure you have CUDA toolkit installed
- Try: `conda install -c conda-forge cupy` if using conda

### Out of memory errors
- Reduce batch size by modifying the code
- Or just continue with the current setup (GPU for KeyBERT, CPU for spaCy)

### Performance without full GPU
Even without CuPy, you still get:
- ✅ GPU acceleration for KeyBERT (via PyTorch)
- ✅ Optimized batch processing
- ✅ Multi-threaded CPU processing for spaCy
- ✅ All features working correctly

The tool adapts automatically and will use the best available hardware.