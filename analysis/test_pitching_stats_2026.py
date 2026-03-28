"""Quick script to test pybaseball pitching_stats for 2026 with qual=1.

Also attempts to surface the URL used to fetch data.
"""

import pandas as pd
import pybaseball as pb
from unittest.mock import patch
import pybaseball.datasources.html_table_processor as htp

# Patch get_tabular_data_from_url to capture the URL
original_get = htp.HTMLTableProcessor.get_tabular_data_from_url
captured_urls = []


def capturing_get(
    self: htp.HTMLTableProcessor, url: str, *args: object, **kwargs: object
) -> pd.DataFrame:
    captured_urls.append(url)
    print(f"URL: {url}")
    return original_get(self, url, *args, **kwargs)  # type: ignore[no-any-return]


pb.cache.disable()

with patch.object(htp.HTMLTableProcessor, "get_tabular_data_from_url", capturing_get):
    print("Trying pitching_stats(2026, qual=1)...")
    try:
        df = pb.pitching_stats(2026, qual=1)
        print(f"\nSuccess! Shape: {df.shape}")
        print(f"Columns: {list(df.columns[:10])} ...")
        print(f"Rows: {len(df)}")
        if len(df) > 0:
            print("\nFirst few pitchers:")
            print(
                df[["Name", "Team", "GS", "IP", "ERA"]].head(10).to_string(index=False)
            )
    except Exception as e:
        print(f"\nFailed: {type(e).__name__}: {e}")

print(f"\nCaptured URLs: {captured_urls}")
