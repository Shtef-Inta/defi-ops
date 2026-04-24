"""Arkham-style live dashboard for defi-ops with AI Debate Feed.

Run standalone:
    python -m src.dashboard_server

Or integrate into daemon — it starts automatically on port 8765.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from src.db import get_conn

DB_PATH: Optional[str] = os.getenv("DB_PATH")
PORT = int(os.getenv("DASHBOARD_PORT", "8765"))


# ── Data queries ────────────────────────────────────────────────────────────

def _fetch_positions(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT pp.id, pp.protocol, pp.strategy, pp.entry_price, pp.size_usd,
               pp.status, pp.pnl_pct, pp.latest_price, pp.entry_at,
               ps.pnl_pct as snap_pnl, ps.captured_at as snap_at
        FROM paper_positions pp
        LEFT JOIN position_snapshots ps ON ps.position_id = pp.id
        WHERE pp.status = 'open'
        ORDER BY pp.entry_at DESC
        """
    ).fetchall()
    seen = {}
    for r in rows:
        pid = r[0]
        if pid not in seen or (r[10] and (seen[pid].get("snap_at") is None or r[10] > seen[pid]["snap_at"])):
            seen[pid] = {
                "id": pid,
                "protocol": r[1],
                "strategy": r[2] or "conservative",
                "entry_price": r[3],
                "size_usd": r[4],
                "status": r[5],
                "pnl_pct": r[8] if r[8] is not None else (r[6] or 0),
                "latest_price": r[7],
                "entry_at": r[8],
                "snap_pnl": r[9],
                "snap_at": r[10],
            }
    return list(seen.values())


def _fetch_stats(conn: sqlite3.Connection) -> dict:
    pos = conn.execute(
        """SELECT COUNT(*), COALESCE(SUM(size_usd), 0) FROM paper_positions WHERE status = 'open'"""
    ).fetchone()
    pnl = conn.execute(
        """SELECT COALESCE(SUM(pnl_pct * size_usd), 0) / NULLIF(SUM(size_usd), 0) FROM paper_positions WHERE status = 'open'"""
    ).fetchone()
    sigs = conn.execute(
        """SELECT COUNT(*) FROM signals WHERE captured_at >= datetime('now', '-24 hours')"""
    ).fetchone()
    ta = conn.execute(
        """SELECT COUNT(*) FROM technical_signals WHERE captured_at >= datetime('now', '-24 hours')"""
    ).fetchone()
    whale = conn.execute(
        """SELECT COUNT(*) FROM wallet_tx WHERE block_time >= datetime('now', '-24 hours')"""
    ).fetchone()
    clusters = conn.execute(
        """SELECT COUNT(*) FROM clusters WHERE status = 'open'"""
    ).fetchone()
    return {
        "open_positions": pos[0],
        "total_exposure": round(pos[1], 2),
        "avg_pnl_pct": round((pnl[0] or 0) * 100, 2),
        "signals_24h": sigs[0],
        "ta_signals_24h": ta[0],
        "whale_tx_24h": whale[0],
        "open_clusters": clusters[0],
    }


def _fetch_signals(conn: sqlite3.Connection, limit: int = 30) -> list[dict]:
    rows = conn.execute(
        """
        SELECT protocol, source_family, source_handle, content, sentiment, captured_at
        FROM signals
        ORDER BY captured_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "protocol": r[0] or "—",
            "source_family": r[1],
            "source_handle": r[2] or "—",
            "content": r[3][:200] if r[3] else "",
            "sentiment": r[4] or "neutral",
            "captured_at": r[5],
        }
        for r in rows
    ]


def _fetch_ta(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """
        SELECT protocol, indicator, signal, value, price, captured_at
        FROM technical_signals
        ORDER BY captured_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "protocol": r[0] or "—",
            "indicator": r[1],
            "signal": r[2],
            "value": round(r[3], 4) if r[3] is not None else None,
            "price": round(r[4], 6) if r[4] is not None else None,
            "captured_at": r[5],
        }
        for r in rows
    ]


def _fetch_clusters(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        """
        SELECT protocol, event_key, voice_weight, conviction, contradiction_flag, status, created_at
        FROM clusters
        WHERE status = 'open'
        ORDER BY voice_weight DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "protocol": r[0] or "—",
            "event_key": r[1],
            "voice_weight": round(r[2] or 0, 2),
            "conviction": r[3] or "SINGLE",
            "contradiction": bool(r[4]),
            "status": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]


def _fetch_strategy_breakdown(conn: sqlite3.Connection) -> dict:
    result = {}
    for strategy in ("conservative", "aggressive", "ultra"):
        row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(size_usd), 0), COALESCE(AVG(pnl_pct), 0)
            FROM paper_positions
            WHERE status = 'open' AND strategy = ?
            """,
            (strategy,),
        ).fetchone()
        result[strategy] = {
            "count": row[0],
            "exposure": round(row[1], 2),
            "avg_pnl_pct": round(row[2] * 100, 2) if row[2] else 0,
        }
    return result


def _fetch_debate_entries(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Read agent debate entries from memory file if present, else empty."""
    debate_path = Path(__file__).parent.parent / "state" / "memory" / "agent_debate.jsonl"
    entries = []
    if debate_path.exists():
        for line in debate_path.read_text().strip().split("\n")[-limit:]:
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return list(reversed(entries))


# ── HTTP Handler ────────────────────────────────────────────────────────────

class _DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/":
            self._serve_html()
        elif self.path == "/api/positions":
            self._serve_json(_fetch_positions(get_conn(DB_PATH)))
        elif self.path == "/api/stats":
            self._serve_json(_fetch_stats(get_conn(DB_PATH)))
        elif self.path == "/api/signals":
            self._serve_json(_fetch_signals(get_conn(DB_PATH)))
        elif self.path == "/api/ta":
            self._serve_json(_fetch_ta(get_conn(DB_PATH)))
        elif self.path == "/api/clusters":
            self._serve_json(_fetch_clusters(get_conn(DB_PATH)))
        elif self.path == "/api/strategies":
            self._serve_json(_fetch_strategy_breakdown(get_conn(DB_PATH)))
        elif self.path == "/api/debate":
            self._serve_json(_fetch_debate_entries(get_conn(DB_PATH)))
        else:
            self.send_error(404)

    def _serve_html(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(_DASHBOARD_HTML.encode("utf-8"))

    def _serve_json(self, data) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


# ── HTML Dashboard ──────────────────────────────────────────────────────────

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DEFI-OPS INTELLIGENCE</title>
<style>
:root {
  --bg: #050810;
  --bg-card: rgba(10, 14, 26, 0.85);
  --border: rgba(0, 212, 255, 0.12);
  --cyan: #00d4ff;
  --green: #00ff88;
  --red: #ff3366;
  --purple: #a855f7;
  --yellow: #fbbf24;
  --text: #e2e8f0;
  --text-dim: #64748b;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  min-height: 100vh;
  overflow-x: hidden;
}
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
  z-index: 0;
}
.container {
  position: relative;
  z-index: 1;
  max-width: 1600px;
  margin: 0 auto;
  padding: 24px;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.logo {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(135deg, var(--cyan), var(--purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-dim);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.last-update { color: var(--text-dim); font-size: 11px; margin-top: 4px; }

/* Cards */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  transition: border-color 0.3s, box-shadow 0.3s;
}
.card:hover {
  border-color: rgba(0,212,255,0.25);
  box-shadow: 0 0 20px rgba(0,212,255,0.05);
}
.card-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-dim);
  margin-bottom: 8px;
  font-family: var(--font-mono);
}
.card-value {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 700;
  color: var(--cyan);
}
.card-sub {
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 4px;
}
.positive { color: var(--green); }
.negative { color: var(--red); }
.neutral { color: var(--yellow); }

/* Tables */
.section-title {
  font-family: var(--font-mono);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--cyan);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  background: var(--cyan);
  border-radius: 2px;
}
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  padding: 12px 16px;
  font-family: var(--font-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-dim);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 10px 16px;
  border-bottom: 1px solid rgba(0,212,255,0.05);
  font-family: var(--font-mono);
  white-space: nowrap;
}
tr:hover td { background: rgba(0,212,255,0.03); }
tr:last-child td { border-bottom: none; }
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.badge-bullish { background: rgba(0,255,136,0.12); color: var(--green); border: 1px solid rgba(0,255,136,0.2); }
.badge-bearish { background: rgba(255,51,102,0.12); color: var(--red); border: 1px solid rgba(255,51,102,0.2); }
.badge-neutral { background: rgba(251,191,36,0.12); color: var(--yellow); border: 1px solid rgba(251,191,36,0.2); }
.badge-conservative { background: rgba(0,212,255,0.12); color: var(--cyan); border: 1px solid rgba(0,212,255,0.2); }
.badge-aggressive { background: rgba(168,85,247,0.12); color: var(--purple); border: 1px solid rgba(168,85,247,0.2); }
.badge-ultra { background: rgba(255,51,102,0.12); color: var(--red); border: 1px solid rgba(255,51,102,0.2); }

/* Two column layout */
.cols-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}
@media (max-width: 1100px) {
  .cols-2 { grid-template-columns: 1fr; }
}

/* Signal row */
.signal-row {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0,212,255,0.05);
  font-size: 13px;
}
.signal-row:last-child { border-bottom: none; }
.signal-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 4px;
}
.signal-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-dim);
}
.signal-text {
  color: var(--text);
  line-height: 1.5;
}

/* Debate feed */
.debate-entry {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(0,212,255,0.05);
}
.debate-entry:last-child { border-bottom: none; }
.debate-agent {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.debate-kimi { color: var(--cyan); }
.debate-codex { color: var(--purple); }
.debate-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
}
.debate-time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 4px;
}

/* Progress bar */
.bar-bg {
  background: rgba(0,212,255,0.08);
  border-radius: 4px;
  height: 6px;
  overflow: hidden;
  margin-top: 6px;
}
.bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--cyan), var(--purple));
  transition: width 0.5s ease;
}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <div class="logo">◈ DEFI-OPS INTELLIGENCE</div>
      <div class="last-update" id="lastUpdate">Initializing...</div>
    </div>
    <div class="status">
      <div class="status-dot"></div>
      <span>DAEMON LIVE</span>
    </div>
  </header>

  <!-- Metric Cards -->
  <div class="grid" id="statsGrid">
    <div class="card"><div class="card-label">Open Positions</div><div class="card-value" id="statPos">—</div><div class="card-sub" id="subPos">$— exposure</div></div>
    <div class="card"><div class="card-label">Avg P&L</div><div class="card-value" id="statPnl">—</div><div class="card-sub" id="subPnl">unrealized</div></div>
    <div class="card"><div class="card-label">Signals 24h</div><div class="card-value" id="statSig">—</div><div class="card-sub">news + onchain</div></div>
    <div class="card"><div class="card-label">TA Signals 24h</div><div class="card-value" id="statTa">—</div><div class="card-sub">RSI / EMA / MACD</div></div>
    <div class="card"><div class="card-label">Whale TX 24h</div><div class="card-value" id="statWhale">—</div><div class="card-sub">tracked wallets</div></div>
    <div class="card"><div class="card-label">Open Clusters</div><div class="card-value" id="statClusters">—</div><div class="card-sub">active events</div></div>
  </div>

  <!-- Strategy Breakdown + Positions -->
  <div class="cols-2">
    <div>
      <div class="section-title">Strategy Breakdown</div>
      <div class="table-wrap">
        <table id="stratTable">
          <thead><tr><th>Strategy</th><th>Positions</th><th>Exposure</th><th>Avg P&L</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    <div>
      <div class="section-title">Open Positions</div>
      <div class="table-wrap">
        <table id="posTable">
          <thead><tr><th>Protocol</th><th>Strategy</th><th>Entry</th><th>Current</th><th>P&L</th><th>Size</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- AI Debate Feed -->
  <div style="margin-bottom: 24px;">
    <div class="section-title">🧠 AI Agent Debate</div>
    <div class="table-wrap" id="debateWrap" style="max-height: 400px; overflow-y: auto;">
      <div class="signal-row" style="color: var(--text-dim); text-align: center; padding: 40px;">Waiting for agent debates...</div>
    </div>
  </div>

  <!-- Signals + TA -->
  <div class="cols-2">
    <div>
      <div class="section-title">Latest Signals</div>
      <div class="table-wrap" id="signalsWrap" style="max-height: 400px; overflow-y: auto;">
      </div>
    </div>
    <div>
      <div class="section-title">Technical Analysis</div>
      <div class="table-wrap" id="taWrap" style="max-height: 400px; overflow-y: auto;">
      </div>
    </div>
  </div>

  <!-- Clusters -->
  <div style="margin-bottom: 24px;">
    <div class="section-title">Active Protocol Clusters</div>
    <div class="table-wrap">
      <table id="clusterTable">
        <thead><tr><th>Protocol</th><th>Event</th><th>Voice Weight</th><th>Conviction</th><th>Status</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

</div>

<script>
const API = '';
function $_(id) { return document.getElementById(id); }

function fmtTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit'}) + ' ' + d.toLocaleDateString('ru-RU');
}

function fmtPct(v) {
  const s = (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
  return `<span class="${v >= 0 ? 'positive' : 'negative'}">${s}</span>`;
}

async function loadStats() {
  const data = await fetch(API + '/api/stats').then(r => r.json());
  $_('statPos').textContent = data.open_positions;
  $_('subPos').textContent = '$' + data.total_exposure.toLocaleString() + ' exposure';
  $_('statPnl').innerHTML = fmtPct(data.avg_pnl_pct).replace(/<span/, '<span style="font-size:28px"');
  $_('statPnl').className = 'card-value ' + (data.avg_pnl_pct >= 0 ? 'positive' : 'negative');
  $_('statSig').textContent = data.signals_24h;
  $_('statTa').textContent = data.ta_signals_24h;
  $_('statWhale').textContent = data.whale_tx_24h;
  $_('statClusters').textContent = data.open_clusters;
  $_('lastUpdate').textContent = 'Last update: ' + new Date().toLocaleTimeString('ru-RU');
}

async function loadStrategies() {
  const data = await fetch(API + '/api/strategies').then(r => r.json());
  const tbody = $_('stratTable').querySelector('tbody');
  const names = {conservative: 'Conservative', aggressive: 'Aggressive', ultra: 'Ultra'};
  const badges = {conservative: 'badge-conservative', aggressive: 'badge-aggressive', ultra: 'badge-ultra'};
  tbody.innerHTML = Object.entries(data).map(([k, v]) => `
    <tr>
      <td><span class="badge ${badges[k]}">${names[k]}</span></td>
      <td>${v.count}</td>
      <td>$${v.exposure.toLocaleString()}</td>
      <td>${fmtPct(v.avg_pnl_pct)}</td>
    </tr>
  `).join('');
}

async function loadPositions() {
  const data = await fetch(API + '/api/positions').then(r => r.json());
  const tbody = $_('posTable').querySelector('tbody');
  const badges = {conservative: 'badge-conservative', aggressive: 'badge-aggressive', ultra: 'badge-ultra'};
  tbody.innerHTML = data.map(p => `
    <tr>
      <td><strong>${p.protocol.toUpperCase()}</strong></td>
      <td><span class="badge ${badges[p.strategy] || 'badge-neutral'}">${p.strategy}</span></td>
      <td>$${p.entry_price?.toFixed(4) || '—'}</td>
      <td>$${p.latest_price?.toFixed(4) || '—'}</td>
      <td>${fmtPct((p.pnl_pct || 0) * 100)}</td>
      <td>$${p.size_usd?.toLocaleString() || '—'}</td>
    </tr>
  `).join('');
}

async function loadDebate() {
  const data = await fetch(API + '/api/debate').then(r => r.json());
  const wrap = $_('debateWrap');
  if (!data.length) {
    wrap.innerHTML = '<div class="signal-row" style="color: var(--text-dim); text-align: center; padding: 40px;">Waiting for agent debates...</div>';
    return;
  }
  wrap.innerHTML = data.map(d => `
    <div class="debate-entry">
      <div class="debate-agent debate-${d.agent?.toLowerCase() || 'kimi'}">${d.agent || 'AGENT'} → ${d.topic || 'General'}</div>
      <div class="debate-text">${d.text || d.message || ''}</div>
      <div class="debate-time">${fmtTime(d.timestamp || d.captured_at)}</div>
    </div>
  `).join('');
}

async function loadSignals() {
  const data = await fetch(API + '/api/signals').then(r => r.json());
  const wrap = $_('signalsWrap');
  const badges = {bullish: 'badge-bullish', bearish: 'badge-bearish', neutral: 'badge-neutral'};
  wrap.innerHTML = data.map(s => `
    <div class="signal-row">
      <div class="signal-meta">
        <span class="badge ${badges[s.sentiment] || 'badge-neutral'}">${s.sentiment}</span>
        <strong>${s.protocol.toUpperCase()}</strong>
        <span class="signal-time">${fmtTime(s.captured_at)}</span>
      </div>
      <div class="signal-text">${s.content}</div>
    </div>
  `).join('');
}

async function loadTA() {
  const data = await fetch(API + '/api/ta').then(r => r.json());
  const wrap = $_('taWrap');
  const badges = {bullish_cross: 'badge-bullish', bearish_cross: 'badge-bearish', oversold: 'badge-bullish', overbought: 'badge-bearish', bullish_spike: 'badge-bullish', bearish_spike: 'badge-bearish'};
  wrap.innerHTML = data.map(t => `
    <div class="signal-row">
      <div class="signal-meta">
        <span class="badge ${badges[t.signal] || 'badge-neutral'}">${t.indicator}</span>
        <strong>${t.protocol.toUpperCase()}</strong>
        <span class="signal-time">${fmtTime(t.captured_at)}</span>
      </div>
      <div class="signal-text">${t.signal} @ $${t.price?.toFixed(4) || '—'} (value=${t.value?.toFixed(2) || '—'})</div>
    </div>
  `).join('');
}

async function loadClusters() {
  const data = await fetch(API + '/api/clusters').then(r => r.json());
  const tbody = $_('clusterTable').querySelector('tbody');
  tbody.innerHTML = data.map(c => `
    <tr>
      <td><strong>${c.protocol.toUpperCase()}</strong></td>
      <td>${c.event_key}</td>
      <td>${c.voice_weight.toFixed(2)}</td>
      <td><span class="badge badge-neutral">${c.conviction}</span></td>
      <td>${c.contradiction ? '<span class="negative">⚠ CONTRA</span>' : '<span class="positive">✓ CLEAR</span>'}</td>
    </tr>
  `).join('');
}

async function refresh() {
  try {
    await Promise.all([loadStats(), loadStrategies(), loadPositions(), loadDebate(), loadSignals(), loadTA(), loadClusters()]);
  } catch(e) {
    console.error('Refresh failed:', e);
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""


# ── Server startup ──────────────────────────────────────────────────────────

def start_dashboard_server(port: Optional[int] = None, db_path: Optional[str] = None) -> threading.Thread:
    global DB_PATH
    if db_path:
        DB_PATH = db_path
    p = port or PORT
    server = HTTPServer(("0.0.0.0", p), _DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[Dashboard] http://0.0.0.0:{p}/")
    return thread


def main() -> None:
    start_dashboard_server()
    print("Press Ctrl+C to stop")
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
