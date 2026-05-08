# preferences-engine
DICE-inspired AI-powered engine for inferring user preferences

![Example](example.png)

## Inspiration

This implementation tries to follow the original [DICE](https://github.com/embabel/dice/tree/90c00d93f8e347ebafa94cf8ba1c855b19eb22b1) design and is heavily inspired by its code and the accompanying article: [Agents That Extract and Use Preferences from Conversations](https://medium.com/embabel/agents-that-extract-and-use-preferences-from-conversations-7b22cca9abb3).

There is also an idea to extend the inference signal beyond chat messages to include implicit user behavior — such as applied filters and item clicks — as additional sources for preference extraction.

Another planned direction is a user-facing API that gives users visibility and control over their inferred preferences — allowing them to inspect what has been inferred and selectively disable individual preferences or turn off inference entirely.
