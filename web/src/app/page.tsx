"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Table, TableHeader, TableRow, TableHead, TableCell, TableBody } from "@/components/ui/table";
import { RefreshCcw, Play, Pause } from "lucide-react";

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

  async function refreshOverview() {
    try {
      const res = await fetch("/api/overview", { cache: "no-store" });
      if (!res.ok) return;
      const data: Overview = await res.json();
      setOverview(data);
      if (data && data.engineStatus) setEngine(data.engineStatus);
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

  useEffect(() => {
    refreshOverview();
    refreshPositions();
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
