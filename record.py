#!/usr/bin/env python


import argparse
import os
import sqlite3
import time
from datetime import datetime
import logging


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def ensure_dir(path):
    dirname = os.path.split(path)[0]
    if dirname == "":
        return
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    elif not os.path.isdir(dirname):
        raise RuntimeError(
            f"path '{dirname}' already exists and is not directory")


def environ(key, default=None):
    try:
        return os.environ[key]
    except KeyError as e:
        if default:
            return default
        else:
            raise e


class DB:
    def __init__(self, path):
        self._con = sqlite3.connect(path)
        self._con.row_factory = sqlite3.Row

    @staticmethod
    def create(path):
        sql = f"""
create table records (
  id integer primary key,
  case_ text not null,
  task text not null,
  contents text,
  start_time text not null,
  end_time text
)
"""
        logging.info(f"creating db: sql={sql}")
        with sqlite3.connect(path) as con:
            cur = con.cursor()
            cur.executescript(sql)
            con.commit()

    def insert_start(self, case, task, contents):
        sql = f"""
insert into records (case_, task, contents, start_time) values ('{case}', '{task}', '{contents}', '{current_time()}');
        """
        logging.info(f"inserting start: {sql}")
        cur = self._con.cursor()
        cur.executescript(sql)
        self._con.commit()

    def insert_end(self):
        sql = f"""
select id, end_time is null as isnull_ from records where id = (select max(id) from records);
"""
        cur = self._con.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        logging.info(f"checking end: {sql}")
        if row is None:
            logging.info(
                f"result of check: no record")
            raise RuntimeError("no task has begun")
        else:
            logging.info(
                f"id={row['id']}, isnull_={row['isnull_']}")
        if row["isnull_"] == 0:
            raise RuntimeError("no task has begun")
        id = row["id"]
        sql = f"""
update records set end_time='{current_time()}' where id={id};
"""
        logging.info(f"inserting end: {sql}")
        cur.execute(sql)
        self._con.commit()

    def list_records(self, day, name):
        sql = f"""
select case_, task, contents, time(start_time) as start_time, time(end_time) as end_time from records where date(start_time) = '{day}';
"""
        logging.info(f"list records: {sql}")
        cur = self._con.cursor()
        rows = cur.execute(sql)
        print("\n".join([
            "{day}\t{name}\t{start_time}\t{end_time}\t{case_}\t{task}\t{contents}".format(
                day=day,
                name=name,
                **row)
            for row in rows
        ]))


class Command:
    def __init__(self, subparsers, db):
        self._parser = subparsers.add_parser(self.name,
                                             help=self.__doc__)
        self._register_argument()
        self._parser.set_defaults(handler=self._handler)
        self._db = db

    def _register_argument(self):
        raise NotImplementedError(f"{type(self)}: _register_argument")

    def _handler(self, args):
        raise NotImplementedError(f"{type(self)}: _handler")


class Start(Command):
    """
    record start time
    """
    name = "start"

    def _register_argument(self):
        self._parser.add_argument("case", metavar="CASE",
                                  help="案件名")
        self._parser.add_argument("task", metavar="TASK",
                                  help="タスク")
        self._parser.add_argument("contents", metavar="CONTENTS",
                                  help="内容")

    def _handler(self, args):
        try:
            self._db.insert_end()
        except RuntimeError:
            pass

        task = dict(
            meeting="会議",
            coding="コーディング",
            interview="面接",
            report="資料作成",
            analysis="分析・検討・調査",
            moving="移動",
            review="レビュー",
            trip="出張"
        )[args.task]

        self._db.insert_start(args.case,
                              task,
                              args.contents)


class End(Command):
    """
    record end time
    """
    name = "end"

    def _register_argument(self):
        pass

    def _handler(self, args):
        self._db.insert_end()


class Print(Command):
    """
    print today's records
    """
    name = "print"

    def _register_argument(self):
        pass

    def _handler(self, args):
        t = today()
        name = environ("HOTOKU_RECORD_NAME")
        self._db.list_records(t, name)


class App:
    _commands = [
        Start,
        End,
        Print
    ]

    def __init__(self):
        self._parser = App._setup_parser()

    def run(self):
        args = self._parser.parse_args()
        if hasattr(args, "handler"):
            args.handler(args)
        else:
            self._parser.print_help()

    @staticmethod
    def _setup_parser():
        parser = argparse.ArgumentParser(description="record")
        subparsers = parser.add_subparsers()
        db = DB(App._db_path())
        for c in App._commands:
            c(subparsers, db)
        return parser

    @staticmethod
    def _db_path():
        return os.path.expanduser(
            environ("HOTOKU_RECORD_DBFILE", "~/.record/db.sqlite"))

    @staticmethod
    def setup_logger():
        logfile = os.path.expanduser(
            environ("HOTOKU_RECORD_LOGFILE", "~/.record/log.txt"))
        debug = environ("HOTOKU_RECORD_DEBUG", "False") == "True"
        ensure_dir(logfile)
        logging.basicConfig(
            format="[%(levelname)s]%(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG if debug else logging.INFO,
            filename=logfile
        )

    @staticmethod
    def setup_db():
        dbfile = App._db_path()
        ensure_dir(dbfile)
        logging.info(f"setting up db: {dbfile}")
        if not os.path.exists(dbfile):
            DB.create(dbfile)


def run():
    App.setup_logger()
    App.setup_db()
    logging.info(
        "================================================================")
    app = App()
    app.run()


if __name__ == "__main__":
    run()
