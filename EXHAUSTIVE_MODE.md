# Exhaustive Query Splitting Mode

## Purpose

This mode is designed to solve a specific problem: **Getting ALL results from Google Scholar when your query returns more than 1000 hits.**

Google Scholar limits results to 1000 per query, so if your search returns 10,000 hits, you're missing 9,000 results. This tool systematically splits your query into smaller chunks that each return <1000 hits, ensuring complete coverage.

## How It Works

1. **Analyzes your base query** to understand its scope
2. **Extracts keywords and entities** from relevant papers (uni/bi-grams only)
3. **Tests modifier effectiveness** to see which ones best split the results
4. **Creates a splitting strategy** using:
   - Single modifiers (e.g., `AND "police training"`)
   - Combinations (e.g., `AND "police training" AND "Chicago"`)
   - Exclusions (e.g., `NOT "police training" NOT "Chicago"`)
5. **Ensures complete coverage** by tracking what's been captured

## Usage

### Basic Command

```bash
python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --start-year 2020 \
    --end-year 2024 \
    --use-gpu
```

### Full Example with All Options

```bash
python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --start-year 2020 \
    --end-year 2024 \
    --target-size 800 \
    --max-metadata 10000 \
    --top-keywords 200 \
    --top-entities 200 \
    --use-gpu \
    --spacy-model en_core_web_lg \
    --use-proxy \
    --proxy-type scraperapi
```

## Parameters

- `--start-year` & `--end-year` (REQUIRED): Define the time range
- `--target-size`: Maximum hits per query (default: 900, stays under 1000 limit)
- `--max-metadata`: How many papers to analyze from OpenAlex (default: 5000)
- `--top-keywords` & `--top-entities`: How many modifiers to extract (default: 100 each)
- `--use-gpu`: Enable GPU acceleration for faster processing
- `--use-proxy`: Use proxy for Google Scholar (recommended for large jobs)

## Example Output

```
============================================================
EXHAUSTIVE QUERY SPLITTER
============================================================
🎯 Goal: Split query into chunks < 900 hits
📝 Base query: (police OR "law enforcement") AND (strategic OR strategy)
📅 Year range: 2020 - 2020
============================================================

📊 Base query hits: 3,456

🔧 Preparing modifiers...
   - Keywords: 95
   - Entities: 87

📈 Testing modifier effectiveness...
   Testing keywords: 100%|████████| 30/30
   Testing entities: 100%|████████| 30/30

🔨 Creating splitting strategy...
   Target: Cover 3,456 hits in chunks < 900

🚀 Executing query splits...
   Executing splits: 100%|████████| 8/8

✓ Verifying coverage...

============================================================
📊 SPLITTING COMPLETE
============================================================
✅ Total queries generated: 8
📈 Coverage: 98.5%
📁 Results saved to: outputs/exhaustive/exhaustive_split_20250605_143022.json
🗺️  Coverage map saved to: outputs/exhaustive/coverage_map_20250605_143022.json
```

## Output Files

### 1. Query CSV (`all_queries_*.csv`)
```csv
year,query_id,query,modifiers,type,hits
2020,1,"(police OR ""law enforcement"") AND (strategic OR strategy) AND ""police training""",police training,single,876
2020,2,"(police OR ""law enforcement"") AND (strategic OR strategy) AND ""community policing""",community policing,single,743
2020,3,"(police OR ""law enforcement"") AND (strategic OR strategy) AND ""Chicago""",Chicago,single,521
...
```

### 2. Coverage Report (`final_report_*.json`)
```json
{
  "timestamp": "2025-06-05T14:35:22",
  "base_query": "(police OR \"law enforcement\") AND (strategic OR strategy)",
  "year_range": "2020-2024",
  "total_queries_generated": 45,
  "total_coverage": 15234,
  "yearly_results": [
    {
      "year": 2020,
      "coverage_percentage": 98.5,
      "queries": 8
    },
    ...
  ]
}
```

## Tips for Best Results

1. **Always specify year ranges** - This makes splitting much more manageable
2. **Start with one year** to test: `--start-year 2023 --end-year 2023`
3. **Use more metadata** for better modifiers: `--max-metadata 10000`
4. **Extract more modifiers**: `--top-keywords 200 --top-entities 200`
5. **Use GPU** for faster processing: `--use-gpu`
6. **Use proxy** to avoid rate limiting: `--use-proxy --proxy-type scraperapi`

## What Makes This Different

Unlike the regular mode which finds "interesting" query combinations, exhaustive mode:
- **Maximizes coverage** rather than finding niche queries
- **Tracks what's been captured** to avoid duplicates
- **Uses exclusion queries** to catch remaining results
- **Processes year by year** for better control
- **Generates ready-to-use query lists** for systematic downloading

## Next Steps

After running this tool, you'll have a CSV file with all queries needed to capture (nearly) all results. You can then:

1. Use the queries to systematically download all papers
2. Remove duplicates based on paper IDs
3. Build a comprehensive dataset of all matching papers

## Limitations

- Some overlap is inevitable (papers matching multiple modifier combinations)
- Very broad queries might need manual intervention
- Rate limiting means large jobs take time
- Coverage might not be exactly 100% due to Google Scholar's fuzzy matching