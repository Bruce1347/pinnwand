"""Collection of pinnwand's command line entry points that allow you to start
a HTTP server, add and remove paste, initialize the database and reap expired
pastes."""

import sys
import logging

from datetime import datetime, timedelta

import click

import tornado.ioloop

from pinnwand.database import Base, session_factory, Paste
from pinnwand.http import make_application
from pinnwand import utility


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@click.group()
def main() -> None:
    """Pinnwand pastebin software."""
    return None


@main.command()
@click.option("--port", default=8000, help="Port to listen to.")
def http(port: int) -> None:
    """Run pinnwand's HTTP server."""
    Base.metadata.create_all(session_factory.engine)

    application = make_application()
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()


@main.command()
@click.option("--lexer", default="text", help="Lexer to use.")
def add(lexer: str) -> None:
    """Add a paste to pinnwand's database from stdin."""
    if lexer not in utility.list_languages():
        log.error("add: unknown lexer")
        return

    paste = Paste(sys.stdin.read(), lexer=lexer, expiry=timedelta(days=1))

    session = session_factory.make_session()
    session.add(paste)
    session.commit()

    log.info("add: paste created: %s", paste.paste_id)


@main.command()
@click.option("--paste", help="Paste identifier.", required=True)
def delete(paste: str) -> None:
    """Delete a paste from pinnwand's database."""
    session = session_factory.make_session()
    paste_object = session.query(Paste).filter(Paste.paste_id == paste).first()

    if not paste_object:
        log.error("delete: unknown paste")
        return

    session.delete(paste_object)
    session.commit()

    log.info("delete: paste %s deleted", paste_object)


@main.command()
def reap() -> None:
    """Delete all pastes that are past their expiry date in pinnwand's
       database."""
    session = session_factory.make_session()
    pastes = session.query(Paste).filter(Paste.exp_date < datetime.now()).all()

    for paste in pastes:
        session.delete(paste)

    session.commit()

    log.info("reap: removed %d pastes", len(pastes))
