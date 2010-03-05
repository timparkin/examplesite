from optparse import OptionParser
from datetime import datetime
import smtplib
import couchdb


def log(email, error, verbose):
    if verbose > 0:
        print email, error

    
def send_email(email, smtphost):
    # Send email to new user
    server = smtplib.SMTP(smtphost)
    return server.sendmail(email['from'], [email['to']], email['msg'])


def send_emails(db, priority, smtphost, verbose):
    if verbose > 0:
        print 'db, priority, smtphost, verbose',db, priority, smtphost, verbose
    ### XXX Ignoring priority for now.
    while True:
        emails= [row.doc for row in db.view('email/undelivered_emails',
                                            include_docs=True, limit=25)]
        if not emails:
            break
        updated = []
        for email in emails:
            try:
                send_email(email, smtphost)
                email['delivered'] = datetime.utcnow().isoformat()
                updated.append(email)
            except smtplib.SMTPException, e:
                log(email, e.value, verbose)
        if updated:
            db.update(updated)


def parseOptions():
    parser = OptionParser()
    parser.add_option("-P", "--high-priority", dest="priority", action="store_const", default=None, const=100,
        help="Send high priority emails",
        metavar="PRIORITY")
    parser.add_option("-p", "--low-priority", dest="priority", action="store_const", default=None, const=0,
        help="Send low priority emails",
        metavar="PRIORITY")
    parser.add_option("-d", "--database", dest="db",
        help="Database to use for message queue",
        metavar="DATABASE")
    parser.add_option("-s", "--smtp", dest="smtphost", default='localhost',
                      help="SMTP server to use", metavar="SMTPHOST")
    parser.add_option("-v", "--verbose", action="store_const",
        dest="verbose", default=0, const=1,
        help="print status messages to stdout")
    (options, args) = parser.parse_args()
    db = couchdb.Database(options.db)
    send_emails(db, options.priority, options.smtphost, options.verbose)
 

if __name__ == "__main__":
    parseOptions()

