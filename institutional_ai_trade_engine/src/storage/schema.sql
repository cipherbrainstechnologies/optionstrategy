CREATE TABLE instruments(
  id INTEGER PRIMARY KEY,
  symbol TEXT UNIQUE,
  exchange TEXT DEFAULT 'NSE',
  enabled INTEGER DEFAULT 1
);

CREATE TABLE setups(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  week_start TEXT,
  mother_high REAL,
  mother_low REAL,
  inside_weeks INTEGER,
  matched_filters INTEGER,
  comment TEXT
);

CREATE TABLE positions(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  status TEXT,
  entry_price REAL,
  stop REAL,
  t1 REAL,
  t2 REAL,
  qty INTEGER,
  capital REAL,
  plan_size REAL,
  opened_ts TEXT,
  closed_ts TEXT,
  pnl REAL,
  rr REAL
);

CREATE TABLE ledger(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  opened_ts TEXT,
  closed_ts TEXT,
  pnl REAL,
  rr REAL,
  tag TEXT
);