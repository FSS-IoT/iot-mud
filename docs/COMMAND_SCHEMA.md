# Command Schema (Internal)

Commands sent by clients are expected to follow this structure:

{
  "v": 1,             # Version
  "type": "input",    # Message type
  "id": "unique_id",  # Client-side request ID
  "data": {
    "text": "the actual command string"
  }
}
