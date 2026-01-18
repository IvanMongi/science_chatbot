"""
Test persistence layer functionality.
"""
import sys
import os
import tempfile
import sqlite3
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from persistence import (
    get_checkpointer,
    create_thread,
    list_threads,
    get_thread,
    update_thread_metadata,
    delete_thread,
    _get_db_connection,
    DATABASE_PATH
)


def test_checkpointer():
    """Test that checkpointer is initialized correctly."""
    checkpointer = get_checkpointer()
    assert checkpointer is not None
    print("✓ Checkpointer initialized successfully")
    
    # Verify it's a singleton
    checkpointer2 = get_checkpointer()
    assert checkpointer is checkpointer2
    print("✓ Checkpointer is singleton")


def test_database_initialization():
    """Test that database is initialized with correct schema."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Check that table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='conversation_threads'
    """)
    result = cursor.fetchone()
    assert result is not None
    print("✓ Database table 'conversation_threads' created")
    
    # Check table schema
    cursor.execute("PRAGMA table_info(conversation_threads)")
    columns = {row[1] for row in cursor.fetchall()}
    expected_columns = {'thread_id', 'title', 'preview', 'message_count', 'created_at', 'updated_at'}
    assert columns == expected_columns
    print("✓ Database schema is correct")
    
    conn.close()


def test_crud_operations():
    """Test Create, Read, Update, Delete operations."""
    test_thread_id = "test-thread-123"
    test_title = "Test Conversation"
    test_preview = "What is machine learning?"
    
    # Test CREATE
    create_thread(test_thread_id, test_title, test_preview)
    print("✓ Thread created successfully")
    
    # Test READ single
    thread = get_thread(test_thread_id)
    assert thread is not None
    assert thread['thread_id'] == test_thread_id
    assert thread['title'] == test_title
    assert thread['preview'] == test_preview
    assert thread['message_count'] == 0
    print("✓ Single thread retrieved successfully")
    
    # Test UPDATE
    update_thread_metadata(test_thread_id, 5, "Updated preview...")
    updated_thread = get_thread(test_thread_id)
    assert updated_thread['message_count'] == 5
    assert updated_thread['preview'] == "Updated preview..."
    print("✓ Thread metadata updated successfully")
    
    # Test READ list
    threads = list_threads(limit=10)
    assert len(threads) > 0
    thread_ids = [t['thread_id'] for t in threads]
    assert test_thread_id in thread_ids
    print("✓ Threads list retrieved successfully")
    
    # Test DELETE
    delete_thread(test_thread_id)
    deleted_thread = get_thread(test_thread_id)
    assert deleted_thread is None
    print("✓ Thread deleted successfully")


def test_pagination():
    """Test list_threads pagination."""
    # Create multiple threads
    for i in range(5):
        thread_id = f"thread-page-test-{i}"
        create_thread(thread_id, f"Thread {i}", f"Preview {i}")
    
    # Test pagination
    page1 = list_threads(limit=2, offset=0)
    page2 = list_threads(limit=2, offset=2)
    
    assert len(page1) == 2
    assert len(page2) <= 2
    
    # Verify different pages
    page1_ids = {t['thread_id'] for t in page1}
    page2_ids = {t['thread_id'] for t in page2}
    assert len(page1_ids & page2_ids) == 0  # No overlap
    
    print("✓ Pagination works correctly")
    
    # Cleanup
    for i in range(5):
        delete_thread(f"thread-page-test-{i}")


def test_ordering():
    """Test that threads are ordered by updated_at descending."""
    import time
    
    # Create threads with time delay
    for i in range(3):
        create_thread(f"order-test-{i}", f"Thread {i}", f"Preview {i}")
        time.sleep(0.1)
    
    threads = list_threads(limit=10)
    
    # Filter to only our test threads
    test_threads = [t for t in threads if t['thread_id'].startswith('order-test-')]
    
    # Verify ordering (newest first)
    for i in range(len(test_threads) - 1):
        current_time = datetime.fromisoformat(test_threads[i]['updated_at'])
        next_time = datetime.fromisoformat(test_threads[i + 1]['updated_at'])
        assert current_time >= next_time
    
    print("✓ Threads ordered correctly (newest first)")
    
    # Cleanup
    for i in range(3):
        delete_thread(f"order-test-{i}")


def run_all_tests():
    """Run all tests."""
    print("Running persistence layer tests...\n")
    
    try:
        test_checkpointer()
        test_database_initialization()
        test_crud_operations()
        test_pagination()
        test_ordering()
        
        print("\n✅ All tests passed!")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
