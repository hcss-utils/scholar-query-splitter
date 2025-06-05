# Scholar Query Splitter

A modular Python tool that automates the process of splitting large Google Scholar queries (>1000 hits) into smaller, manageable subqueries using semantic keyword and entity extraction.

## Overview

This tool helps researchers overcome Google Scholar's 1000-result limit by intelligently splitting broad queries into more specific subqueries. It uses OpenAlex to gather metadata, extracts meaningful modifiers using NLP techniques, and generates optimized subqueries that return manageable result sets.

## Features

- **OpenAlex Integration**: Downloads open-access metadata for initial analysis
- **Smart Modifier Extraction**: Uses KeyBERT for keyword extraction and spaCy for named entity recognition
- **Intelligent Query Generation**: Creates subqueries by combining base queries with extracted modifiers
- **Temporal Splitting**: Supports year-based query splitting for comprehensive coverage
- **Google Scholar Hit Counting**: Validates each subquery by counting actual hits
- **Progress Tracking**: Real-time progress bars and comprehensive logging
- **Results Analysis**: Provides insights on the most effective query splitting strategies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hcss-utils/scholar-query-splitter.git
cd scholar-query-splitter
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

### Basic Usage

```bash
python main.py '(police OR "law enforcement") AND (strategic OR strategy)'
```

### Advanced Usage

```bash
python main.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --openalex-email your.email@example.com \
    --max-results 2000 \
    --start-year 2010 \
    --end-year 2023 \
    --max-queries 150 \
    --top-keywords 30 \
    --top-entities 25 \
    --use-proxy \
    --output-csv results.csv
```

### Command Line Arguments

- `base_query` (required): The base search query to split
- `--openalex-email`: Email for OpenAlex polite pool access (recommended)
- `--max-results`: Maximum results to fetch from OpenAlex (default: 1000)
- `--start-year`: Start year for temporal splitting
- `--end-year`: End year for temporal splitting
- `--max-queries`: Maximum number of subqueries to generate (default: 100)
- `--top-keywords`: Number of top keywords to extract (default: 20)
- `--top-entities`: Number of top entities to extract (default: 20)
- `--use-proxy`: Use proxy for Google Scholar requests
- `--proxy-type`: Type of proxy to use [free, luminati, scraperapi] (default: free)
- `--spacy-model`: spaCy model for NER (default: en_core_web_sm)
- `--output-csv`: Output CSV file name (default: query_results.csv)
- `--skip-openalex`: Skip OpenAlex download and use existing metadata
- `--metadata-file`: Path to existing OpenAlex metadata JSON file

## Project Structure

```
scholar-query-splitter/
├── main.py                 # Main orchestrator script
├── pipeline/              # Core pipeline modules
│   ├── openalex.py       # OpenAlex metadata downloader
│   ├── modifier_extraction.py  # KeyBERT + spaCy NER extractor
│   ├── query_generation.py     # Subquery generator
│   └── scholar_hits.py        # Google Scholar hit counter
├── json/                  # Raw JSON metadata storage
├── outputs/              # Logs and temporary outputs
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Output Files

The tool generates several output files:

1. **JSON Metadata** (`json/openalex_*.json`): Raw metadata from OpenAlex
2. **Query Results CSV** (`query_results.csv`): Detailed results for each subquery including:
   - Query string
   - Base query and modifiers
   - Year range
   - Hit count
   - Status and errors
3. **Analysis JSON** (`query_results_analysis.json`): Summary statistics and insights
4. **Log File** (`outputs/log.txt`): Detailed execution logs

## Example Output

```csv
index,query,base_query,modifiers,modifier_count,year_range,hit_count,status,error,timestamp
0,"(police OR ""law enforcement"") AND (strategic OR strategy) ""community policing""",police OR "law enforcement") AND (strategic OR strategy),"community policing",1,,342,success,,2024-01-15T10:30:45
1,"(police OR ""law enforcement"") AND (strategic OR strategy) ""crime prevention"" after:2019 before:2021",police OR "law enforcement") AND (strategic OR strategy),"crime prevention",1,"(2020, 2020)",127,success,,2024-01-15T10:31:02
```

## Tips for Best Results

1. **Use Specific Base Queries**: Start with a well-defined base query that captures your research topic
2. **Provide Email for OpenAlex**: This gives you access to the polite pool for faster API access
3. **Adjust Time Ranges**: Use year ranges to split very large result sets temporally
4. **Monitor Rate Limits**: The tool includes automatic rate limiting, but be patient with large query sets
5. **Use Proxies Carefully**: Free proxies can be unreliable; consider paid options for production use

## Troubleshooting

### Common Issues

1. **"Model not found" error**: Run `python -m spacy download en_core_web_sm`
2. **Rate limiting errors**: Increase delays or use proxy options
3. **Memory issues with large datasets**: Reduce `--max-results` or process in batches

### Debug Mode

For detailed debugging, modify the logging level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAlex](https://openalex.org/) for providing open scholarly metadata
- [scholarly](https://github.com/scholarly-python-package/scholarly) for Google Scholar integration
- [KeyBERT](https://github.com/MaartenGr/KeyBERT) for keyword extraction
- [spaCy](https://spacy.io/) for named entity recognition

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{scholar_query_splitter,
  title = {Scholar Query Splitter: Automated Query Decomposition for Google Scholar},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/hcss-utils/scholar-query-splitter}
}
```