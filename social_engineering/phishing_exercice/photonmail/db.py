from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import datetime
import sqlite3

engine = None

class Mail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    addr_from: str
    addr_to: str
    subject: str
    contents: str
    date: datetime = Field(default_factory=datetime.utcnow)
    read: bool
    context: Optional[str] = Field(default=None)
    
def init(filename="mailbox.db"):
    global engine
    engine = create_engine(f"sqlite:///{filename}")
    SQLModel.metadata.create_all(engine)

def add(email, context=None):
    with Session(engine) as session:
        new_mail = Mail(addr_from=email['from'], addr_to=email['to'], subject=email['object'], contents=email['contents'], context=context, read=False)
        session.add(new_mail)
        session.commit()

def get_mailbox(_from=None, _to=None):
    if _from is None and _to is None:
        return None
    with Session(engine) as session:
        if _from:
            statement = select(Mail).where(Mail.addr_from == _from)
        elif _to:
            statement = select(Mail).where(Mail.addr_to == _to)
        results = session.exec(statement)
        mailbox = [ result.dict() for result in results ]
        mailbox.reverse()
        return mailbox

def read(id):
    with Session(engine) as session:
        statement = select(Mail).where(Mail.id == id)
        mail = session.exec(statement).one()
        mail.read = True
        session.add(mail)
        session.commit()
    return

def delete(id):
    with Session(engine) as session:
        statement = select(Mail).where(Mail.id == id)
        mail = session.exec(statement).one()
        session.delete(mail)
        session.commit()
    return
