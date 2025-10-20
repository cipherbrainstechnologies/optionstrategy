-- Instruments table (trading universe + portfolio)
CREATE TABLE IF NOT EXISTS instruments(
  id INTEGER PRIMARY KEY,
  symbol TEXT UNIQUE NOT NULL,
  exchange TEXT DEFAULT 'NSE',
  enabled INTEGER DEFAULT 1,
  in_portfolio INTEGER DEFAULT 0,
  avg_portfolio_price REAL,
  portfolio_qty INTEGER
);

CREATE INDEX IF NOT EXISTS idx_instruments_enabled ON instruments(enabled);
CREATE INDEX IF NOT EXISTS idx_instruments_portfolio ON instruments(in_portfolio);

-- Setups table (detected 3WI patterns)
CREATE TABLE IF NOT EXISTS setups(
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  week_start TEXT NOT NULL,
  mother_high REAL NOT NULL,
  mother_low REAL NOT NULL,
  inside_weeks INTEGER DEFAULT 2,
  matched_filters INTEGER DEFAULT 0,
  quality_score REAL,
  comment TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_setups_symbol ON setups(symbol);
CREATE INDEX IF NOT EXISTS idx_setups_week ON setups(week_start);

-- Signals table (trade signals)
CREATE TABLE IF NOT EXISTS signals(
  id INTEGER PRIMARY KEY,
  signal_id TEXT UNIQUE NOT NULL,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  direction TEXT NOT NULL,
  trigger_price REAL NOT NULL,
  stop_loss REAL NOT NULL,
  target1 REAL NOT NULL,
  target2 REAL NOT NULL,
  confidence REAL NOT NULL,
  pattern_type TEXT NOT NULL,
  status TEXT DEFAULT 'PENDING',
  trigger_ts TEXT NOT NULL,
  triggered_at TEXT,
  metadata TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_trigger ON signals(trigger_ts);

-- Orders table
CREATE TABLE IF NOT EXISTS orders(
  id INTEGER PRIMARY KEY,
  order_id TEXT UNIQUE NOT NULL,
  broker_order_id TEXT,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty INTEGER NOT NULL,
  order_type TEXT NOT NULL,
  price REAL,
  status TEXT NOT NULL,
  filled_qty INTEGER DEFAULT 0,
  avg_fill_price REAL DEFAULT 0,
  tag TEXT,
  signal_id TEXT,
  position_id INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_broker ON orders(broker_order_id);
CREATE INDEX IF NOT EXISTS idx_orders_signal ON orders(signal_id);

-- Fills table (order executions)
CREATE TABLE IF NOT EXISTS fills(
  id INTEGER PRIMARY KEY,
  fill_id TEXT UNIQUE NOT NULL,
  order_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty INTEGER NOT NULL,
  price REAL NOT NULL,
  filled_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fills_order ON fills(order_id);
CREATE INDEX IF NOT EXISTS idx_fills_symbol ON fills(symbol);

-- Positions table (enhanced)
CREATE TABLE IF NOT EXISTS positions(
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  status TEXT NOT NULL,
  entry_price REAL NOT NULL,
  stop REAL NOT NULL,
  t1 REAL NOT NULL,
  t2 REAL NOT NULL,
  qty INTEGER NOT NULL,
  original_qty INTEGER NOT NULL,
  capital REAL NOT NULL,
  plan_size REAL NOT NULL,
  opened_ts TEXT NOT NULL,
  closed_ts TEXT,
  pnl REAL DEFAULT 0,
  rr REAL DEFAULT 0,
  exit_reason TEXT,
  signal_id TEXT,
  metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_opened ON positions(opened_ts);
CREATE INDEX IF NOT EXISTS idx_positions_signal ON positions(signal_id);

-- Ledger table (learning ledger)
CREATE TABLE IF NOT EXISTS ledger(
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  opened_ts TEXT NOT NULL,
  closed_ts TEXT NOT NULL,
  pnl REAL NOT NULL,
  rr REAL NOT NULL,
  tag TEXT,
  entry_price REAL,
  exit_price REAL,
  qty INTEGER,
  hold_duration_hours REAL,
  metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_ledger_symbol ON ledger(symbol);
CREATE INDEX IF NOT EXISTS idx_ledger_closed ON ledger(closed_ts);
CREATE INDEX IF NOT EXISTS idx_ledger_tag ON ledger(tag);