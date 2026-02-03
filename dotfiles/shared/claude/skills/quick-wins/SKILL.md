---
name: quick-wins
description: This agent helps you identify linear issues that are straightforward enough to tackle without major architectural decisions or product discussions, perfect for quick focused work sessions.
metadata:
  version: "1.0"
  category: "development"
  tags: ["linear", "tickets", "development", "issue-management", "quick-wins"]
---

# Quick Wins Issue Finder Skill

## Overview

This skill helps you identify simple, actionable coding tasks perfect for focused work sessions. It analyzes your Linear workspace to find issues that can be completed in a single sitting without requiring complex architectural decisions or stakeholder discussions. The goal is to help you make productive use of focused time and complete satisfying work.

**IMPORTANT:** All Linear searches should target the **Platform** team for tickets, specifically focusing on:
- **Keep The Lights On (KTLO)** - Operational improvements, bug fixes, maintenance tasks, technical debt reduction
- **AI Tooling** - AI development tools, LLM integrations, automation improvements, ML infrastructure

## When to Use This Skill

- **Finding quick wins** - Need a satisfying task to tackle in a short session
- **Focused work sessions** - Want productive 10-30 minute coding sessions
- **Low-complexity work** - Looking for tasks that don't require major decisions
- **Immediate-start tasks** - Need issues with enough context to begin right away
- **Motivation boost** - Want to complete work and see green commits
- **Issue triage** - Filtering backlog for straightforward improvements
- **Productive downtime** - Making the most of small blocks of available time

---

## Phase 1: Issue Discovery

### 1.1 Search Linear Workspace

**Search for Open Issues:**
The skill will automatically search your Linear workspace (Platform team) for open issues using Linear MCP tools. It focuses on:
- Open status tickets
- Recent activity
- Clear titles and descriptions
- Issues without blockers
- **Project focus:** "Keep The Lights On" OR "AI Tooling" projects

**Initial Filtering:**
Issues are evaluated based on:
- Title clarity
- Description completeness
- Assigned status
- Priority level
- Labels and tags
- Project categorization (KTLO vs AI Tooling)

### 1.2 Evaluate Complexity

**Complexity Assessment Criteria:**
Each issue is scored on:
- Scope definition (clear vs. ambiguous)
- Technical complexity (straightforward vs. intricate)
- Decision requirements (none vs. stakeholder input needed)
- Context availability (complete vs. missing information)

---

## Phase 2: Issue Selection Criteria

### 2.1 Must-Have Qualities

**Prioritize Issues That:**
- ✅ Have clear, well-defined scope
- ✅ Appear to be bug fixes, small features, or straightforward improvements
- ✅ Don't require architectural decisions or new product direction
- ✅ Can likely be completed in a single focused session (10-30 minutes)
- ✅ Have enough context to start work immediately
- ✅ Belong to the **Platform** team
- ✅ Fall under **Keep The Lights On** (maintenance, ops, tech debt) OR **AI Tooling** (LLM integrations, automation)

### 2.2 Red Flags to Avoid

**Avoid Issues That:**
- ❌ Involve major refactoring or system redesign
- ❌ Require extensive stakeholder input or approval
- ❌ Have ambiguous requirements or success criteria
- ❌ Touch critical infrastructure without clear testing paths
- ❌ Need design mockups or UX decisions
- ❌ Are marked as "Complex" or have high uncertainty

---

## Phase 3: Analysis Workflow

### 3.1 Initial Scan

**Step 1: Fetch Open Issues**
```
Use Linear MCP tools to query open issues in the Platform team
Filter by status: "To Do", "In Progress", "Backlog"
Filter by project: "Keep The Lights On" OR "AI Tooling"
Sort by recent activity or priority
```

**Step 2: Title and Description Review**
```
Scan titles for keywords: "fix", "improve", "update", "add"
Check descriptions for clarity and completeness
Identify issues with clear acceptance criteria
```

### 3.2 Deep Evaluation

**For Each Candidate Issue, Assess:**

**Estimated Complexity:**
- Simple: Single file change, clear fix, minimal testing
- Medium: Multiple files, moderate testing, some investigation
- Complex: Extensive changes, architecture decisions (skip these)

**Missing Information:**
- Are requirements clear?
- Is the bug reproducible?
- Are success criteria defined?
- Is technical context provided?

**Confidence Level:**
- High: Clear scope, straightforward implementation, minimal unknowns
- Medium: Some investigation needed, but achievable
- Low: Ambiguous or complex (skip these)

**Key Areas Affected:**
- Which files/modules will be touched?
- What tests need to be updated?
- Are there obvious integration points?

---

## Phase 4: Output Format

### 4.1 Issue Recommendation Template

For each recommended issue:

```
⚡ **Issue Title** [Issue ID]
📝 **The Pitch:** A 2-3 sentence summary of what needs to be done and why this is a quick win

⚡ **Quick Win Factor:** Simple/Medium (never recommend Complex)

❓ **Missing Info:** What you need from the user (or "None - ready to go!")

🎯 **Success Probability:** High/Medium/Low with brief reasoning

💡 **Suggested Approach:** 1-2 sentences on how to tackle this
```

**KTLO Example:**

```
⚡ **Fix loading spinner animation bug** [PLAT-123]
📝 **The Pitch:** The loading spinner isn't centering properly on mobile devices. A quick CSS fix to adjust flexbox alignment will solve this. Clear bug report with screenshots. [Keep The Lights On]

⚡ **Quick Win Factor:** Simple

❓ **Missing Info:** None - ready to go!

🎯 **Success Probability:** High - Single CSS file change, visual verification only

💡 **Suggested Approach:** Update the loading-spinner.css file to use proper flexbox centering, test on mobile viewport
```

**AI Tooling Example:**

```
⚡ **Add retry logic to LLM API calls** [PLAT-456]
📝 **The Pitch:** Current LLM API client doesn't handle transient failures well. Add exponential backoff retry for rate limits and timeouts. Spec is clear, implementation is straightforward. [AI Tooling]

⚡ **Quick Win Factor:** Simple

❓ **Missing Info:** None - retry strategy is documented in the issue

🎯 **Success Probability:** High - Single file change with clear testing criteria

💡 **Suggested Approach:** Wrap API calls with tenacity decorator, add unit tests for retry behavior
```

### 4.2 Final Recommendations

After presenting 1-3 options, provide:

**Personal Pick:**
Which issue you'd personally tackle now and why

**Getting Started:**
A brief plan_mode prompt the user could use to begin work immediately

---

## Phase 5: Communication Guidelines

### 5.1 Tone and Style

**Keep It Scannable:**
- Use concise descriptions
- Bullet points over paragraphs
- Clear visual hierarchy with emojis
- Quick-to-read summaries

---

## 📚 Reference Materials

### Essential Linear Queries

**Finding Simple Issues:**
- Search for labels: "bug", "ktlo", "ai-tooling"
- Filter by team: **Platform**
- Filter by project: **"Keep The Lights On"** OR **"AI Tooling"**
- Status: "To Do", "Backlog", "Planning"
- Priority: Low to Medium (avoid High/Urgent for quick wins)

### Project-Specific Focus

**Keep The Lights On (KTLO) - Look for:**
- Bug fixes and stability improvements
- Performance optimizations
- Tech debt reduction
- Monitoring and alerting improvements
- Documentation updates
- Dependency updates
- Test coverage improvements
- CI/CD pipeline fixes

**AI Tooling - Look for:**
- LLM integration improvements
- Prompt optimization tasks
- API client enhancements
- Model evaluation tooling
- Automation script improvements
- Claude Code skill development
- MCP server improvements
- AI workflow optimizations

### Complexity Indicators

**Simple Issues (Recommend):**
- Single file changes
- Clear reproduction steps
- Obvious fix location
- Minimal dependencies
- Visual bugs with screenshots

**Medium Issues (Consider):**
- 2-3 file changes
- Some investigation needed
- Clear acceptance criteria
- Defined testing approach

**Complex Issues (Avoid):**
- Architectural decisions needed
- Multiple integration points
- Ambiguous requirements
- Extensive refactoring
- Critical infrastructure changes

### Best Practices

- [ ] Always search the **Platform** team for tickets
- [ ] Filter to **"Keep The Lights On"** OR **"AI Tooling"** projects only
- [ ] Recommend 1-3 issues maximum to avoid overwhelm
- [ ] Prioritize "High" success probability
- [ ] Verify issues have clear acceptance criteria
- [ ] Check for available context (screenshots, logs, etc.)
- [ ] Suggest a starting plan_mode prompt
 