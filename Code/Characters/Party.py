class Party:
    def __init__(self):
        self.members = []
        self.selected_index = 0

    def add(self, character):
        self.members.append(character)

    def remove(self, index):
        if 0 <= index < len(self.members):
            return self.members.pop(index)
        return None
    def get_current_character(self):
        return self.party.get_character(self.selected_character)
    def current(self):
        if self.members:
            return self.members[self.selected_index]
        return None

    def next(self):
        if self.members:
            self.selected_index = (self.selected_index + 1) % len(self.members)

    def prev(self):
        if self.members:
            self.selected_index = (self.selected_index - 1) % len(self.members)

    def get(self, index):
        if 0 <= index < len(self.members):
            return self.members[index]
        return None

    def __len__(self):
        return len(self.members)