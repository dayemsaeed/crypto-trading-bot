# Freqtrade Trend-Following Bot (Binance Spot)

Long-only swing bot on 4h candles across 8 major USDT pairs. Strategy:
`user_data/strategies/TrendFollowStrategy.py` — EMA50/200 trend filter, MACD
confirmation, RSI pullback entries, volume filter, trailing stop. Tuned
parameters live in `TrendFollowStrategy.json` (auto-loaded).

## Daily driving

```bash
docker compose up -d        # start (currently DRY-RUN — simulated $1000 wallet)
docker compose logs -f      # watch
docker compose down         # stop
```

Everything is on port 8080:

- **Overview**: http://127.0.0.1:8080/dashboard.html — custom at-a-glance page
  (`dashboard/index.html`, mounted into FreqUI's static dir): wallet, profit
  curve, open/closed trades, per-pair entry-signal checklist, and a link to FreqUI.
- **FreqUI** (deep dive): http://127.0.0.1:8080 — username `freqtrader`, password in
  `user_data/config.json` under `api_server.password`. Charts overlay the
  strategy's EMA50/200, RSI, and MACD via `plot_config` in the strategy.

## Re-backtest / re-tune

```bash
docker compose run --rm freqtrade download-data --config /freqtrade/user_data/config.json --timeframe 4h --timerange 20240101-
docker compose run --rm freqtrade backtesting --config /freqtrade/user_data/config.json --strategy TrendFollowStrategy --timerange 20240201-
docker compose run --rm freqtrade hyperopt --config /freqtrade/user_data/config.json --strategy TrendFollowStrategy --hyperopt-loss SharpeHyperOptLoss --spaces buy sell --epochs 60 --timerange 20240201- -j 4
```

Last backtest (2024-02 → 2026-07): +3.37%, profit factor 1.11, 64 trades,
max drawdown ~10%. Market did +3.08% over the same window — this is roughly
market-matching with lower drawdown, not a money printer.

## Go-live checklist (do NOT skip)

1. Run dry-run for **at least 2–4 weeks**; results should roughly match backtest expectations.
2. Create a Binance API key with **spot trade permission only** — withdrawals
   disabled, IP-restricted to your machine.
3. Put the key/secret in `user_data/config.json` (`exchange.key` / `exchange.secret`).
   This file is gitignored so it won't be committed, but double-check `git status`
   before any `git add` once real keys are in it.
4. Set `"dry_run": false` in `user_data/config.json`.
5. Fund with only what you can afford to lose entirely. Keep `max_open_trades: 4`.
6. `docker compose up -d` and check logs show "Dry run is disabled" and your real balance.

No trading bot guarantees profit. Crypto is volatile; past backtest
performance does not predict future results.
