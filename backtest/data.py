import warnings
import pandas as pd

OHLCV = ['open','high','low','close','volume']

def load_csv(path: str, source_timezone: str = 'UTC') -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = {'timestamp', *OHLCV} - set(df.columns)
    if missing:
        raise ValueError(f'missing required columns: {sorted(missing)}')
    ts = pd.to_datetime(df['timestamp'], errors='raise')
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(source_timezone)
    else:
        ts = ts.dt.tz_convert(source_timezone)
    out = df[OHLCV].copy()
    out.index = ts
    out = out.sort_index()
    if out.index.has_duplicates:
        warnings.warn('Duplicate timestamp rows found; keeping the last row for each duplicate timestamp.', RuntimeWarning, stacklevel=2)
        out = out[~out.index.duplicated(keep='last')]
    return out.astype(float)


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    return df.resample(timeframe, label='left', closed='left').agg(
        {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
    ).dropna(subset=['open','high','low','close'])
