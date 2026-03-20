from ddd import ValueObject

"""
In the future, subtitle would have properties like language, rate, etc.
"""
class Subtitle(ValueObject):
    def __init__(self, url: str, name: str) -> None:
        # TODO: Validate url
        self.url = url
        self.name = name