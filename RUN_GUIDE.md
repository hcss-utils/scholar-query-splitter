# Scholar Query Splitter - Run Guide

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/hcss-utils/scholar-query-splitter.git
cd scholar-query-splitter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Basic Usage

```bash
# Basic run with GPU acceleration (recommended for RTX 4090)
python main.py '(police OR "law enforcement") AND (strategic OR strategy)' --use-gpu

# With custom parameters
python main.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --use-gpu \
    --max-results 2000 \
    --top-keywords 30 \
    --top-entities 30 \
    --output-csv police_strategy_queries.csv
```

## Features & Progress Display

### GPU Optimization
When using `--use-gpu` with your RTX 4090:
- Automatic GPU detection and utilization
- Optimized batch sizes for 24GB VRAM
- Multi-threaded CPU fallback if GPU unavailable

### Verbose Progress Display

The tool provides detailed progress information at each stage:

#### 1. **Document Processing**
```
============================================================
MODIFIER EXTRACTION PIPELINE
============================================================
📊 Documents to process: 2000
🖥️  Hardware: GPU (NVIDIA GeForce RTX 4090)
💾 RAM Available: 82.3 GB / 90.0 GB
============================================================

📝 Processing documents: 100%|████████████| 2000/2000 [00:12<00:00, 164.23docs/s]
```

#### 2. **Keyword Extraction (KeyBERT)**
```
==================================================
🔑 KEYWORD EXTRACTION PHASE
==================================================
📋 Configuration:
   - N-gram range: (1, 3)
   - Diversity: 0.5 (MMR)
   - Stopword filtering: Enabled
   - Custom stopwords: 357 words

🔄 Processing in batches of 100 documents...
🔑 Extracting keywords: 100%|████████████| 20/20 [00:45<00:00, 2.25s/batch]
   ✓ Processed 500 / 2000 documents
   ✓ Processed 1000 / 2000 documents
   ✓ Processed 1500 / 2000 documents
   ✓ Processed 2000 / 2000 documents

📊 Keyword statistics:
   - Total unique keywords found: 4,523

🏆 Top 10 keywords:
    1. community policing              (score: 0.0234)
    2. intelligence-led policing       (score: 0.0198)
    3. strategic planning              (score: 0.0187)
    4. crime prevention                (score: 0.0165)
    5. predictive policing            (score: 0.0154)
    ...

✅ Extracted 30 keywords
💾 Keywords saved to: outputs/keywords_20250605_143022.json
```

#### 3. **Named Entity Extraction (spaCy)**
```
==================================================
🏷️  NAMED ENTITY EXTRACTION PHASE
==================================================
📋 Configuration:
   - Entity types: EVENT, FAC, GPE, LOC, ORG, PERSON
   - Min entity length: 3 characters
   - Batch processing: Enabled

🔄 Processing 2000 texts in 10 batches...
🏷️  Extracting entities: 100%|████████████| 10/10 [00:32<00:00, 3.20s/batch]
   ✓ Processed 1000 / 2000 texts
   📊 Unique entities so far: 1,234
   ✓ Processed 2000 / 2000 texts

📊 Entity statistics:
   - Total entities found: 15,678
   - Unique entities: 2,345

📈 Entities by type:
   - ORG     :  5432 ( 34.6%)
   - GPE     :  4321 ( 27.6%)
   - PERSON  :  2876 ( 18.3%)
   - LOC     :  1654 ( 10.5%)
   - FAC     :   876 (  5.6%)
   - EVENT   :   519 (  3.3%)

🏆 Top 10 entities:
    1. United States            [GPE    ] (freq: 0.0432)
    2. FBI                      [ORG    ] (freq: 0.0387)
    3. New York Police Department [ORG   ] (freq: 0.0298)
    4. London                   [GPE    ] (freq: 0.0276)
    5. Department of Justice    [ORG    ] (freq: 0.0254)
    ...

✅ Extracted 30 unique entities
💾 Entities saved to: outputs/entities_20250605_143055.json
```

### Incremental Output Files

The tool saves intermediate results as it processes:

1. **Keywords file** (`outputs/keywords_YYYYMMDD_HHMMSS.json`):
```json
[
  ["community policing", 0.0234],
  ["intelligence-led policing", 0.0198],
  ["strategic planning", 0.0187]
]
```

2. **Entities file** (`outputs/entities_YYYYMMDD_HHMMSS.json`):
```json
[
  ["United States", "GPE", 0.0432],
  ["FBI", "ORG", 0.0387],
  ["New York Police Department", "ORG", 0.0298]
]
```

## Advanced Usage

### Using Existing OpenAlex Metadata
```bash
# Skip downloading and use existing metadata
python main.py '(police OR "law enforcement")' \
    --skip-openalex \
    --metadata-file json/openalex_20250605_010747_500_results.json \
    --use-gpu
```

### Time-based Query Splitting
```bash
# Split queries by year range
python main.py '(police OR "law enforcement") AND strategy' \
    --start-year 2015 \
    --end-year 2024 \
    --use-gpu
```

### Using Better spaCy Models
```bash
# Download larger model for better NER
python -m spacy download en_core_web_lg

# Use it in the tool
python main.py 'your query' --spacy-model en_core_web_lg --use-gpu
```

### Using Proxy for Google Scholar
```bash
# With ScraperAPI (recommended)
python main.py 'your query' --use-proxy --proxy-type scraperapi --use-gpu
```

## Performance Tips for RTX 4090

1. **Always use `--use-gpu`** - This enables GPU acceleration for both KeyBERT and spaCy
2. **Increase batch sizes** - Your 90GB RAM can handle larger batches
3. **Use larger models** - `en_core_web_lg` or `en_core_web_trf` for better accuracy

## Environment Variables

Create a `.env` file:
```bash
OPENALEX_EMAIL=your-email@example.com  # For polite pool access
SCRAPERAPI_KEY=your-api-key             # If using ScraperAPI
```

## Output Files

- **CSV Results**: `query_results.csv` (or custom name)
- **Analysis JSON**: `query_results_analysis.json`
- **Keywords**: `outputs/keywords_*.json`
- **Entities**: `outputs/entities_*.json`
- **Logs**: `outputs/log.txt`

## Troubleshooting

### CUDA/GPU Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### Memory Issues
- Reduce `--max-results` if running out of RAM
- The tool automatically adjusts batch sizes based on available memory

### spaCy GPU Setup
```bash
# Install CUDA-enabled spaCy
pip install spacy[cuda12x]  # For CUDA 12.x
```