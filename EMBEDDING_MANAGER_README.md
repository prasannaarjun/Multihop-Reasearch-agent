# Embedding Manager Script

This script provides a comprehensive interface for viewing and managing user embeddings in the multi-hop research agent system.

## Features

- **List Users**: View all users with their embedding counts and statistics
- **View Embeddings**: Display detailed embedding information for specific users
- **Statistics**: View overall embedding statistics across all users
- **Clear Embeddings**: Remove embeddings for specific users or all users
- **Interactive Menu**: Easy-to-use command-line interface

## Prerequisites

1. Ensure your virtual environment is activated:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. Make sure your database is running and accessible
3. Ensure all required dependencies are installed (see `requirements.txt`)

## Usage

### Running the Script

```powershell
python embedding_manager.py
```

### Menu Options

1. **List all users with embedding counts**
   - Shows all users in the system
   - Displays embedding count, unique messages, and last login
   - Sorted by embedding count (highest first)

2. **View embeddings for a specific user**
   - Enter a user ID to view their embeddings
   - Shows embedding details including message content preview
   - Displays conversation information
   - Configurable limit for number of embeddings to show

3. **View overall statistics**
   - Total embeddings in the system
   - Number of unique users with embeddings
   - Average embeddings per user
   - Embedding dimension information

4. **Clear embeddings for a specific user**
   - Enter a user ID to clear their embeddings
   - Requires confirmation before deletion
   - Shows count of deleted embeddings

5. **Clear all embeddings**
   - Removes all embeddings from the database
   - Requires explicit confirmation
   - Shows count of deleted embeddings

6. **Exit**
   - Safely exits the program

## Example Output

### User List
```
================================================================================
ID    Username             Email                          Full Name           Embeddings Messages   Last Login          
================================================================================
1     john_doe             john@example.com              John Doe            15         8          2024-01-15 14:30:45
2     jane_smith           jane@example.com              Jane Smith          0          0          N/A                 
================================================================================
```

### Embedding Details
```
Embeddings for user: john_doe (ID: 1)
======================================================================================
Embedding ID    Message ID      Role       Content Preview                                    Created             Conversation                   
======================================================================================
emb_123         msg_456         user       What is the capital of France?                   2024-01-15 14:30:45  Geography Discussion           
emb_124         msg_457         assistant  The capital of France is Paris. It is located... 2024-01-15 14:31:02  Geography Discussion           
======================================================================================
```

### Statistics
```
============================================================
EMBEDDING STATISTICS
============================================================
Total Embeddings: 150
Unique Messages: 75
Embedding Dimension: 384
Total Users With Embeddings: 5
Avg Embeddings Per User: 30.00
Max Embeddings Per User: 50
============================================================
```

## Safety Features

- **Confirmation Prompts**: All deletion operations require explicit confirmation
- **Error Handling**: Graceful error handling with informative messages
- **Transaction Safety**: Database operations are wrapped in transactions
- **Rollback on Error**: Failed operations are automatically rolled back

## Database Schema

The script works with the following database tables:
- `users`: User information
- `embeddings`: Embedding vectors with metadata
- `chat_messages`: Chat messages linked to embeddings
- `conversations`: Conversation information

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check your `DATABASE_URL` in the `.env` file
   - Ensure PostgreSQL is running
   - Verify database credentials

2. **Permission Denied**
   - Ensure the database user has appropriate permissions
   - Check if the user can read/write to the required tables

3. **No Users Found**
   - Verify that users exist in the database
   - Check if the `users` table is properly populated

### Environment Variables

Make sure these are set in your `.env` file:
```
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
EMBEDDING_DIM=384
```

## Testing

Run the test suite to verify functionality:

```powershell
python -m pytest tests/test_embedding_manager.py -v
```

## Security Notes

- This script has full access to the embedding database
- Use with caution in production environments
- Consider restricting access to authorized personnel only
- Always backup your database before performing bulk operations

## Support

For issues or questions:
1. Check the error messages for specific guidance
2. Verify your database connection and permissions
3. Review the test cases for expected behavior
4. Check the logs for detailed error information

