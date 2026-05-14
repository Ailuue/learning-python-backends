from sqlmodel import Field, SQLModel


class BookmarkTagLink(SQLModel, table=True):
    bookmark_id: int | None = Field(
        default=None, foreign_key="bookmark.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: int | None = Field(
        default=None, foreign_key="tag.id", primary_key=True, ondelete="CASCADE"
    )
