#!/usr/bin/python3.4
import argparse as ap, os, sqlite3 as sql, configparser,sys,time
from datetime import datetime, timedelta
u_home=os.path.expanduser("~")
dburl=""

def create_default_config():
    if not os.path.exists(u_home+"/.tmgr"):
        os.makedirs(u_home+"/.tmgr")
    confp=configparser.ConfigParser()
    confp["DEFAULT"]={"db":u_home+"/.tmgr/tmgr.db"}
    with open(u_home+"/.tmgrrc","w+") as conf:
        confp.write(conf)
    dbcon=sql.connect(u_home+"/.tmgr/tmgr.db")
    db=dbcon.cursor()
    db.execute("CREATE TABLE times(id INTEGER PRIMARY KEY, start DATETIME DEFAULT CURRENT_TIMESTAMP,stop DATETIME DEFAULT NULL, project VARCHAR)")
    dbcon.commit()

def start(args):
    dbcon=sql.connect(dburl)
    db=dbcon.cursor()
    db.execute("SELECT * FROM times WHERE project='%s' AND stop=NULL"%args.project)
    if db.fetchall()!=[]:
        print("Another timer for this project is currently running, close it first!")
        sys.exit(1)
    db.execute("INSERT INTO times(project) VALUES (?)",(args.project,))

    db.execute("SELECT start FROM times WHERE project=? AND stop=NULL",(args.project,))
    print("Timer started at %s"%db.fetchone())
    dbcon.commit()
    dbcon.close()

def stop(args):
    dbcon=sql.connect(dburl)
    db=dbcon.cursor()
    project="%s"%args.project
    db.execute("SELECT * FROM times WHERE project=? AND stop IS NULL",(project,))
    if db.fetchall()==[]:
        print("No timer running for this project.")
        sys.exit(1)
    ts=datetime.utcnow() + timedelta(days=1)
    db.execute("UPDATE times SET stop=? WHERE project=? and stop IS NULL",(ts,project))
    dbcon.commit()
    dbcon.close()
    print("Timer for project %s stopped."%args.project)

def dbprint(args):
    dbcon=sql.connect(dburl)
    db=dbcon.cursor()
    db.execute("SELECT project,TIME(SUM(strftime('%s',stop)-strftime('%s',start)),'unixepoch') FROM times GROUP BY project")
    result=db.fetchall()
    dbcon.close()
    print('{:*^30}|{:*^30}'.format("project","time"))
    for i in result:
        print('{0[0]:<30}|{0[1]:<30}'.format(i))

def status(args):
    dbcon=sql.connect(dburl)
    db=dbcon.cursor()
    db.execute("SELECT project,start FROM times where stop IS NULL")
    result=db.fetchall()
    dbcon.close()
    for i in result:
        t=datetime.utcnow() + timedelta(days=1) - datetime.fromtimestamp(time.mktime(time.strptime(i[1],"%Y-%m-%d %H:%M:%S")))
        print('%s:%s'%(i[0],t))
def default(args):
    sys.exit(0)

if not os.path.exists(u_home+"/.tmgrrc"):
    create_default_config()

conf=configparser.ConfigParser()
conf.read(u_home+"/.tmgrrc")
dburl=conf["DEFAULT"]["db"]


cliparser=ap.ArgumentParser(description="cli base time management tool")
clisp=cliparser.add_subparsers()
parser_start=clisp.add_parser('start')
parser_start.add_argument('project')
parser_start.set_defaults(func=start)

parser_stop=clisp.add_parser('stop')
parser_stop.add_argument('project')
parser_stop.set_defaults(func=stop)

parser_print=clisp.add_parser('print')
parser_print.set_defaults(func=dbprint)

parser_status=clisp.add_parser('status')
parser_status.set_defaults(func=status)

args=cliparser.parse_args()
args.func(args)



