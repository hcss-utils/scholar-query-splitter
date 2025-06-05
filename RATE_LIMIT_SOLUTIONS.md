# Dealing with Google Scholar Rate Limits

## The Problem
Google Scholar returns "429 Too Many Requests" when you query too frequently. You're seeing the CAPTCHA page (`/sorry/index`).

## Solutions

### 1. Use ScraperAPI (Recommended)

First, get a free API key from https://www.scraperapi.com/ (5000 requests/month free).

Then add to your `.env` file:
```bash
SCRAPERAPI_KEY=your_api_key_here
```

Run with proxy:
```bash
python main_exhaustive.py 'your query' \
    --start-year 2020 \
    --end-year 2024 \
    --use-proxy \
    --proxy-type scraperapi \
    --use-gpu
```

### 2. Add Manual Delays

Create a custom version with longer delays:

```python
# In pipeline/scholar_hits.py, modify these values:
self.min_delay = 30   # Was 5
self.max_delay = 60   # Was 15
self.error_delay = 300  # Was 60
```

### 3. Use Free Proxies (Less Reliable)

```bash
python main_exhaustive.py 'your query' \
    --start-year 2020 \
    --end-year 2024 \
    --use-proxy \
    --proxy-type free \
    --use-gpu
```

### 4. Manual CAPTCHA Solving

If you get blocked:
1. Open https://scholar.google.com in your browser
2. Complete the CAPTCHA
3. Wait 5-10 minutes
4. Try again with longer delays

### 5. Use Scholarly's Built-in Solutions

The tool already uses the `scholarly` library which has some built-in anti-blocking features:

```python
from scholarly import scholarly, ProxyGenerator

# Set up a proxy
pg = ProxyGenerator()
pg.FreeProxies()  # or pg.ScraperAPI(api_key)
scholarly.use_proxy(pg)
```

## Best Practices to Avoid Rate Limits

1. **Start Small**: Test with one year first
   ```bash
   python test_exhaustive.py
   ```

2. **Use Realistic Delays**: Don't rush
   ```bash
   # Add custom delay parameter (you'd need to implement this)
   --min-delay 30 --max-delay 60
   ```

3. **Process During Off-Hours**: Less traffic = less blocking

4. **Rotate User Agents**: Already implemented in the tool

5. **Use Institution Access**: If you have university VPN, use it

## Quick Fix for Current Session

Since you're blocked now:

1. Wait 10-15 minutes
2. Use ScraperAPI for the exhaustive run:
   ```bash
   # Sign up at https://www.scraperapi.com/
   export SCRAPERAPI_KEY=your_key
   
   python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
       --start-year 2023 \
       --end-year 2023 \
       --use-proxy \
       --proxy-type scraperapi \
       --use-gpu \
       --target-size 500
   ```

## Alternative: Skip Hit Counting

For testing, you can modify the exhaustive splitter to use simulated counts:

```python
# In pipeline/exhaustive_splitter.py, _get_hit_count method
# Change the else block to always simulate:
def _get_hit_count(self, query: str, year_range: Optional[Tuple[int, int]] = None) -> int:
    """Get hit count for a query."""
    # Temporarily simulate to avoid rate limits
    import random
    time.sleep(0.1)
    
    # Simulate realistic distributions
    if "AND" in query and query.count("AND") > 2:
        return random.randint(50, 500)  # More specific queries
    else:
        return random.randint(500, 5000)  # Broader queries
```

This lets you test the splitting logic without hitting Google Scholar.