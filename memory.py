# memory.py

class ChatMemory:
    """
    Simple chat memory class for short-term conversation storage.
    """

    def __init__(self):
        """
        Initialize an empty chat history.
        Each message is a dict: {"role": "user" or "assistant", "content": message}
        """
        self.history = []

    def add_user_message(self, message: str):
        """
        Add a message from the user to memory.
        """
        self.history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str):
        """
        Add a message from the assistant to memory.
        """
        self.history.append({"role": "assistant", "content": message})

    def get_full_history(self):
        """
        Retrieve the full chat history.
        """
        return self.history

    def clear(self):
        """
        Clear all chat memory.
        """
        self.history = []