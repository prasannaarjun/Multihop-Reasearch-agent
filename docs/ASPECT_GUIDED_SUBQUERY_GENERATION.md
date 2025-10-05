# Aspect-Guided Subquery Generation

## Overview

This feature implements **dynamic, aspect-guided subquery generation** that explicitly targets uncovered aspects until all core aspects are addressed or the hop budget is exhausted. This replaces the previous fixed-length, upfront subquery generation approach.

## Problem Solved

**Before**: The system generated a fixed number of generic subqueries upfront, leading to:
- Uncovered aspects (like "Definition of Attention Heads" or "Query/Key/Value vectors") never being addressed
- Wasted hops on redundant or tangentially related queries
- No feedback loop between retrieval and subquery generation

**After**: The system dynamically generates subqueries based on which aspects remain uncovered:
- Each hop explicitly targets the most important uncovered aspect
- Core aspects are prioritized over optional ones
- System stops when all core aspects are covered

## Architecture

### 1. Aspect-to-Subquery Mapping

Each uncovered aspect is converted into a targeted subquery using either:

**LLM-based (preferred)**:
```python
system_prompt = "Generate focused subqueries for uncovered aspects..."
response = llm_client.generate_text(prompt, system_prompt)
# Returns: SUBQUERY: What is an attention head? | ASPECT: Definition of Attention Heads
```

**Template-based (fallback)**:
```python
def _aspect_to_subquery_template(aspect, main_question):
    if aspect.type == 'definition':
        return f"What is {topic}?"
    elif aspect.type == 'comparison':
        return f"What are the differences in {topic}?"
    # ... more templates
```

### 2. Prioritization Logic

Aspects are sorted by importance before subquery generation:

```python
# Sort by importance (core aspects first)
sorted_aspects = sorted(uncovered_aspects, key=lambda a: a.importance, reverse=True)

# Core aspects (importance >= 0.8) are always attempted first
# Optional aspects (importance < 0.8) are deferred or skipped if budget is low
```

### 3. Iterative Loop

The research agent uses a feedback loop:

```
while current_hop < max_hops:
    1. Get uncovered aspects
    2. If all core aspects covered → STOP
    3. Generate subquery targeting top uncovered aspect
    4. Retrieve documents
    5. Update coverage
    6. Repeat
```

### 4. Adaptive Hop Allocation

```python
# Coverage low after N hops → bias toward uncovered aspects
if coverage_percentage < 0.5 and current_hop > min_hops:
    # Target only core uncovered aspects
    uncovered_core = [a for a in uncovered if a.importance >= 0.8]
    
# High coverage → can try exploratory queries
elif coverage_percentage >= 0.7:
    # All core covered, can stop or explore optional aspects
```

## Implementation Details

### New Methods in QueryPlanner

#### `generate_subqueries_for_aspects()`
```python
def generate_subqueries_for_aspects(
    self, 
    main_question: str,
    uncovered_aspects: List[QueryAspect],
    llm_client=None,
    max_subqueries: int = 3
) -> List[Tuple[str, str]]:
    """
    Generate targeted subqueries for uncovered aspects.
    
    Returns:
        List of (subquery, aspect_name) tuples showing the mapping
    """
```

**Features:**
- Prioritizes core aspects (importance >= 0.8)
- Limits to `max_subqueries` to control hop budget
- Returns explicit aspect-to-subquery mappings for transparency
- Falls back gracefully if LLM fails

#### `_generate_aspect_subqueries_llm()`
```python
def _generate_aspect_subqueries_llm(
    self,
    main_question: str,
    aspects: List[QueryAspect],
    llm_client
) -> List[Tuple[str, str]]:
    """
    Use LLM to generate natural subqueries for aspects.
    
    Prompt includes:
    - Main question for context
    - List of uncovered aspects with type and importance
    - Request for focused, natural-language subqueries
    """
```

#### `_aspect_to_subquery_template()`
```python
def _aspect_to_subquery_template(
    self,
    aspect: QueryAspect,
    main_question: str
) -> str:
    """
    Convert aspect to subquery using templates.
    
    Templates by aspect type:
    - definition: "What is X?"
    - comparison: "What are the differences in X?"
    - process: "How does X work?"
    - causal: "Why is X important?"
    - evaluation: "What are the pros/cons of X?"
    - application: "What are the applications of X?"
    """
```

### Updated ResearchAgent Flow

The `_process_iterative()` method now uses aspect-guided generation:

```python
def _process_iterative(self, question: str, per_sub_k: int, start_time: float):
    # Extract aspects upfront
    aspect_coverage = self.query_planner.extract_aspects(question, self.llm_client)
    
    # Iterative loop
    while current_hop < max_hops:
        # Get uncovered aspects
        uncovered = aspect_coverage.get_uncovered_aspects(threshold=0.5)
        
        if not uncovered:
            print("All aspects covered, stopping")
            break
        
        # Generate subquery targeting top uncovered aspect
        subquery_mappings = self.query_planner.generate_subqueries_for_aspects(
            question, uncovered, self.llm_client, max_subqueries=1
        )
        
        subquery, target_aspect = subquery_mappings[0]
        print(f"🎯 Targeting Aspect: {target_aspect}")
        
        # Retrieve and update coverage
        documents = self.retriever.retrieve(subquery, top_k=per_sub_k)
        self.query_planner.update_aspect_coverage(aspect_coverage, documents, current_hop)
        
        # Check stopping condition
        should_continue, reason = self.query_planner.should_continue_retrieval(
            documents, current_hop, aspect_coverage=aspect_coverage
        )
        
        if not should_continue:
            break
```

## Logging & Debugging

### Aspect-to-Subquery Mapping

```
[Hop 1/10] Targeting 3 uncovered aspects
  🎯 Targeting Aspect: Definition of Attention Heads
  Subquery: What is an attention head in transformer models?
  Found 3 relevant documents
  📊 Coverage: 33.3% (2 aspects uncovered)
  Uncovered: ['Query/Key/Value Vectors', 'Multi-Head Attention Architecture']

[Hop 2/10] Targeting 2 uncovered aspects
  🎯 Targeting Aspect: Query/Key/Value Vectors
  Subquery: What roles do query, key, and value vectors play in attention?
  Found 2 relevant documents
  📊 Coverage: 66.7% (1 aspect uncovered)
  Uncovered: ['Multi-Head Attention Architecture']

[Hop 3/10] Targeting 1 uncovered aspect
  🎯 Targeting Aspect: Multi-Head Attention Architecture
  Subquery: How is multi-head attention architecture structured?
  Found 2 relevant documents
  📊 Coverage: 100.0% (0 aspects uncovered)
  Decision: Stop - All core aspects covered (weighted coverage: 95.0%)

✓ Stopping early after 3 hops: All core aspects covered
```

### Coverage Feedback Loop

At each hop, the system logs:
- Which aspects are still uncovered
- Which aspect is being targeted
- Coverage percentage after retrieval
- Stopping decision and reasoning

## Examples

### Example 1: Comparison Query

```python
Query: "Compare self-attention vs multi-head attention"

Identified Aspects:
1. [CORE] Definition of self-attention (importance: 1.0)
2. [CORE] Definition of multi-head attention (importance: 1.0)
3. [CORE] Comparison between mechanisms (importance: 1.0)

Hop 1: Targets "Definition of self-attention"
  → Subquery: "What is self-attention in transformers?"
  → Coverage: 33% (2 uncovered)

Hop 2: Targets "Definition of multi-head attention"
  → Subquery: "What is multi-head attention?"
  → Coverage: 67% (1 uncovered)

Hop 3: Targets "Comparison between mechanisms"
  → Subquery: "How does self-attention differ from multi-head attention?"
  → Coverage: 100% (0 uncovered)
  → STOP: All core aspects covered
```

### Example 2: Complex Technical Query

```python
Query: "How do query, key, and value vectors work in attention heads?"

Identified Aspects:
1. [CORE] Query vectors role (importance: 1.0)
2. [CORE] Key vectors role (importance: 1.0)
3. [CORE] Value vectors role (importance: 1.0)
4. [CORE] Attention head mechanism (importance: 1.0)
5. [optional] Historical context (importance: 0.6)

System targets aspects 1-4 first (core), deferring aspect 5 (optional)

Result: Comprehensive coverage of all core concepts before budget exhausted
```

### Example 3: Simple Query

```python
Query: "What is Python?"

Identified Aspects:
1. [CORE] Definition of Python (importance: 1.0)

Hop 1: Targets "Definition of Python"
  → Subquery: "What is Python programming language?"
  → Coverage: 100%
  → STOP: All aspects covered after just 1 hop

Efficient: No wasted hops on tangential queries
```

## Configuration

### Enable/Disable

```python
# Enable aspect-guided generation (default)
agent = ResearchAgent(
    retriever=retriever,
    llm_client=llm_client,
    adaptive_mode=True  # Uses aspect-guided approach
)

# Disable (use batch mode)
agent = ResearchAgent(
    retriever=retriever,
    llm_client=llm_client,
    adaptive_mode=False  # Uses fixed upfront generation
)
```

### Tune Parameters

```python
# Control subqueries per hop
subquery_mappings = planner.generate_subqueries_for_aspects(
    question,
    uncovered,
    llm_client,
    max_subqueries=1  # Generate 1 subquery per hop (default)
)

# Control coverage threshold
uncovered = aspect_coverage.get_uncovered_aspects(
    threshold=0.5  # Aspect considered covered if score >= 0.5
)

# Control importance threshold for "core" aspects
core_aspects = [a for a in aspects if a.importance >= 0.8]
```

## Benefits

### 1. **Targeted Coverage**
- Each hop explicitly addresses a specific uncovered aspect
- No more wasted hops on redundant queries

### 2. **Efficiency**
- Stops as soon as all core aspects are covered
- Can cover complex queries in fewer hops

### 3. **Transparency**
- Clear mapping between aspects and subqueries
- Easy to debug why certain subqueries were generated

### 4. **Prioritization**
- Core aspects always attempted first
- Optional aspects deferred if budget is limited

### 5. **Adaptability**
- Uses LLM for natural subquery generation
- Falls back to templates if LLM unavailable

## Testing

Comprehensive test suite in `tests/test_aspect_guided_subqueries.py`:

```bash
pytest tests/test_aspect_guided_subqueries.py -v
```

**Test Coverage:**
- ✅ Template-based aspect-to-subquery conversion (5 tests)
- ✅ Subquery generation for aspects (4 tests)
- ✅ Prioritization logic (2 tests)
- ✅ Integration scenarios (2 tests)
- ✅ Edge cases (3 tests)

**All 15 tests passing** ✅

## Comparison: Before vs After

| Feature | Before (Fixed) | After (Aspect-Guided) |
|---------|---------------|----------------------|
| **Subquery Generation** | All upfront, fixed count | Dynamic, per-hop based on coverage |
| **Targeting** | Generic, based on diversity | Explicit, targets uncovered aspects |
| **Stopping** | Document quality or hop limit | Aspect coverage or hop limit |
| **Efficiency** | Often wastes hops | Stops when aspects covered |
| **Transparency** | Unclear why subqueries chosen | Clear aspect-to-subquery mapping |
| **Coverage** | May miss aspects | Ensures all core aspects addressed |

## Metadata

Results now include aspect-guided metadata:

```python
result = agent.process(question)

metadata = result.metadata
print(f"Mode: {metadata['mode']}")  # 'iterative_aspect_guided'
print(f"Actual hops: {metadata['actual_hops']}")
print(f"Coverage: {metadata['aspect_coverage']['weighted_coverage']:.1%}")

# Per-aspect details
for aspect_info in metadata['aspect_coverage']['aspects']:
    print(f"{aspect_info['aspect']}: {aspect_info['coverage_score']:.1%}")
    print(f"  Covered at hop: {aspect_info['covered_at_hop']}")
```

## Future Enhancements

### Implemented ✅
- [x] Aspect extraction (LLM + heuristic)
- [x] Coverage tracking
- [x] Aspect-to-subquery mapping (LLM + templates)
- [x] Prioritization by importance
- [x] Iterative generation with feedback
- [x] Comprehensive logging
- [x] Testing

### Potential Improvements 🔄
- [ ] Semantic similarity for aspect-document matching (instead of keywords)
- [ ] Multi-aspect subqueries (one subquery targets multiple aspects)
- [ ] Learning from past queries to improve aspect extraction
- [ ] Dynamic importance adjustment based on query context
- [ ] Parallel subquery execution for uncovered aspects

## Related Files

- `agents/research/query_planner.py` - Core implementation (lines 676-827)
- `agents/research/research_agent.py` - Integration (lines 207-309)
- `tests/test_aspect_guided_subqueries.py` - Test suite
- `ASPECT_COVERAGE_FEATURE.md` - Coverage tracking docs

## Quick Start

```python
from agents.research.research_agent import ResearchAgent
from ollama_client import OllamaClient

# Initialize (aspect-guided is enabled by default)
agent = ResearchAgent(
    retriever=retriever,
    llm_client=OllamaClient(),
    adaptive_mode=True
)

# Process a complex query
result = agent.process("Compare transformer attention mechanisms")

# System will:
# 1. Extract aspects (e.g., self-attention, multi-head, comparison)
# 2. Generate subqueries targeting each uncovered aspect
# 3. Stop when all core aspects are covered
# 4. Return comprehensive answer with aspect coverage metadata
```

## Support

For issues or questions:
- Check logs for aspect-to-subquery mappings
- Review coverage percentages at each hop
- Run tests: `pytest tests/test_aspect_guided_subqueries.py -v`
- Check aspect extraction: `planner.extract_aspects(question)`

