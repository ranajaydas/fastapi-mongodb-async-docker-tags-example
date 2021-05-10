from pydantic import BaseModel, validator
from typing import List


class Article(BaseModel):
    content: str
    tags: List[str] = []

    @validator('tags', each_item=True)
    def check_invalid_tag(cls, tag):
        """Check each tag for invalid characters and convert to lowercase"""
        invalid_chars = ['?', '/']
        assert not any(char in tag for char in invalid_chars), f'Invalid character found in tag: {invalid_chars}'
        return tag.lower()

    @validator('tags')
    def remove_duplicates(cls, tags):
        if len(tags) > 1:
            return list({tag: 0 for tag in tags})
        return tags
