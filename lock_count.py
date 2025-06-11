from server import app, db
from models import Locker

with app.app_context():
    # Vypíš celkový počet záznamov v tabuľke Locker
    print(Locker.query.count(), "záznamov v tabuľke Locker")
    # Pre každý existujúci záznam vypíš jeho ID, či je aktívny, kto požiadal a komu je priradený, a jeho kód
    for l in Locker.query.all():
        print(l.id, l.is_active, l.requested_by, l.assigned_to, l.code)