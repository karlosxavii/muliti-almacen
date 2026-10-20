from datetime import datetime

from app.core.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    def save(self, commit: bool = True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit: bool = True):
        db.session.delete(self)
        if commit:
            db.session.commit()

    def to_dict(self, exclude=None):
        exclude = set(exclude or [])
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
