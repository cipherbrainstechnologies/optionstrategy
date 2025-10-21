"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Table, TableHeader, TableRow, TableHead, TableCell, TableBody } from "@/components/ui/table";
import { RefreshCcw, Play, Pause, Search, Loader2 } from "lucide-react";

type Overview = {
  engineStatus: string;
  paperMode: boolean;
  lastScan: string;
  capital: number;
  openRiskPct: number;
  pnlDay: number;
  positions: number;
  signals: number;
  winRate: number;
  scanRunning?: boolean;
};

type Position = {
  symbol: string;
  entry: number;
  stop: number;
  t1: number;
  t2: number;
  ltp: number;
  status: string;
  pnl: number;
};

type ScanResult = {
  symbol: string;
  current_price: number;
  rsi: number;
  wma20: number;
  wma50: number;
  wma100: number;
  volume_ratio: number;
  atr_pct: number;
  patterns_found: number;
  filters_passed: number;
  breakout_detected: boolean;
  strategy_status: string;
  mother_high: number | null;
  mother_low: number | null;
  quality_score: number;
  scanned_at?: string;
};

type ScanResults = {
  total_instruments: number;
  scanned_instruments: ScanResult[];
  valid_setups: ScanResult[];
  breakouts: ScanResult[];
  errors: string[];
};

function StatCard(props: { title: string; value: string | number | boolean; suffix?: string; color?: string }) {
  const { title, value, suffix, color = "text-foreground" } = props;
  return (
    <Card className="flex-1 text-center shadow-sm">
      <CardHeader className="text-sm text-muted-foreground">{title}</CardHeader>
      <CardContent>
        <div className={"text-2xl font-bold " + color}>
          {value}
          {suffix}
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [engine, setEngine] = useState<string>("Starting");
  const [positions, setPositions] = useState<Position[]>([]);
  const [scanning, setScanning] = useState<boolean>(false);
  const [scanResults, setScanResults] = useState<ScanResults | null>(null);
  const [fyersAuthUrl, setFyersAuthUrl] = useState<string | null>(null);
  const [tradingMode, setTradingMode] = useState<'sandbox' | 'live'>('sandbox');

  async function refreshOverview() {
    try {
      const res = await fetch("/api/overview", { cache: "no-store" });
      if (!res.ok) return;
      const data: Overview = await res.json();
      setOverview(data);
      if (data && data.engineStatus) setEngine(data.engineStatus);
      if (data && data.scanRunning !== undefined) setScanning(data.scanRunning);
    } catch {}
  }

  async function refreshPositions() {
    try {
      const res = await fetch("/api/positions", { cache: "no-store" });
      if (!res.ok) return;
      const data: Position[] = await res.json();
      setPositions(Array.isArray(data) ? data : []);
    } catch {}
  }

  async function refreshScanResults() {
    try {
      const res = await fetch("/api/scan/results", { cache: "no-store" });
      if (!res.ok) return;
      const data: ScanResults = await res.json();
      // Ensure data has the expected structure
      if (data && typeof data === 'object') {
        setScanResults({
          total_instruments: data.total_instruments || 0,
          scanned_instruments: data.scanned_instruments || [],
          valid_setups: data.valid_setups || [],
          breakouts: data.breakouts || [],
          errors: data.errors || []
        });
      }
    } catch (error) {
      console.error('Error fetching scan results:', error);
    }
  }

  useEffect(() => {
    refreshOverview();
    refreshPositions();
    refreshScanResults();
    fetchFyersAuthUrl();
    const i = setInterval(() => {
      refreshOverview();
    }, 60000);
    return () => clearInterval(i);
  }, []);

  async function handleAction(action: string, symbol?: string) {
    if (action === "book-all") {
      const ok = confirm("Confirm booking profits for all positions?");
      if (!ok) return;
    }
    try {
      await fetch("/api/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, symbol }),
      });
      if (action === "refresh") {
        await Promise.all([refreshOverview(), refreshPositions()]);
      }
    } catch {}
  }

  async function fetchFyersAuthUrl() {
    try {
      const res = await fetch(`/api/fyers/auth-url?mode=${tradingMode}`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.auth_url) {
          setFyersAuthUrl(data.auth_url);
        }
      }
    } catch {}
  }

  async function toggleTradingMode() {
    const newMode = tradingMode === 'sandbox' ? 'live' : 'sandbox';
    setTradingMode(newMode);
    
    try {
      // Update backend trading mode
      const res = await fetch("/api/trading-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: newMode })
      });
      
      if (res.ok) {
        // Refresh auth URL for the new mode
        await fetchFyersAuthUrl();
        // Refresh overview to show updated mode
        await refreshOverview();
      }
    } catch (error) {
      console.error("Error toggling trading mode:", error);
      // Revert the toggle if API call failed
      setTradingMode(tradingMode);
    }
  }

  async function handleManualScan(dryRun: boolean = false) {
    if (scanning) {
      alert("Scan already in progress. Please wait for it to complete.");
      return;
    }
    
    try {
      setScanning(true);
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dry_run: dryRun }),
      });
      
      if (!res.ok) {
        const error = await res.json();
        alert(error.message || "Failed to start scan");
        setScanning(false);
        return;
      }
      
      const result = await res.json();
      alert(result.message || "Manual scan started");
      
      // Start polling for scan completion
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch("/api/scan/status", { cache: "no-store" });
          if (statusRes.ok) {
            const status = await statusRes.json();
            
            // Refresh scan results during scan to show progress
            await refreshScanResults();
            
            if (!status.running) {
              setScanning(false);
              clearInterval(pollInterval);
              await refreshOverview();
              await refreshPositions();
              await refreshScanResults();
            }
          }
        } catch {
          // Ignore polling errors
        }
      }, 2000);
      
    } catch {
      alert("Failed to start manual scan");
      setScanning(false);
    }
  }

  const o: Overview =
    overview || ({
      engineStatus: engine,
      paperMode: true,
      lastScan: "--:--",
      capital: 0,
      openRiskPct: 0,
      pnlDay: 0,
      positions: positions.length,
      signals: 0,
      winRate: 0,
    } as Overview);

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Institutional AI Trade Engine</h1>
        <div className="flex items-center space-x-3">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handleManualScan(false)}
            disabled={scanning}
          >
            {scanning ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {scanning ? "Scanning..." : "Manual Scan"}
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handleManualScan(true)}
            disabled={scanning}
          >
            {scanning ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {scanning ? "Scanning..." : "Dry Run Scan"}
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleAction("pause-resume")}>
            {engine === "Running" ? <Pause className="w-4 h-4 mr-1" /> : <Play className="w-4 h-4 mr-1" />}
            {engine === "Running" ? "Pause Engine" : "Resume Engine"}
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleAction("refresh")}>
            <RefreshCcw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Engine" value={engine} color={engine === "Running" ? "text-green-600" : "text-red-600"} />
        <StatCard title="Mode" value={o.paperMode ? "Paper" : "Live"} color="text-blue-600" />
        <StatCard title="Capital" value={"Rs " + o.capital} />
        <StatCard title="Open Risk" value={o.openRiskPct} suffix="%" />
        <StatCard title="Positions" value={o.positions} />
        <StatCard title="Signals Today" value={o.signals} />
        <StatCard title="Win Rate" value={o.winRate} suffix="%" />
        <StatCard title="PnL (Day)" value={"Rs " + o.pnlDay} color={o.pnlDay >= 0 ? "text-green-600" : "text-red-600"} />
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="scanner">Scanner</TabsTrigger>
          <TabsTrigger value="positions">Positions</TabsTrigger>
          <TabsTrigger value="ledger">Ledger</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <Card>
            <CardHeader>Market Context</CardHeader>
            <CardContent className="flex justify-between">
              <div>NIFTY50: 22,850 (+0.65%)</div>
              <div>BANKNIFTY: 48,920 (+0.54%)</div>
              <div>IV Zone: Calm</div>
              <div>Last Scan: {o.lastScan}</div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading Mode Toggle */}
        <div className="mt-4">
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="text-blue-800 font-semibold">🎯 Trading Mode</div>
                <div className="flex items-center space-x-3">
                  <span className={`text-sm font-medium ${tradingMode === 'sandbox' ? 'text-blue-900' : 'text-gray-500'}`}>
                    Sandbox
                  </span>
                  <button
                    onClick={toggleTradingMode}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      tradingMode === 'live' ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        tradingMode === 'live' ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                  <span className={`text-sm font-medium ${tradingMode === 'live' ? 'text-blue-900' : 'text-gray-500'}`}>
                    Live
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-blue-700 text-sm">
                  {tradingMode === 'sandbox' ? (
                    <>
                      🧪 <strong>Sandbox Mode:</strong> Safe testing environment with demo data. No real money involved.
                    </>
                  ) : (
                    <>
                      ⚡ <strong>Live Mode:</strong> Real trading with actual market data and real money. Use with caution!
                    </>
                  )}
                </p>
                <div className="text-blue-600 text-xs">
                  {tradingMode === 'sandbox' ? (
                    "Switch to Live mode when you're ready for real trading."
                  ) : (
                    "⚠️ Live trading mode is active. All trades will be executed with real money."
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {fyersAuthUrl && (
          <div className="mt-4">
            <Card className="border-orange-200 bg-orange-50">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="text-orange-800 font-semibold">🔑 FYERS Token Renewal Required</div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-orange-700 text-sm">
                    Your FYERS access token has expired. The system is currently using MockExchange for testing.
                  </p>
                  <div className="space-y-2">
                    <p className="text-orange-700 text-sm font-medium">To renew your token:</p>
                    <ol className="text-orange-700 text-sm space-y-1 ml-4">
                      <li>1. Click the authentication URL below</li>
                      <li>2. Complete the OAuth login process</li>
                      <li>3. Copy the new access token</li>
                      <li>4. Update FYERS_ACCESS_TOKEN in Render dashboard</li>
                      <li>5. Restart the application</li>
                    </ol>
                  </div>
                  <div className="mt-4">
                    <a 
                      href={fyersAuthUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors text-sm font-medium"
                    >
                      🔗 Open FYERS Authentication
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <TabsContent value="scanner" className="mt-4">
          <Card>
            <CardHeader className="flex justify-between">
              <div className="font-semibold">Scanner Control</div>
              <div className="flex items-center space-x-2">
                <div className="text-sm text-muted-foreground">
                  {scanning ? "Scan in progress..." : `Last scan: ${o.lastScan}`}
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={refreshScanResults}
                  disabled={scanning}
                >
                  <RefreshCcw className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h3 className="font-medium">Manual Scan</h3>
                  <p className="text-sm text-muted-foreground">
                    Run a complete scan of all enabled instruments to detect new 3WI patterns and breakouts.
                  </p>
                  <div className="flex space-x-2">
                    <Button 
                      onClick={() => handleManualScan(false)}
                      disabled={scanning}
                      className="flex-1"
                    >
                      {scanning ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
                      {scanning ? "Scanning..." : "Run Live Scan"}
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => handleManualScan(true)}
                      disabled={scanning}
                      className="flex-1"
                    >
                      {scanning ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
                      {scanning ? "Scanning..." : "Dry Run"}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="font-medium">Auto Scan Schedule</h3>
                  <div className="text-sm space-y-1">
                    <div className="flex justify-between">
                      <span>Pre-Open Scan:</span>
                      <span className="font-mono">09:25 IST</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Close Scan:</span>
                      <span className="font-mono">15:10 IST</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Frequency:</span>
                      <span>Daily (Mon-Fri)</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h3 className="font-medium mb-2">Scan Information</h3>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>• Manual scans can be run at any time, even outside market hours</p>
                  <p>• Live scans will create actual positions if breakouts are confirmed</p>
                  <p>• Dry run scans only detect patterns without creating positions</p>
                  <p>• Scan results are logged and can be viewed in the system logs</p>
                </div>
              </div>

              {scanResults && scanResults.scanned_instruments && scanResults.scanned_instruments.length > 0 ? (
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Latest Scan Results</h3>
                  <div className="text-sm text-muted-foreground mb-4">
                    Scanned {scanResults.total_instruments || 0} instruments • 
                    Found {scanResults.valid_setups?.length || 0} valid setups • 
                    {scanResults.breakouts?.length || 0} breakouts confirmed
                  </div>
                  
                  <div className="max-h-96 overflow-y-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Symbol</TableHead>
                          <TableHead>Price</TableHead>
                          <TableHead>RSI</TableHead>
                          <TableHead>Trend</TableHead>
                          <TableHead>Volume</TableHead>
                          <TableHead>Patterns</TableHead>
                          <TableHead>Filters</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Last Scanned</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {scanResults.scanned_instruments.map((result, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium">{result.symbol}</TableCell>
                            <TableCell>₹{result.current_price.toFixed(2)}</TableCell>
                            <TableCell className={result.rsi > 55 ? "text-green-600" : "text-red-600"}>
                              {result.rsi.toFixed(1)}
                            </TableCell>
                            <TableCell>
                              <div className="text-xs">
                                <div>WMA20: {result.wma20.toFixed(1)}</div>
                                <div>WMA50: {result.wma50.toFixed(1)}</div>
                                <div>WMA100: {result.wma100.toFixed(1)}</div>
                              </div>
                            </TableCell>
                            <TableCell className={result.volume_ratio >= 1.5 ? "text-green-600" : "text-red-600"}>
                              {result.volume_ratio.toFixed(1)}x
                            </TableCell>
                            <TableCell>{result.patterns_found}</TableCell>
                            <TableCell>
                              <span className={result.filters_passed === 4 ? "text-green-600" : "text-orange-600"}>
                                {result.filters_passed}/4
                              </span>
                            </TableCell>
                            <TableCell>
                              <span className={`px-2 py-1 rounded text-xs ${
                                result.strategy_status === "Breakout Confirmed" ? "bg-green-100 text-green-800" :
                                result.strategy_status === "Valid Setup" ? "bg-blue-100 text-blue-800" :
                                result.strategy_status.includes("Pattern") ? "bg-yellow-100 text-yellow-800" :
                                "bg-gray-100 text-gray-800"
                              }`}>
                                {result.strategy_status}
                              </span>
                            </TableCell>
                            <TableCell>
                              <span className="text-xs text-muted-foreground">
                                {result.scanned_at ? new Date(result.scanned_at).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                  second: '2-digit'
                                }) : '-'}
                              </span>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              ) : scanning ? (
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Scan in Progress</h3>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Scanning instruments... Please wait.</span>
                  </div>
                </div>
              ) : scanResults && scanResults.scanned_instruments && scanResults.scanned_instruments.length === 0 ? (
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Latest Scan Results</h3>
                  <div className="text-sm text-muted-foreground">
                    No scan results available. Run a manual scan to see detailed results.
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="positions" className="mt-4">
          <Card>
            <CardHeader className="flex justify-between">
              <div className="font-semibold">Active Positions</div>
              <div className="space-x-2">
                <Button size="sm" variant="outline" onClick={() => handleAction("trail-all")}>
                  Trail All
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleAction("book-all")}>
                  Book Profits
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Entry</TableHead>
                    <TableHead>Stop</TableHead>
                    <TableHead>T1/T2</TableHead>
                    <TableHead>LTP</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>PnL%</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {positions.map((p, i) => (
                    <TableRow key={i}>
                      <TableCell>{p.symbol}</TableCell>
                      <TableCell>{p.entry}</TableCell>
                      <TableCell>{p.stop}</TableCell>
                      <TableCell>
                        {p.t1}/{p.t2}
                      </TableCell>
                      <TableCell>{p.ltp}</TableCell>
                      <TableCell>{p.status}</TableCell>
                      <TableCell className={p.pnl >= 0 ? "text-green-600" : "text-red-600"}>{p.pnl}%</TableCell>
                      <TableCell>
                        <Button variant="outline" size="sm" onClick={() => handleAction("move-sl-be", p.symbol)}>
                          SL-&gt;BE
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
