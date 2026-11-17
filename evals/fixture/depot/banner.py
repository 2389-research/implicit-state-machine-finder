# ABOUTME: The promo banner shown at the top of the shop home page.
# ABOUTME: Kept per browser session; nothing is stored.


class Banner:
    def __init__(self):
        self.seen = False
        self.dismissed = False

    def render(self):
        if self.dismissed:
            return ""
        self.seen = True
        return "<div class='promo'>Free shipping this week</div>"

    def dismiss(self):
        self.dismissed = True
