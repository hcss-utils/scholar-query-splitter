# Scholar Query Splitter

A powerful Python tool that helps researchers overcome Google Scholar's 1000-result limit by intelligently splitting large queries into smaller, manageable chunks using AI-powered semantic analysis.

## 🎯 Two Modes of Operation

### 1. **Discovery Mode** (main.py)
Find interesting query combinations and research gaps by exploring modifier combinations.

### 2. **Exhaustive Mode** (main_exhaustive.py) 
Systematically split large queries to capture ALL results when a query returns >1000 hits.

## Overview

Google Scholar limits search results to 1000 per query. This tool solves that limitation by:
- Analyzing your query using OpenAlex metadata
- Extracting relevant keywords and entities using AI/NLP
- Generating strategic subqueries that together capture all results
- Tracking coverage to ensure no results are missed

## Features

- **🚀 GPU Acceleration**: Optimized for NVIDIA GPUs (tested on RTX 4090)
- **📊 OpenAlex Integration**: Downloads open-access metadata for analysis
- **🧠 AI-Powered Extraction**: 
  - KeyBERT for semantic keyword extraction
  - spaCy for named entity recognition with type classification
- **📈 Smart Query Generation**: Creates optimal subqueries using:
  - Single modifiers
  - Modifier combinations
  - Exclusion queries
- **📅 Temporal Splitting**: Year-by-year processing for better control
- **📋 Complete Coverage Tracking**: Ensures no results are missed
- **💾 Incremental Saving**: Results saved as processing continues
- **📊 Comprehensive Analysis**: Statistics and insights on query effectiveness

## Installation

### Basic Installation

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

### GPU Setup (Optional but Recommended)

For GPU acceleration with NVIDIA GPUs:

```bash
# Install CUDA support for spaCy
pip install -r requirements-gpu.txt

# Or manually:
pip install cupy-cuda12x  # For CUDA 12.x
pip install spacy[cuda12x]
```

## Usage

### Discovery Mode - Find Research Gaps

Use this mode to explore interesting query combinations and find research niches:

```bash
# Basic usage
python main.py '(police OR "law enforcement") AND (strategic OR strategy)'

# With GPU and custom parameters
python main.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --use-gpu \
    --max-results 2000 \
    --top-keywords 30 \
    --top-entities 30 \
    --output-csv results.csv
```

### Exhaustive Mode - Get ALL Results

Use this mode when you need to capture ALL results from queries returning >1000 hits:

```bash
# Split a query exhaustively for complete coverage
python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --start-year 2020 \
    --end-year 2024 \
    --use-gpu

# With all options
python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --start-year 2020 \
    --end-year 2024 \
    --target-size 800 \           # Max hits per subquery
    --max-metadata 10000 \        # More metadata = better modifiers
    --top-keywords 200 \          # Extract more keywords
    --top-entities 200 \          # Extract more entities
    --use-gpu \
    --spacy-model en_core_web_lg
```

### Quick Test

Test the exhaustive mode with a single year:

```bash
python test_exhaustive.py
```

## Parameters

### Common Parameters
- `base_query`: Your search query (required)
- `--use-gpu`: Enable GPU acceleration
- `--spacy-model`: spaCy model to use (default: en_core_web_sm)
- `--top-keywords`: Number of keywords to extract
- `--top-entities`: Number of entities to extract

### Discovery Mode Specific
- `--max-results`: Max results from OpenAlex (default: 1000)
- `--max-queries`: Max subqueries to generate (default: 100)
- `--output-csv`: Output CSV filename

### Exhaustive Mode Specific
- `--start-year` & `--end-year`: Year range (REQUIRED)
- `--target-size`: Max hits per query (default: 900)
- `--max-metadata`: Max metadata to analyze (default: 5000)

## Output Files

### Discovery Mode
- `query_results.csv`: Queries with hit counts
- `query_results_analysis.json`: Statistical analysis
- `outputs/keywords_*.json`: Extracted keywords
- `outputs/entities_*.json`: Extracted entities with types

### Exhaustive Mode
- `outputs/exhaustive/all_queries_*.csv`: Complete query list
- `outputs/exhaustive/final_report_*.json`: Coverage report
- `outputs/exhaustive/year_*_results.json`: Year-specific results
- `outputs/exhaustive/coverage_map_*.json`: Coverage tracking

## How It Works

### 1. Metadata Collection
- Queries OpenAlex for relevant papers
- Downloads metadata including titles, abstracts, and concepts

### 2. Modifier Extraction
- **Keywords**: Extracts meaningful uni/bi-grams using KeyBERT
- **Entities**: Identifies organizations, locations, people using spaCy
- **Filtering**: Removes stopwords and terms already in base query

### 3. Query Generation

#### Discovery Mode
- Combines modifiers to create interesting subqueries
- Focuses on finding niche combinations

#### Exhaustive Mode
- Tests modifier effectiveness
- Creates optimal splitting strategy
- Uses combinations and exclusions to ensure complete coverage

### 4. Validation
- Counts actual Google Scholar hits for each query
- Tracks coverage to ensure completeness

## Entity Types

The tool extracts and classifies these entity types:
- **ORG**: Organizations (FBI, United Nations)
- **GPE**: Geopolitical entities (United States, London)
- **PERSON**: People names
- **LOC**: Locations (Africa, Pacific Ocean)
- **FAC**: Facilities (JFK Airport)
- **EVENT**: Events (World War II)

## Tips for Best Results

1. **Start with Exhaustive Mode** for systematic literature reviews
2. **Use GPU acceleration** for 5-10x faster processing
3. **Extract more modifiers** for better coverage (--top-keywords 200)
4. **Process year by year** for large time ranges
5. **Use larger spaCy models** for better entity recognition

## Example Workflow

```bash
# Step 1: Test with one year
python main_exhaustive.py 'your query' --start-year 2023 --end-year 2023 --use-gpu

# Step 2: If successful, run full range
python main_exhaustive.py 'your query' --start-year 2015 --end-year 2024 --use-gpu

# Step 3: Use generated queries to download papers systematically
# The CSV output contains all queries needed for complete coverage
```

## Performance

With RTX 4090 and 90GB RAM:
- Processes ~1000 documents in 2-3 minutes
- Extracts keywords/entities from 10,000 documents in ~10 minutes
- GPU acceleration provides 5-10x speedup for NLP tasks

## Troubleshooting

### CUDA/GPU Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

### Memory Issues
- Reduce `--max-metadata` if running out of RAM
- Process fewer years at once

### Rate Limiting
- Use `--use-proxy` for Google Scholar requests
- Add delays between requests

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{scholar_query_splitter,
  title = {Scholar Query Splitter: Automated Query Decomposition for Complete Google Scholar Coverage},
  author = {HCSS Utils},
  year = {2024},
  url = {https://github.com/hcss-utils/scholar-query-splitter}
}
```

## Acknowledgments

- OpenAlex for providing free academic metadata
- The KeyBERT and spaCy teams for excellent NLP tools
- Google Scholar for being an invaluable research resource