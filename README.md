# ChroniKeeper

**Blurb:** ChroniKeeper is a background memory engine for AI roleplay in SillyTavern, keeping track of characters, world events, and relationships automatically to maintain story continuity.

---

## Overview

ChroniKeeper is a modular RAG-based system that:
- Tracks character traits, transformations, and relationships over time.
- Maintains world summaries and event tracking.
- Produces concise summaries (~200–400 tokens) for LLM prompts.
- Runs in the background to minimize manual memory updates.

### Features
- Character memory with transformations, relationship scoring, and key events.
- World memory with automatic day/night and event tracking.
- Modular design for easy expansion and debugging.
- Integration with SillyTavern chat history for context-aware summaries.

## How to Use
1. Place the `chronikeeper` folder in your SillyTavern extensions directory.  
2. Run the system via CLI or Python:  
   ```bash
   python -m chronikeeper
