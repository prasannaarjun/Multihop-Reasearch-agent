# Aspect-Based Coverage Tracking Feature

## Overview

This feature enhances the multihop subquery generation loop with a **coverage-check layer** that ensures all aspects of a user's query are addressed before stopping. This solves the problem where the agent would stop early upon finding high-quality documents, even when the question had multiple facets (e.g., comparisons like "self-attention vs. multi-attention").

## Problem Solved

**Before**: The system would stop early if it found high-quality documents, potentially missing important aspects of multi-faceted questions.

**After**: The system tracks coverage of each aspect and only stops when:
- All core aspects are covered above a confidence threshold, OR
- Maximum hop limit is reached

## Key Components

### 1. Aspect Extraction

The system automatically identifies distinct facets/aspects of a query:

#### Aspect Types
- **Definition**: "What is X?"
- **Comparison**: "X vs Y", "Compare X and Y"
- **Process**: "How does X work?"
- **Causal**: "Why is X important?"
- **Evaluation**: "Advantages/disadvantages of X"
- **Application**: "Uses/examples of X"

#### Extraction Methods
1. **LLM-based** (preferred): Uses the LLM to intelligently identify aspects
2. **Heuristic-based** (fallback): Uses regex patterns and keyword detection

#### Example
```python
Query: "self-attention vs multi-head attention"

Identified Aspects:
1. [CORE] Definition/explanation of self-attention (definition)
2. [CORE] Definition/explanation of multi-head attention (definition)
3. [CORE] Comparison between self-attention and multi-head attention (comparison)
```

### 2. Coverage Tracking

Each aspect is tracked with:
- **Coverage Score** (0.0 to 1.0): How well documents cover this aspect
- **Importance** (0.0 to 1.0): Core (≥0.8) vs optional (<0.8)
- **Keywords**: Terms used to match documents to aspects
- **Covered at Hop**: Which hop first covered this aspect

#### Coverage Calculation
Documents are scored against each aspect based on:
- Keyword matches in document content/title
- Document relevance score
- Best matching document determines aspect coverage

### 3. Intelligent Stopping Conditions

The system uses a multi-tier stopping logic:

```
1. If at max_hops → STOP (safety limit)
2. If below min_hops → CONTINUE (quality assurance)
3. If aspect coverage enabled:
   - If all core aspects covered (≥70% weighted coverage) → STOP
   - If core aspects uncovered → CONTINUE
   - If coverage below 70% → CONTINUE
4. Fallback to traditional document-quality stopping
```

### 4. Comprehensive Logging

At each hop, the system logs:
```
📋 Identified Aspects (3):
  1. [CORE] Definition of self-attention (definition)
  2. [CORE] Definition of multi-attention (definition)
  3. [CORE] Comparison between mechanisms (comparison)

[Hop 1] Subquery: What is self-attention?
  Found 3 relevant documents (total: 3)
  📊 Coverage: 33.3% (2 aspects uncovered)
  Uncovered: ['Definition of multi-attention', 'Comparison between mechanisms']
  Decision: Continue - Core aspects still uncovered

[Hop 2] Subquery: What is multi-head attention?
  Found 3 relevant documents (total: 6)
  📊 Coverage: 66.7% (1 aspect uncovered)
  Uncovered: ['Comparison between mechanisms']
  Decision: Continue - Core aspects still uncovered

[Hop 3] Subquery: Difference between self-attention and multi-head attention
  Found 2 relevant documents (total: 8)
  📊 Coverage: 100.0% (0 aspects uncovered)
  Decision: Stop - All core aspects covered (weighted coverage: 95.0%)
```

## Usage

### Basic Usage

```python
from agents.research.research_agent import ResearchAgent
from agents.research.document_retriever import DocumentRetriever
from ollama_client import OllamaClient

# Initialize with aspect coverage enabled (default)
agent = ResearchAgent(
    retriever=retriever,
    llm_client=OllamaClient(),
    adaptive_mode=True,  # Enables aspect coverage
    min_hops=3,
    max_hops=10
)

# Process a query
result = agent.process("self-attention vs multi-head attention")

# Access coverage metadata
coverage_info = result.metadata['aspect_coverage']
print(f"Total aspects: {coverage_info['total_aspects']}")
print(f"Coverage: {coverage_info['weighted_coverage']:.1%}")

for aspect in coverage_info['aspects']:
    print(f"{aspect['aspect']}: {aspect['coverage_score']:.1%}")
```

### Disabling Aspect Coverage

```python
# Disable aspect coverage (use traditional stopping)
planner = QueryPlanner(enable_aspect_coverage=False)

agent = ResearchAgent(
    retriever=retriever,
    llm_client=llm_client,
    adaptive_mode=False  # Use batch mode without coverage
)
```

### Customizing Coverage Thresholds

```python
# In should_continue_retrieval call (internal)
should_continue, reason = planner.should_continue_retrieval(
    retrieved_docs=docs,
    current_hop=hop,
    aspect_coverage=coverage,
    coverage_threshold=0.5,  # Threshold for "covered" (default: 0.5)
    min_confidence_threshold=0.5  # Document quality threshold
)
```

## Data Structures

### QueryAspect
```python
@dataclass
class QueryAspect:
    aspect: str              # "Definition of self-attention"
    aspect_type: str         # "definition"
    importance: float        # 0.0 to 1.0 (core vs optional)
    keywords: List[str]      # ["self-attention", "definition"]
```

### AspectCoverage
```python
@dataclass
class AspectCoverage:
    aspects: List[QueryAspect]
    coverage_scores: Dict[str, float]      # aspect -> coverage score
    covered_by_hop: Dict[str, int]         # aspect -> hop number
    
    # Methods
    def is_aspect_covered(aspect, threshold=0.5) -> bool
    def get_uncovered_aspects(threshold=0.5) -> List[QueryAspect]
    def get_coverage_percentage() -> float
    def get_weighted_coverage() -> float  # Weighted by importance
```

## Configuration Options

### QueryPlanner Initialization
```python
planner = QueryPlanner(
    min_hops=3,                      # Minimum hops (quality assurance)
    max_hops=10,                     # Maximum hops (safety limit)
    enable_aspect_coverage=True      # Enable coverage tracking
)
```

### ResearchAgent Initialization
```python
agent = ResearchAgent(
    retriever=retriever,
    llm_client=llm_client,
    use_llm=True,                    # Required for aspect extraction
    adaptive_mode=True,              # Enable adaptive/iterative mode
    min_hops=3,
    max_hops=10
)
```

## Metadata in ResearchResult

```python
result = agent.process(question)

# Access aspect coverage metadata
if result.metadata['aspect_coverage']['enabled']:
    coverage = result.metadata['aspect_coverage']
    
    print(f"Total aspects: {coverage['total_aspects']}")
    print(f"Coverage percentage: {coverage['coverage_percentage']:.1%}")
    print(f"Weighted coverage: {coverage['weighted_coverage']:.1%}")
    print(f"Uncovered count: {coverage['uncovered_count']}")
    
    # Details for each aspect
    for aspect_info in coverage['aspects']:
        print(f"{aspect_info['aspect']}")
        print(f"  Type: {aspect_info['type']}")
        print(f"  Importance: {aspect_info['importance']}")
        print(f"  Coverage: {aspect_info['coverage_score']:.1%}")
        print(f"  Covered at hop: {aspect_info['covered_at_hop']}")
```

## Examples

### Example 1: Comparison Query
```python
Query: "Compare transformers and RNNs for NLP"

Aspects Identified:
1. [CORE] Definition of transformers (definition)
2. [CORE] Definition of RNNs (definition)
3. [CORE] Comparison for NLP (comparison)

Result: System continues until all 3 aspects are covered
```

### Example 2: Multi-Part Query
```python
Query: "What are neural networks and how do they work?"

Aspects Identified:
1. [CORE] Definition of neural networks (definition)
2. [CORE] Process/mechanism of neural networks (process)

Result: System ensures both definition AND process are covered
```

### Example 3: Simple Query
```python
Query: "What is Python?"

Aspects Identified:
1. [CORE] Definition of Python (definition)

Result: Simpler stopping - single aspect, may stop early
```

## Backward Compatibility

✅ **Fully backward compatible**

- Aspect coverage is enabled by default but degrades gracefully
- Traditional document-quality stopping still works as fallback
- Can be explicitly disabled: `enable_aspect_coverage=False`
- Existing code continues to work without changes

## Testing

Comprehensive test suite in `tests/test_aspect_coverage.py`:

```bash
pytest tests/test_aspect_coverage.py -v
```

Tests cover:
- ✅ Aspect extraction (comparison, definition, process, etc.)
- ✅ Coverage initialization and tracking
- ✅ Coverage score calculation
- ✅ Weighted coverage (importance-based)
- ✅ Stopping conditions (all scenarios)
- ✅ Integration scenarios (end-to-end)

## Benefits

### 1. **Completeness**
Ensures all aspects of multi-faceted questions are addressed

### 2. **Efficiency**
Stops as soon as all aspects are covered (not just on document count)

### 3. **Quality**
min_hops enforcement prevents premature stopping

### 4. **Transparency**
Detailed logging shows what aspects are covered and when

### 5. **Flexibility**
Works with LLM or heuristics, can be disabled if needed

## Limitations & Future Improvements

### Current Limitations
- Keyword-based document matching (simple but effective)
- Heuristic aspect extraction has limited patterns
- Fixed coverage threshold (70%)

### Potential Improvements
1. **Semantic matching**: Use embeddings to match documents to aspects
2. **Confidence-based weighting**: Different thresholds for core vs optional
3. **Dynamic threshold**: Adjust coverage threshold based on query complexity
4. **Aspect prioritization**: Explicitly target uncovered aspects in next subquery
5. **LLM-based coverage scoring**: Use LLM to assess if document covers aspect

## Related Files

- `agents/research/query_planner.py` - Core implementation
- `agents/research/research_agent.py` - Integration with agent
- `tests/test_aspect_coverage.py` - Test suite
- `examples/aspect_coverage_demo.py` - Demonstration script

## Quick Start

1. **Default usage** (aspect coverage enabled):
   ```python
   agent = ResearchAgent(retriever, llm_client)
   result = agent.process("your question")
   ```

2. **Check coverage**:
   ```python
   coverage = result.metadata['aspect_coverage']
   print(f"Coverage: {coverage['weighted_coverage']:.1%}")
   ```

3. **Disable if needed**:
   ```python
   planner = QueryPlanner(enable_aspect_coverage=False)
   ```

## Support

For issues or questions:
- Check test suite: `tests/test_aspect_coverage.py`
- Run demo: `python examples/aspect_coverage_demo.py`
- Review logs: Look for "Coverage status at hop X" messages

