# Fix: PostgreSQL JSONB Query Error

## Issue

Error when loading statistics:
```
psycopg2.errors.UndefinedFunction: function json_extract_path_text(jsonb, unknown) does not exist
```

## Root Cause

The `embedding_metadata` column is of type **JSONB** (not JSON), but the code was using `json_extract_path_text()` which only works with JSON type columns.

## Solution

Replaced ORM queries using `func.json_extract_path_text()` with raw SQL queries using the JSONB `->>` operator.

### Before (Broken):
```python
file_types_result = self.db_session.query(
    func.json_extract_path_text(EmbeddingDB.embedding_metadata, 'file_type').label('file_type'),
    func.count().label('count')
).filter(...)
```

### After (Fixed):
```python
file_types_query = text("""
    SELECT 
        embedding_metadata->>'file_type' as file_type,
        COUNT(*) as count
    FROM embeddings 
    WHERE user_id = :user_id 
    AND embedding_metadata->>'file_type' IS NOT NULL
    GROUP BY embedding_metadata->>'file_type'
""")
file_types_result = self.db_session.execute(file_types_query, {"user_id": self.user_id})
```

## Key Changes

### File: `agents/research/document_retriever.py`

1. **Added import**: `text` from sqlalchemy
2. **Fixed file type query**: Lines 114-126
3. **Fixed filename query**: Lines 128-136

## JSONB vs JSON in PostgreSQL

| Operator | Purpose | Example |
|----------|---------|---------|
| `->` | Get JSON object/array (returns JSONB) | `data->'field'` |
| `->>` | Get JSON value as text | `data->>'field'` |
| `#>` | Get nested object by path (returns JSONB) | `data#>'{a,b}'` |
| `#>>` | Get nested value as text | `data#>>'{a,b}'` |

For JSONB columns:
- ✅ Use `->>` operator for text extraction
- ❌ Don't use `json_extract_path_text()` (for JSON only)

## Testing

The fix resolves:
- ✅ Loading collection statistics
- ✅ File type distribution queries
- ✅ Unique filename counts
- ✅ User document statistics

No linter errors detected.

## Related Files

This same pattern is correctly implemented in:
- `document_ingestion.py` (lines 384-403) ✅
- `embedding_manager.py` (uses raw SQL correctly) ✅

The fix brings `document_retriever.py` in line with the rest of the codebase.

