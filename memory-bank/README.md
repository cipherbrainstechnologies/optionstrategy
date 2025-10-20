# 📚 Memory Bank - Institutional AI Trade Engine

## Overview

Welcome to the Memory Bank - the **source of truth** for all project knowledge, context, decisions, and patterns for the Institutional AI Trade Engine.

This memory bank is a living knowledge base that captures:
- ✅ **What** the system does (architecture)
- ✅ **How** it works (flows and patterns)
- ✅ **Why** decisions were made (decision log)
- ✅ **What challenges** we've faced (challenges log)

---

## 📂 Structure

```
memory-bank/
├── README.md                          # This file - navigation guide
├── architecture.md                    # Complete system architecture
├── implementation-complete.md         # Master spec compliance & deployment guide
├── decisions.md                       # Architectural decision log
├── challenges.md                      # Known challenges and solutions
├── flows/                             # Operational flow documents
│   ├── scanning-flow.md              # New setup detection flow
│   ├── tracking-flow.md              # Live position management flow
│   └── eod-flow.md                   # End-of-day reporting flow
└── patterns/                          # Implementation patterns
    ├── idempotency-pattern.md        # Ensuring repeatable operations
    └── risk-management-pattern.md    # Position sizing and risk controls
```

---

## 🚀 Quick Start

### For New Team Members
1. **Start here**: Read this README
2. **Understand the system**: Read `architecture.md`
3. **Learn the flows**: Read files in `flows/` directory
4. **Study patterns**: Read files in `patterns/` directory
5. **Context**: Read `decisions.md` and `challenges.md`

### For Active Development
1. **Before starting a task**: Read relevant flow and pattern documents
2. **During development**: Update documentation as you make changes
3. **After completion**: Document decisions and challenges discovered
4. **Before PR**: Ensure memory bank is updated

---

## 📖 Document Guide

### architecture.md

**Purpose**: Complete system architecture documentation

**Contains**:
- High-level system overview
- Module-by-module breakdown
- Data flow diagrams
- Technology stack
- Deployment architecture
- Security considerations
- Performance optimization
- Monitoring and observability

**When to read**:
- New to the project
- Designing new features
- Debugging system-wide issues
- Performance optimization

**When to update**:
- New modules added
- Architecture changes
- Technology stack updates
- Deployment changes

---

### implementation-complete.md

**Purpose**: Master specification compliance verification and deployment guide

**Contains**:
- Full compliance checklist against master spec
- Component-by-component verification
- Deployment instructions (quick start + production)
- Testing & validation procedures
- Performance metrics and targets
- Security and compliance checklist
- Production readiness confirmation

**When to read**:
- Verifying system completeness
- Preparing for deployment
- Understanding what has been built
- Planning testing phases

**When to update**:
- Major milestones completed
- Production deployment performed
- Performance benchmarks achieved
- New deployment procedures added

---

### decisions.md

**Purpose**: Architectural Decision Record (ADR)

**Contains**:
- All major decisions made
- Context and rationale for each decision
- Alternatives considered
- Current status (Active/Deprecated/Under Review)

**When to read**:
- Understanding why things are built a certain way
- Proposing architectural changes
- Evaluating alternatives

**When to update**:
- Making any significant architectural decision
- Deprecating old decisions
- Reviewing decisions quarterly

**Format**: Use Decision Template in file

---

### challenges.md

**Purpose**: Known issues, limitations, and solutions

**Contains**:
- All challenges discovered
- Impact assessment
- Workarounds and solutions
- Status tracking
- Lessons learned

**When to read**:
- Debugging issues
- Planning new features
- Risk assessment

**When to update**:
- Discovering new challenges
- Solving existing challenges
- Changing challenge status

**Format**: Use Challenge Template in file

---

### flows/

**Purpose**: Detailed operational flow documentation

**Files**:

1. **scanning-flow.md**
   - New 3WI setup detection
   - Pattern filtering
   - Position entry logic
   - Runs: 09:25 & 15:10 IST daily

2. **tracking-flow.md**
   - Live position management
   - Profit/loss rules
   - Stop loss management
   - Runs: Hourly 09:00-15:00 IST

3. **eod-flow.md**
   - Daily performance summary
   - Reporting and metrics
   - Ledger updates
   - Runs: 15:25 IST daily

**When to read**:
- Understanding specific operations
- Debugging flow issues
- Optimizing performance

**When to update**:
- Changing flow logic
- Adding new steps
- Modifying schedules

---

### patterns/

**Purpose**: Reusable implementation patterns

**Files**:

1. **idempotency-pattern.md**
   - Ensuring operations can be safely repeated
   - Database constraints
   - Alert deduplication
   - Testing strategies

2. **risk-management-pattern.md**
   - Position sizing formulas
   - Risk calculations
   - Target setting
   - Portfolio limits

**When to read**:
- Implementing new features
- Code review
- Understanding core patterns

**When to update**:
- New patterns emerge
- Pattern refinements
- Better examples found

---

## 🔄 Memory Bank Protocol

### Required Reads (Before Starting Any Task)

✅ **For Scanner Development**:
- architecture.md (Data Layer, Strategy Layer)
- flows/scanning-flow.md
- patterns/idempotency-pattern.md
- decisions.md (Decisions #001-#008)

✅ **For Tracker Development**:
- architecture.md (Execution Layer)
- flows/tracking-flow.md
- patterns/risk-management-pattern.md
- decisions.md (Risk-related)

✅ **For New Features**:
- architecture.md (full read)
- All relevant flow documents
- All relevant pattern documents
- decisions.md (to avoid re-deciding)

✅ **For Bug Fixes**:
- challenges.md (is this a known issue?)
- Relevant flow document
- architecture.md (affected module)

---

## 📝 Update Protocol

### When to Update

**Immediate Updates Required**:
- ✅ New architectural decision made
- ✅ Critical challenge discovered
- ✅ Flow logic changed
- ✅ New pattern established

**Regular Updates**:
- 🔄 Weekly: Review open challenges
- 🔄 Monthly: Update documentation for completed work
- 🔄 Quarterly: Review all decisions

### How to Update

1. **Edit the relevant file** in `memory-bank/`
2. **Follow the existing format** (templates provided)
3. **Be specific and clear** (future you will thank current you)
4. **Add examples** where helpful
5. **Update this README** if structure changes

### Pull Request Requirements

**Every PR must**:
1. ✅ Update relevant documentation
2. ✅ Reference memory bank docs in PR description
3. ✅ Document any new decisions
4. ✅ Document any new challenges
5. ✅ Include memory bank diff in PR

---

## 🎯 Usage Examples

### Example 1: Adding Partial Exit Feature

**Before coding**:
1. Read `flows/tracking-flow.md` (understand current logic)
2. Read `patterns/risk-management-pattern.md` (understand R-multiples)
3. Read `decisions.md` (Decision #008 on partial exits)
4. Read `challenges.md` (any related challenges?)

**During development**:
1. Update `flows/tracking-flow.md` with new partial exit step
2. Update `patterns/risk-management-pattern.md` with examples
3. Add any new challenges discovered to `challenges.md`

**After completion**:
1. Update `decisions.md` if any decisions made
2. Update `architecture.md` if module changed
3. Include memory bank updates in PR

---

### Example 2: Debugging Scanner Issue

**Investigation**:
1. Read `challenges.md` (known scanner issues?)
2. Read `flows/scanning-flow.md` (expected behavior)
3. Read `architecture.md` (scanner module details)
4. Read `patterns/idempotency-pattern.md` (idempotency working?)

**After fix**:
1. Add challenge to `challenges.md` if it was new
2. Update solution in `challenges.md` if it was known
3. Update `flows/scanning-flow.md` if logic changed

---

### Example 3: Proposing Architecture Change

**Before proposing**:
1. Read `decisions.md` (has this been decided before?)
2. Read `architecture.md` (understand current architecture)
3. Read `challenges.md` (what problems exist?)

**Proposal**:
1. Create draft decision in `decisions.md`
2. Mark status as "Under Review"
3. Reference in proposal document

**After approval**:
1. Update decision status to "Active"
2. Update `architecture.md` with changes
3. Deprecate old decision if applicable

---

## 📊 Memory Bank Health Metrics

### Current Status

**Last Updated**: 2025-01-22

**Completeness**:
- Architecture documentation: ✅ 100%
- Flow documentation: ✅ 100% (3/3 flows)
- Pattern documentation: ✅ 100% (2 core patterns)
- Decision log: ✅ 100% (8 active, 1 deprecated, 1 under review)
- Challenge log: ✅ 100% (10 documented)

**Maintenance**:
- Last review: 2025-01-22
- Next review: 2025-02-22 (monthly)
- Review cadence: Monthly
- Owners: All team members

---

## 🔍 Search Tips

### Finding Information

**To find**:
- "Why was this decision made?" → `decisions.md`
- "How does this flow work?" → `flows/*.md`
- "What's the pattern for X?" → `patterns/*.md`
- "Is this a known issue?" → `challenges.md`
- "Where is module Y?" → `architecture.md`

**Use grep**:
```bash
# Find all references to "scanner"
grep -r "scanner" memory-bank/

# Find decision about SQLite
grep -A 20 "SQLite" memory-bank/decisions.md

# Find idempotency examples
grep -A 10 "Example" memory-bank/patterns/idempotency-pattern.md
```

---

## 🤝 Contributing

### Everyone Should:
1. ✅ Read memory bank before starting tasks
2. ✅ Update memory bank as part of work
3. ✅ Review memory bank in PRs
4. ✅ Suggest improvements

### Document Owners:
- **architecture.md**: System Architect
- **decisions.md**: Tech Lead
- **challenges.md**: All team members
- **flows/*.md**: Module owners
- **patterns/*.md**: Senior developers

---

## 📚 Related Documentation

### In Project Root
- `README.md` - Project overview
- `QUICKSTART.md` - Quick start guide
- `IMPLEMENTATION_SUMMARY.md` - Implementation status

### In Code
- Inline documentation
- Function docstrings
- Module README files

### External
- Angel One SmartAPI docs
- Telegram Bot API docs
- Technical Analysis library docs

---

## 🎓 Learning Path

### Week 1: Understanding
1. Day 1-2: Read `architecture.md`
2. Day 3-4: Read all `flows/*.md`
3. Day 5: Read `patterns/*.md`

### Week 2: Context
1. Day 1-2: Read `decisions.md`
2. Day 3-4: Read `challenges.md`
3. Day 5: Review code with memory bank

### Week 3: Contributing
1. Day 1-2: Update documentation
2. Day 3-4: Review others' updates
3. Day 5: Propose improvements

---

## ✅ Checklist for Memory Bank Updates

**Before Coding**:
- [ ] Read relevant architecture section
- [ ] Read relevant flow document
- [ ] Read relevant pattern document
- [ ] Check decisions for related topics
- [ ] Check challenges for known issues

**During Coding**:
- [ ] Note decisions made
- [ ] Note challenges discovered
- [ ] Note new patterns used

**Before PR**:
- [ ] Update architecture.md (if architecture changed)
- [ ] Update relevant flow document (if flow changed)
- [ ] Update relevant pattern document (if pattern changed)
- [ ] Add decision to decisions.md (if decision made)
- [ ] Add challenge to challenges.md (if challenge found)
- [ ] Update this README (if structure changed)

---

## 🔗 Quick Links

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| [architecture.md](./architecture.md) | System architecture | As needed |
| [decisions.md](./decisions.md) | Decision log | Per decision |
| [challenges.md](./challenges.md) | Challenge tracking | As discovered |
| [flows/scanning-flow.md](./flows/scanning-flow.md) | Scanning flow | Per change |
| [flows/tracking-flow.md](./flows/tracking-flow.md) | Tracking flow | Per change |
| [flows/eod-flow.md](./flows/eod-flow.md) | EOD flow | Per change |
| [patterns/idempotency-pattern.md](./patterns/idempotency-pattern.md) | Idempotency | Per pattern |
| [patterns/risk-management-pattern.md](./patterns/risk-management-pattern.md) | Risk management | Per pattern |

---

## 💡 Best Practices

1. **Read First**: Always read relevant docs before coding
2. **Update Immediately**: Update docs as you make changes
3. **Be Specific**: Provide examples and details
4. **Link Together**: Reference related docs
5. **Review Regularly**: Monthly review of all docs
6. **Ask Questions**: If unclear, clarify and update

---

## 📞 Support

**Questions about memory bank?**
- Check this README first
- Review the specific document
- Ask in team chat
- Open an issue

**Found an error?**
- Fix it immediately
- Update the document
- Notify team

**Want to improve?**
- Suggest changes
- Submit PR
- Discuss in team meeting

---

**Remember**: The memory bank is only useful if it's kept up to date. Your future self (and teammates) will thank you! 🙏
