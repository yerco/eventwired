class Paginator:
    def __init__(self, total_items, page=1, per_page=10):
        self.page = max(page, 1)
        self.per_page = per_page
        self.total_items = total_items
        self.total_pages = (total_items + per_page - 1) // per_page

    def offset(self):
        return (self.page - 1) * self.per_page

    def limit(self):
        return self.per_page

    def to_dict(self):
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_prev": self.page > 1,
            "has_next": self.page < self.total_pages,
            "prev_page": self.page - 1 if self.page > 1 else None,
            "next_page": self.page + 1 if self.page < self.total_pages else None,
        }

    def has_next(self):
        return self.page < self.total_pages

    def has_prev(self):
        return self.page > 1