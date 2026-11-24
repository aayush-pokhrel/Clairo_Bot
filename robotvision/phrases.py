"""What the robot says. Edit freely: each entry is a list and one is picked at random
(never the same one twice in a row), so the robot doesn't sound like a recording.

{name} is replaced with config.ROBOT_NAME.
"""

PHRASES = {
    # --- presence ---
    "first_greeting": [
        "Ohh, hello! How are you? I'm {name}.",
        "Oh, hey there! How are you doing? I'm {name}, nice to meet you.",
    ],
    "greeting": [
        "Ohh, hello! How are you?",
        "Oh hey, welcome back! How are you doing?",
        "Hello again! How's it going?",
        "Oh, hi there! How are you today?",
    ],
    "goodbye": [
        "Bye for now! Come back soon.",
        "See you later!",
        "Aww, leaving already? Take care!",
    ],
    # --- answers to "how are you?" (thumbs shortly after the greeting) ---
    "doing_well": [
        "Yay, glad you're doing well!",
        "That's great to hear!",
        "Awesome, me too!",
    ],
    "doing_badly": [
        "Aww, I'm sorry to hear that. I hope your day gets better.",
        "Oh no. Well, I'm here if you need anything.",
    ],
    # --- gestures ---
    "Open_Palm": [
        "Hii! What can I help you with today?",
        "Hi there! What can I do for you?",
        "Hey! How can I help?",
    ],
    "Wave": [
        "Hey! Waving right back at you!",
        "Hi hi! Nice wave!",
        "Hello! Good to see you!",
    ],
    "Victory": [
        "Yay, I'm so happy that helped!",
        "Great, glad that made sense!",
        "Awesome! Happy I could help.",
    ],
    "Victory_no_context": [
        "Peace! Hope you're having a good day.",
        "Peace to you too!",
    ],
    "Thumb_Up": [
        "Awesome!",
        "Great, love that!",
        "Nice! Glad to hear it.",
    ],
    "Thumb_Down": [
        "Oh no, sorry about that. Want to try again?",
        "Hmm, not great huh? Let's try another way.",
    ],
    "Two_Thumbs_Up": [
        "Two thumbs up? You're making me blush!",
        "Wow, double thumbs! Thank you!",
    ],
    "OK_Sign": [
        "Perfect, sounds good!",
        "Okay, got it!",
    ],
    "Pointing_Up": [
        "Ooh, you have a question? I'm all ears.",
        "Yes? Go ahead, I'm listening.",
    ],
    "ILoveYou": [
        "Aww, love you too!",
        "Aww, that's so sweet. Right back at you!",
    ],
    "Closed_Fist": [
        "Okay, I'll stay quiet for a bit. Show me an open palm when you need me.",
        "Got it, going quiet. Just wave or show your palm when you want me back.",
    ],
    "wake_up": [
        "I'm back! What can I help you with?",
        "Hi again! What do you need?",
    ],
}
