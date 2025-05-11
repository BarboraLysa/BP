from server import app, db
from models import Locker

with app.app_context():
    print(Locker.query.count(), "záznamov v tabuľke Locker")
    for l in Locker.query.all():
        print(l.id, l.is_active, l.requested_by, l.assigned_to, l.code)