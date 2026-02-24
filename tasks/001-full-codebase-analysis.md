# Task 001: Full Codebase Analysis & Documentation

## Objective
Perform a comprehensive, professional-grade analysis of the entire `claude_testing_1` codebase (Copper/Gold strategy) and produce detailed documentation in the `docs/` folder.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Main strategy: `copper_gold_strategy.cpp` (~89KB C++ file)
- Strategy notes: `copper_gold_strategy_v2.md`
- Data: `data/raw/futures/` (40+ futures CSVs) and `data/raw/macro/` (16 macro indicator CSVs)

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** Think and act like a senior quant at a top prop firm — rigorous, precise, skeptical. No hand-waving. Identify edge, risk, assumptions, and flaws with the same scrutiny you'd apply to a live trading system managing real capital.

## Execution — Deploy Agent Teams

### Agent 1: Strategy Logic Analyst
- Read and analyze `copper_gold_strategy.cpp` end-to-end
- Document: signal generation logic, entry/exit rules, position sizing, risk management
- Identify the core trading thesis (copper/gold ratio as macro indicator?)
- Map out all parameters, thresholds, and configurable knobs
- Output: `docs/strategy-logic.md`

### Agent 2: Data & Feature Engineer Analyst
- Analyze all CSV files in `data/raw/futures/` and `data/raw/macro/`
- Document: what each dataset is, time range, granularity, how they feed into the strategy
- Identify which data the strategy actually consumes vs what's available but unused
- Flag any data quality concerns (gaps, stale data, misaligned timestamps)
- Output: `docs/data-inventory.md`

### Agent 3: Strategy Design Document Analyst
- Read `copper_gold_strategy_v2.md` thoroughly
- Synthesize with findings from Agents 1 & 2
- Produce an executive-level strategy overview: thesis, universe, signals, risk framework, known limitations
- Include a section on potential improvements and research directions (think like a PM reviewing a new strategy for allocation)
- Output: `docs/strategy-overview.md`

### Agent 4: Architecture & Code Quality Reviewer
- Assess the C++ codebase structure, build system, dependencies
- Document code organization, key classes/functions, data flow architecture
- Flag: tech debt, hardcoded values, missing error handling, performance concerns
- Identify what would need to change to take this from research to production
- Output: `docs/architecture-review.md`

## Deliverables
All output goes in `/home/riley/Code/claude_testing_1/docs/`:
1. `strategy-logic.md` — Detailed signal/execution logic breakdown
2. `data-inventory.md` — Complete data catalog and quality assessment
3. `strategy-overview.md` — Executive strategy summary
4. `architecture-review.md` — Code architecture and quality review

## Instructions
- Deploy all 4 agents in parallel — they are independent
- Each agent writes its own output file directly
- After all agents complete, review outputs for consistency and completeness
- Do NOT commit — orchestrator (Terminal 1) handles git
