"""
Test script to verify message persistence functionality.
Run this after starting the backend to test the persistence feature.
"""
import asyncio
import uuid
from persistence import (
    create_thread, 
    save_messages_to_db, 
    load_messages_from_db,
    get_messages_for_display,
    _init_db
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


async def test_message_persistence():
    """Test saving and loading messages."""
    print("🧪 Testing Message Persistence\n")
    
    # Ensure DB is initialized
    _init_db()
    print("✅ Database initialized")
    
    # Create a test thread
    thread_id = str(uuid.uuid4())
    thread = create_thread(thread_id, title="Test Thread", preview="Testing message persistence")
    print(f"✅ Created thread: {thread_id}")
    
    # Create test messages
    test_messages = [
        HumanMessage(content="What is quantum entanglement?"),
        AIMessage(content="Quantum entanglement is a phenomenon..."),
        HumanMessage(content="Can you give me an example?"),
        AIMessage(content="Sure! Consider two electrons...")
    ]
    
    # Save messages
    print(f"\n📝 Saving {len(test_messages)} messages...")
    save_messages_to_db(thread_id, test_messages)
    print("✅ Messages saved")
    
    # Load messages back
    print("\n📥 Loading messages from database...")
    loaded_messages = load_messages_from_db(thread_id)
    print(f"✅ Loaded {len(loaded_messages)} messages")
    
    # Verify content
    print("\n🔍 Verifying message content...")
    for idx, (original, loaded) in enumerate(zip(test_messages, loaded_messages)):
        assert original.content == loaded.content, f"Message {idx} content mismatch"
        assert type(original) == type(loaded), f"Message {idx} type mismatch"
    print("✅ All messages match!")
    
    # Test get_messages_for_display
    print("\n🎨 Testing display format...")
    display_messages = get_messages_for_display(thread_id)
    print(f"✅ Retrieved {len(display_messages)} messages for display")
    
    for msg in display_messages:
        print(f"  - [{msg['role']}] {msg['content'][:50]}...")
    
    # Test incremental save (simulating a continued conversation)
    print("\n➕ Testing incremental message save...")
    additional_messages = test_messages + [
        HumanMessage(content="Thanks for the explanation!"),
        AIMessage(content="You're welcome! Feel free to ask more questions.")
    ]
    
    save_messages_to_db(thread_id, additional_messages)
    reloaded_messages = load_messages_from_db(thread_id)
    print(f"✅ Now have {len(reloaded_messages)} total messages (should be 6)")
    
    assert len(reloaded_messages) == 6, "Should have 6 total messages"
    
    print("\n🎉 All tests passed! Message persistence is working correctly.")
    print(f"\n💡 Test thread ID: {thread_id}")
    print("   You can now test this in the frontend by sending messages to this thread.")


if __name__ == "__main__":
    asyncio.run(test_message_persistence())
