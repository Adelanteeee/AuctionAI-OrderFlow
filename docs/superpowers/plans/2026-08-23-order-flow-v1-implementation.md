# AuctionAI Order Flow v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Pine Script v6 Order Flow indicator with hybrid Delta, CVD, Volume, Absorption, Effort vs Result, Divergence, candle coloring, and selectable Daily/Session Volume Profile.

**Architecture:** Build two coordinated overlay scripts with equivalent downstream logic: a Universal edition using lower-timeframe intrabar Delta estimation, and a Premium/Ultimate edition using TradingView `request.footprint()`. This split preserves public usability because lower-tier accounts cannot use scripts that request footprint data. Both editions expose the same order-flow evidence model and profile settings.

**Tech Stack:** TradingView Pine Script v6, GitHub

**Spec:** `docs/superpowers/specs/2026-08-23-order-flow-v1-design.md`

## Global Constraints

- Do not modify the existing `AuctionAI` repository or v5.0 codebase.
- Repository is public and standalone: `Adelanteeee/AuctionAI-OrderFlow`.
- Do not copy third-party LuxAlgo source code; use only independently implemented concepts.
- Indicator is evidence-oriented and must not emit trade entry/exit commands.
- Active Delta source must be visible in diagnostics.
- Volume-derived evidence must degrade to neutral/NA when usable volume data is unavailable.
- Pine Script version must be `//@version=6`.

---

### Task 1: Repository Skeleton and Universal Core
- [x] Create README and methodology/limitations docs.
- [x] Create `tradingview/AuctionAI_OrderFlow_v1.pine`.
- [x] Add lower-timeframe Delta, Volume, CVD, Effort vs Result, Absorption, Divergence and candle coloring.
- [x] Add diagnostics and Data Window outputs.

### Task 2: Daily / Session Volume Profile
- [x] Add Off / Daily / Session modes.
- [x] Add Asia / London / New York / Custom sessions.
- [x] Add Levels Only / Full Profile displays.
- [x] Add POC / VAH / VAL calculation and profile histogram.

### Task 3: Footprint Edition
- [x] Create `tradingview/AuctionAI_OrderFlow_v1_Footprint.pine`.
- [x] Replace only the canonical Delta acquisition with `request.footprint()`.
- [x] Preserve equivalent downstream CVD, Absorption, Divergence, coloring and profile logic.
- [x] Expose `TradingView Footprint` as the active source.

### Task 4: Validation / Release
- [x] Static sanity checks: Pine v6 header, no conflict markers, deterministic single `barcolor()` call.
- [ ] Compile Universal edition in TradingView Pine Editor.
- [ ] Compile Footprint edition on a Premium/Ultimate TradingView account.
- [ ] Test XAUUSD, FX, index/futures-compatible symbol and crypto.
- [ ] Adjust thresholds after chart validation if needed.

## Release Gate

The branch is ready for TradingView compile/runtime validation. Do not merge to `main` until the Universal edition compiles successfully and runtime behavior is checked on at least one liquid symbol. The Footprint edition requires Premium/Ultimate for its own compile/runtime validation.