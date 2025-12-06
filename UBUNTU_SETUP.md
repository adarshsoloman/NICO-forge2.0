# Rewat-Forge Ubuntu Setup Guide

## Quick Start

The easiest way to get started on Ubuntu is using the automated setup script:

```bash
cd Rewat-Forge
bash setup_ubuntu.sh
```

This script will:
- ✅ Check Python version (3.8+ required)
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Verify installation

## Manual Installation

If you prefer manual setup or need more control:

### 1. Install Python 3.8+

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

Verify installation:
```bash
python3 --version  # Should show 3.8 or higher
```

### 2. Create Virtual Environment

```bash
cd Rewat-Forge
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python3 test_modules.py
```

## Configuration

Edit `config.py` to customize your setup:

```python
# Adjust worker threads for your CPU
WORKER_THREADS = 4  # Recommended: number of CPU cores

# Enable/disable LLM verification
USE_LLM_VERIFICATION = False  # Set to True if using LLM

# If using LLM, configure API settings
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_API_KEY = "your-api-key-here"
LLM_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
```

## Running the Pipeline

### Single PDF Pair

```bash
source .venv/bin/activate  # Always activate first
python3 rewat_pipeline.py english.pdf hindi.pdf
```

### Multiple PDF Pairs (Folder Mode)

```bash
python3 rewat_pipeline.py english_pdfs/ hindi_pdfs/
```

**Note:** PDFs must have identical filenames in both folders.

## Ubuntu-Specific Tips

### Virtual Environment

Always activate the virtual environment before running the pipeline:

```bash
source .venv/bin/activate
```

You'll see `(.venv)` in your terminal prompt when activated.

To deactivate:
```bash
deactivate
```

### File Paths

Ubuntu uses forward slashes (`/`) for paths:
```bash
# ✅ Correct
python3 rewat_pipeline.py /home/user/pdfs/eng.pdf /home/user/pdfs/hin.pdf

# ✅ Also correct (relative paths)
python3 rewat_pipeline.py ./pdfs/eng.pdf ./pdfs/hin.pdf
```

### Permissions

If you get permission errors when running scripts:

```bash
chmod +x setup_ubuntu.sh
```

## Troubleshooting

### Issue: "python3: command not found"

**Solution:** Install Python 3:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Issue: "No module named 'fitz'"

**Solution:** Activate virtual environment and reinstall dependencies:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: Virtual environment not activating

**Solution:** Install venv module:
```bash
sudo apt install python3-venv
```

Then recreate the virtual environment:
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

### Issue: PDF processing fails

**Solution:** Ensure PDFs are readable:
```bash
# Check file permissions
ls -l *.pdf

# Make readable if needed
chmod +r *.pdf
```

### Issue: Out of memory errors

**Solution:** Reduce worker threads in `config.py`:
```python
WORKER_THREADS = 2  # Reduce based on available RAM
```

### Issue: LLM API errors

**Solution:** 
1. Verify API key is correct in `config.py`
2. Check internet connection
3. Test with LLM disabled first:
   ```python
   USE_LLM_VERIFICATION = False
   ```

## Performance Optimization

### CPU Usage

Adjust worker threads based on your CPU:
```bash
# Check CPU cores
nproc

# Set in config.py
WORKER_THREADS = 4  # Use number from nproc
```

### Monitoring

Track resource usage while processing:
```bash
# In another terminal
htop
# or
top
```

## System Requirements

- **OS:** Ubuntu 20.04+ (or Debian-based distros)
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum, 8GB+ recommended for large PDFs
- **Disk:** 500MB for dependencies + space for PDFs/output

## Dependencies

All managed via `requirements.txt`:
- **PyMuPDF** (≥1.24.0) - PDF text extraction
- **requests** (≥2.31.0) - HTTP requests for LLM APIs
- **openai** (≥1.0.0) - OpenAI-compatible API client

## Updating

To update Rewat-Forge:

```bash
# Pull latest changes (if using git)
git pull

# Reinstall dependencies
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Uninstalling

```bash
# Remove virtual environment
rm -rf .venv

# Remove output files (optional)
rm final_output.csv final_output.json errors.log
```

## Additional Resources

- **Main README:** [README.md](README.md)
- **LLM Alignment Guide:** [LLM_ALIGNMENT_GUIDE.md](LLM_ALIGNMENT_GUIDE.md)
- **Quick Start:** [QUICK_START.md](QUICK_START.md)

## Getting Help

If you encounter issues:

1. Check `errors.log` for detailed error messages
2. Run `python3 test_modules.py` to verify modules
3. Test with a small sample PDF first
4. Disable LLM verification to isolate issues

---

**Happy Dataset Extraction on Ubuntu! 🐧🚀**
