# Message Persistence Migration Guide

## Overview
This update adds persistent message storage to the database, allowing chat history to survive server restarts. Messages are now stored in a new `messages` table alongside the existing thread metadata.

## What Changed

### 1. Database Schema
Added a new `messages` table:
- `id`: Auto-incrementing primary key
- `thread_id`: Foreign key to conversation_threads
- `role`: Message role (user, assistant, system, tool)
- `content`: Message text content
- `tool_calls`: JSON serialized tool calls (for assistant messages)
- `tool_call_id`: ID for tool response messages
- `created_at`: Timestamp
- `message_index`: Order within thread (ensures proper sequence)

### 2. Backend Changes

#### `persistence.py`
- **New table**: `messages` table created in `_init_db()`
- **New function**: `save_messages_to_db()` - Saves messages to database with deduplication
- **New function**: `load_messages_from_db()` - Loads and reconstructs LangChain messages
- **New function**: `get_messages_for_display()` - Returns formatted messages for frontend

#### `main.py`
- **Updated**: `/api/chat` endpoint now loads existing messages before invoking agent
- **New**: `/api/threads/{thread_id}/messages` endpoint for fetching conversation history

#### `graph.py`
- Minor cleanup (removed duplicate return statement)

### 3. Frontend Changes

#### `script.js`
- **Updated**: `loadThread()` now fetches and displays previous messages when user clicks on a thread
- Messages are rendered chronologically when switching between conversations

## How It Works

### Message Flow
1. **User sends message**: Frontend sends to `/api/chat` with optional `thread_id`
2. **Backend loads history**: If `thread_id` exists, `load_messages_from_db()` retrieves past messages
3. **Agent processes**: LangGraph agent receives full conversation context
4. **Save to DB**: New messages are saved via `save_messages_to_db()`
5. **Frontend display**: When user clicks old thread, frontend fetches messages via `/api/threads/{thread_id}/messages`

### Deduplication Strategy
The `save_messages_to_db()` function:
- Counts existing messages in the thread
- Only saves messages beyond the current count
- Uses `message_index` to maintain order
- Prevents duplicate saves on repeated calls

## Migration Steps

### Automatic Migration
The database will automatically migrate when you restart the server:
1. The `_init_db()` function runs on module import
2. `CREATE TABLE IF NOT EXISTS` ensures safe migration
3. Existing threads are preserved
4. New messages table is created with indexes

### Manual Verification
```bash
# Check if migration was successful
cd backend
python -c "from persistence import _init_db; _init_db(); print('✅ Migration complete')"
```

## Testing

### Run Test Script
```bash
cd backend
python test_message_persistence.py
```

This will:
- Create a test thread
- Save sample messages
- Load and verify messages
- Test incremental saves
- Display formatted output

### Manual Testing
1. Start the backend: `uvicorn main:app --reload`
2. Open frontend in browser
3. Create a new chat and send messages
4. **Stop the server** (Ctrl+C)
5. **Restart the server**
6. Click on the thread in the sidebar
7. ✅ Previous messages should load and display

## API Endpoints

### GET `/api/threads/{thread_id}/messages`
Returns all user and assistant messages for a thread.

**Response:**
```json
{
  "thread_id": "uuid-here",
  "messages": [
    {
      "role": "user",
      "content": "What is quantum entanglement?",
      "created_at": "2026-01-19T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Quantum entanglement is...",
      "created_at": "2026-01-19T10:30:05Z"
    }
  ]
}
```

## Backward Compatibility

### Existing Data
- Existing threads continue to work normally
- Old threads will have empty message history (started fresh from this point)
- LangGraph's checkpointer still maintains in-memory state during active sessions

### No Breaking Changes
- All existing endpoints remain unchanged
- Frontend is backward compatible
- Database schema is additive only

## Performance Considerations

### Indexing
Two indexes are created for optimal performance:
- `idx_messages_thread_id`: Fast thread-based queries
- `idx_messages_created_at`: Chronological sorting

### Query Optimization
- `load_messages_from_db()`: Single query with ORDER BY
- `save_messages_to_db()`: Batch insert for new messages
- `get_messages_for_display()`: Filters out system/tool messages for frontend

## Troubleshooting

### Messages not persisting
- Check that database file exists: `backend/conversations.db`
- Verify table creation: `sqlite3 conversations.db ".schema messages"`
- Check logs for errors during save

### Old messages not loading
- Verify `/api/threads/{thread_id}/messages` returns data
- Check browser console for fetch errors
- Ensure thread_id is correctly passed to backend

### Duplicate messages
- Check that `save_messages_to_db()` deduplication logic is working
- Verify `message_index` uniqueness constraint

## Future Enhancements

Potential improvements:
- Add message editing/deletion
- Implement message search
- Add pagination for long conversations
- Export conversation to file
- Message reactions/favorites
- Conversation branching
