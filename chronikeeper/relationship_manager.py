class RelationshipManager:
    def __init__(self):
        self.relationships = {}  # {char_id: {other_char_id: score}}

    def update_relationship(self, char_id, other_char_id, delta):
        if char_id not in self.relationships:
            self.relationships[char_id] = {}
        if other_char_id not in self.relationships[char_id]:
            self.relationships[char_id][other_char_id] = 0
        self.relationships[char_id][other_char_id] += delta

    def get_relationship(self, char_id, other_char_id):
        return self.relationships.get(char_id, {}).get(other_char_id, 0)
