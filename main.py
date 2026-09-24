# -*- coding: utf-8 -*-
"""Pansiyon Nöbet Takip — Android (KivyMD)"""
import os, calendar, sqlite3
from datetime import date, datetime
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFillFlatButton
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast

APP_TITLE = "Pansiyon Nöbet"
DB_FILE = "pansiyon_nobet.db"
MONTHS = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
DH = 8

DEFAULT_TEACHERS = [
    "NAİF KÜLÜNÇE", "NABİ DEMİRBAŞ", "AHMET KESKİNBIÇAK", "LUTFİ BOZKURT",
    "HÜSEYİN UMA", "İBRAHİM YILMAZ", "CEVDET ÇETİN", "MUSTAFA KARA",
    "ERDAL ŞAKİR", "İSMAİL KARATAY", "FERDİ TİYESTİ", "ABDULSELAM ERİTMEZ",
    "ERCAN SÖNMEZ", "İSHAK YILDIZ", "SÜLEYMAN SARAÇOĞLU", "MEHMET ALİ GÖMÜK",
    "ABDULKADİR HARTAVİ", "FATİH SAKINMAZ", "RÜSTEM TAŞ", "MÜSLÜM KAYA",
    "MAHMUT YILMAZ", "CİHAN ATMACA", "HABİP İMAMOĞLU", "FARUK TOPRAK",
    "OSMAN HARMAN", "AYHAN DOĞAN", "ALİ ÖZGÜR CEYLAN", "MAHMUT KILIÇ",
    "EMRE YILMAZ", "SERHAT ERGİN", "EMRE DEMİR", "MEHMET YAHYA DURMUŞ"]


class DB:
    def __init__(self, path=DB_FILE):
        try:
            from android.storage import app_storage_path
            path = os.path.join(app_storage_path(), path)
        except Exception:
            pass
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS teachers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,active INTEGER DEFAULT 1)")
        c.execute("""CREATE TABLE IF NOT EXISTS duties(id INTEGER PRIMARY KEY AUTOINCREMENT,duty_date TEXT UNIQUE,teacher1 TEXT DEFAULT '',teacher2 TEXT DEFAULT '',teacher3 TEXT DEFAULT '',backup TEXT DEFAULT '',hours INTEGER DEFAULT 8,locked INTEGER DEFAULT 0,manual INTEGER DEFAULT 1,note TEXT DEFAULT '')""")
        c.execute("CREATE TABLE IF NOT EXISTS leaves(id INTEGER PRIMARY KEY AUTOINCREMENT,teacher TEXT,start_date TEXT,end_date TEXT,ltype TEXT DEFAULT 'İZİN')")
        c.execute("CREATE TABLE IF NOT EXISTS holidays(date TEXT PRIMARY KEY,name TEXT DEFAULT '')")
        c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT DEFAULT '')")
        self.conn.commit()
        for n in DEFAULT_TEACHERS:
            c.execute("INSERT OR IGNORE INTO teachers(name) VALUES(?)", (n,))
        self.conn.commit()

    def teachers(self):
        return self.conn.execute("SELECT * FROM teachers WHERE active=1 ORDER BY name").fetchall()
    def teacher_names(self):
        return [r["name"] for r in self.teachers()]
    def add_teacher(self, n):
        n = " ".join(n.strip().upper().split())
        if not n: return False
        try:
            self.conn.execute("INSERT INTO teachers(name) VALUES(?)", (n,))
            self.conn.commit(); return True
        except sqlite3.IntegrityError: return False
    def del_teacher(self, n):
        self.conn.execute("UPDATE teachers SET active=0 WHERE name=?", (n,)); self.conn.commit()
    def get_duty(self, d):
        return self.conn.execute("SELECT * FROM duties WHERE duty_date=?", (d,)).fetchone()
    def month_duties(self, y, m):
        s = f"{y:04d}-{m:02d}-01"
        e = f"{y:04d}-{m:02d}-{calendar.monthrange(y,m)[1]:02d}"
        return self.conn.execute("SELECT * FROM duties WHERE duty_date BETWEEN ? AND ? ORDER BY duty_date", (s,e)).fetchall()
    def save_duty(self, d, t1="", t2="", t3="", b="", h=DH, mn=1, note=""):
        self.conn.execute("""INSERT INTO duties(duty_date,teacher1,teacher2,teacher3,backup,hours,manual,note) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(duty_date) DO UPDATE SET teacher1=excluded.teacher1,teacher2=excluded.teacher2,teacher3=excluded.teacher3,backup=excluded.backup,hours=excluded.hours,manual=excluded.manual,note=excluded.note""", (d,t1,t2,t3,b,h,mn,note))
        self.conn.commit()
    def del_duty(self, d):
        self.conn.execute("DELETE FROM duties WHERE duty_date=?", (d,)); self.conn.commit()
    def stats(self, y, m):
        base = {"weekday":0,"weekend":0,"total":0,"hours":0}
        res = {n: dict(base) for n in self.teacher_names()}
        for r in self.month_duties(y,m):
            d = datetime.strptime(r["duty_date"],"%Y-%m-%d").date()
            h = r["hours"] or DH
            for n in (r["teacher1"],r["teacher2"],r["teacher3"]):
                if not n: continue
                res.setdefault(n, dict(base))
                res[n]["total"] += 1; res[n]["hours"] += h
                if d.weekday() >= 5: res[n]["weekend"] += 1
                else: res[n]["weekday"] += 1
        return res
    def add_leave(self, t, s, e, ty="İZİN"):
        self.conn.execute("INSERT INTO leaves(teacher,start_date,end_date,ltype) VALUES(?,?,?,?)", (t,s,e,ty)); self.conn.commit()
    def leaves(self):
        return self.conn.execute("SELECT * FROM leaves ORDER BY start_date DESC").fetchall()
    def del_leave(self, i):
        self.conn.execute("DELETE FROM leaves WHERE id=?", (i,)); self.conn.commit()
    def is_on_leave(self, t, d):
        r = self.conn.execute("SELECT COUNT(*) FROM leaves WHERE teacher=? AND start_date<=? AND end_date>=?", (t,d,d)).fetchone()
        return r[0] > 0
    def add_holiday(self, d, n=""):
        self.conn.execute("INSERT INTO holidays(date,name) VALUES(?,?) ON CONFLICT(date) DO UPDATE SET name=excluded.name", (d,n)); self.conn.commit()
    def holidays(self):
        return self.conn.execute("SELECT * FROM holidays ORDER BY date").fetchall()
    def is_holiday(self, d):
        return bool(self.conn.execute("SELECT 1 FROM holidays WHERE date=?", (d,)).fetchone())
    def del_holiday(self, d):
        self.conn.execute("DELETE FROM holidays WHERE date=?", (d,)); self.conn.commit()
    def set_setting(self, k, v):
        self.conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k,str(v))); self.conn.commit()
    def setting(self, k, d=""):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (k,)).fetchone()
        return r["value"] if r else d


class BaseScreen(MDScreen):
    def __init__(self, app, **kw):
        super().__init__(**kw); self.app = app; self.build_ui()
    def refresh(self): pass


class HomeScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Pansiyon Nöbet", elevation=4,
            left_action_items=[["menu", lambda x: self.app.open_nav()]],
            right_action_items=[["refresh", lambda x: self.refresh()]]))
        self.month_lbl = MDLabel(text="", halign="center", font_style="H6", bold=True, size_hint_y=None, height="40dp")
        root.add_widget(self.month_lbl)
        self.stats_box = MDBoxLayout(orientation="vertical", spacing="8dp", padding="12dp", size_hint_y=None)
        self.stats_box.bind(minimum_height=self.stats_box.setter("height"))
        self.labels = {}
        for k, t in [("days","Nöbetli Gün"),("duties","Toplam Nöbet"),("hours","Toplam Saat"),("teachers","Aktif Öğretmen")]:
            c = MDCard(orientation="horizontal", padding="12dp", size_hint_y=None, height="70dp", radius=[10])
            lbl = MDLabel(text=f"{t}: 0", halign="center", font_style="Subtitle1", bold=True)
            c.add_widget(lbl); self.labels[k] = lbl; self.stats_box.add_widget(c)
        root.add_widget(self.stats_box)
        btns = MDBoxLayout(orientation="vertical", spacing="8dp", padding="12dp", size_hint_y=None, height="220dp")
        btns.add_widget(MDFillFlatButton(text="➕ Nöbet Ekle", size_hint_y=None, height="48dp", on_release=lambda x: self.app.edit_duty(date.today())))
        btns.add_widget(MDFillFlatButton(text="⚡ Otomatik Dağıt", size_hint_y=None, height="48dp", on_release=self.app.auto_distribute))
        btns.add_widget(MDFlatButton(text="📅 Çizelge", size_hint_y=None, height="48dp", on_release=lambda x: self.app.go("schedule")))
        btns.add_widget(MDFlatButton(text="📊 Rapor", size_hint_y=None, height="48dp", on_release=lambda x: self.app.go("report")))
        root.add_widget(btns)
        self.add_widget(root)
    def refresh(self):
        self.month_lbl.text = f"{MONTHS[self.app.month]} {self.app.year}"
        rows = self.app.db.month_duties(self.app.year, self.app.month)
        duties = sum(sum(1 for x in (r["teacher1"],r["teacher2"],r["teacher3"]) if x) for r in rows)
        hours = sum((r["hours"] or DH) * sum(1 for x in (r["teacher1"],r["teacher2"],r["teacher3"]) if x) for r in rows)
        days = sum(1 for r in rows if any((r["teacher1"],r["teacher2"],r["teacher3"])))
        for k,v in [("days",days),("duties",duties),("hours",hours),("teachers",len(self.app.db.teacher_names()))]:
            self.labels[k].text = f"{dict(days='Nöbetli Gün',duties='Toplam Nöbet',hours='Toplam Saat',teachers='Aktif Öğretmen')[k]}: {v}"


class ScheduleScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Nöbet Çizelgesi", elevation=4,
            left_action_items=[["arrow-left", lambda x: self.app.prev_month()]],
            right_action_items=[["arrow-right", lambda x: self.app.next_month()]]))
        self.month_lbl = MDLabel(text="", halign="center", bold=True, size_hint_y=None, height="36dp")
        root.add_widget(self.month_lbl)
        self.lv = MDList(); sc = MDScrollView(); sc.add_widget(self.lv); root.add_widget(sc)
        self.add_widget(root)
    def refresh(self):
        self.month_lbl.text = f"{MONTHS[self.app.month]} {self.app.year}"
        self.lv.clear_widgets()
        for d in range(1, calendar.monthrange(self.app.year, self.app.month)[1] + 1):
            dt = date(self.app.year, self.app.month, d)
            r = self.app.db.get_duty(dt.isoformat())
            wd = DAYS[dt.weekday()]
            if r and any((r["teacher1"],r["teacher2"],r["teacher3"])):
                names = " • ".join(x for x in (r["teacher1"],r["teacher2"],r["teacher3"]) if x)
                sub = names
                ter = f"{r['hours'] or DH} saat" + (" 🔒" if r["locked"] else "")
            else:
                sub = "— boş —"; ter = ""
            item = ThreeLineListItem(text=f"{dt.strftime('%d.%m.%Y')} ({wd})",
                secondary_text=sub, tertiary_text=ter,
                on_release=lambda x, dd=dt: self.app.edit_duty(dd))
            self.lv.add_widget(item)


class TeachersScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Öğretmenler", elevation=4,
            right_action_items=[["plus", lambda x: self.app.add_teacher_dialog()]]))
        self.lv = MDList(); sc = MDScrollView(); sc.add_widget(self.lv); root.add_widget(sc)
        self.add_widget(root)
    def refresh(self):
        self.lv.clear_widgets()
        s = self.app.db.stats(self.app.year, self.app.month)
        for n in sorted(self.app.db.teacher_names()):
            st = s.get(n, {"total":0,"hours":0})
            self.lv.add_widget(TwoLineListItem(text=n,
                secondary_text=f"Bu ay: {st['total']} nöbet • {st['hours']} saat",
                on_release=lambda x, nn=n: self.app.teacher_menu(nn)))


class LeavesScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="İzin / Rapor", elevation=4,
            right_action_items=[["plus", lambda x: self.app.add_leave_dialog()]]))
        self.lv = MDList(); sc = MDScrollView(); sc.add_widget(self.lv); root.add_widget(sc)
        self.add_widget(root)
    def refresh(self):
        self.lv.clear_widgets()
        for r in self.app.db.leaves():
            self.lv.add_widget(ThreeLineListItem(text=r["teacher"],
                secondary_text=f"{r['start_date']} → {r['end_date']}",
                tertiary_text=r["ltype"],
                on_release=lambda x, i=r["id"]: self.app.del_leave_dialog(i)))


class HolidaysScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Tatiller", elevation=4,
            right_action_items=[["plus", lambda x: self.app.add_holiday_dialog()]]))
        self.lv = MDList(); sc = MDScrollView(); sc.add_widget(self.lv); root.add_widget(sc)
        self.add_widget(root)
    def refresh(self):
        self.lv.clear_widgets()
        for r in self.app.db.holidays():
            self.lv.add_widget(TwoLineListItem(text=r["date"], secondary_text=r["name"] or "-",
                on_release=lambda x, d=r["date"]: self.app.del_holiday_dialog(d)))


class ReportScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Aylık Puantaj", elevation=4,
            right_action_items=[["arrow-left", lambda x: self.app.prev_month()],
                                ["arrow-right", lambda x: self.app.next_month()]]))
        self.month_lbl = MDLabel(text="", halign="center", bold=True, size_hint_y=None, height="36dp")
        root.add_widget(self.month_lbl)
        self.lv = MDList(); sc = MDScrollView(); sc.add_widget(self.lv); root.add_widget(sc)
        self.add_widget(root)
    def refresh(self):
        self.month_lbl.text = f"{MONTHS[self.app.month]} {self.app.year}"
        self.lv.clear_widgets()
        s = self.app.db.stats(self.app.year, self.app.month)
        fee = float(self.app.db.setting("fee_per_hour","0") or 0)
        for n in sorted(s):
            st = s[n]
            ek = f" • {st['hours']*fee:.0f}₺" if fee > 0 else ""
            self.lv.add_widget(ThreeLineListItem(text=n,
                secondary_text=f"HI {st['weekday']} • HS {st['weekend']}",
                tertiary_text=f"Toplam {st['total']} nöbet • {st['hours']} saat{ek}"))


class SettingsScreen(BaseScreen):
    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(MDTopAppBar(title="Ayarlar", elevation=4))
        form = MDBoxLayout(orientation="vertical", spacing="12dp", padding="16dp", size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        self.school = MDTextField(hint_text="Okul Adı")
        self.fee = MDTextField(hint_text="Saatlik Ücret (₺)", input_filter="float")
        form.add_widget(self.school); form.add_widget(self.fee)
        form.add_widget(MDFillFlatButton(text="Kaydet", size_hint_y=None, height="48dp", on_release=self.save))
        form.add_widget(MDFlatButton(text="Hazır Tatilleri Yükle", size_hint_y=None, height="48dp", on_release=self.load_h))
        root.add_widget(form); self.add_widget(root)
    def refresh(self):
        self.school.text = self.app.db.setting("school","DİREKLİ AYHAN ŞAHENK MTAL")
        self.fee.text = self.app.db.setting("fee_per_hour","0")
    def save(self, *a):
        self.app.db.set_setting("school", self.school.text.strip())
        self.app.db.set_setting("fee_per_hour", self.fee.text.strip() or "0")
        toast("Kaydedildi")
    def load_h(self, *a):
        y = self.app.year
        defaults = [(f"{y}-01-01","Yılbaşı"),(f"{y}-04-23","Ulusal Egemenlik ve Çocuk Bayramı"),(f"{y}-05-01","Emek ve Dayanışma Günü"),(f"{y}-05-19","Atatürk'ü Anma, Gençlik ve Spor Bayramı"),(f"{y}-07-15","Demokrasi ve Milli Birlik Günü"),(f"{y}-08-30","Zafer Bayramı"),(f"{y}-10-29","Cumhuriyet Bayramı")]
        for d, n in defaults: self.app.db.add_holiday(d, n)
        toast(f"{len(defaults)} tatil yüklendi")


class PansiyonApp(MDApp):
    def __init__(self, **kw):
        super().__init__(**kw); self.year = 2026; self.month = 9

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.title = APP_TITLE
        self.db = DB()
        self.sm = MDScreenManager()
        self.screens = {}
        for name, cls in [("home",HomeScreen),("schedule",ScheduleScreen),
                          ("teachers",TeachersScreen),("leaves",LeavesScreen),
                          ("holidays",HolidaysScreen),("report",ReportScreen),
                          ("settings",SettingsScreen)]:
            s = cls(self, name=name); self.screens[name] = s; self.sm.add_widget(s)
        Clock.schedule_once(lambda dt: self.refresh_all(), 0.3)
        return self.sm

    def go(self, name):
        self.sm.current = name; self.screens[name].refresh()
    def refresh_all(self):
        for s in self.screens.values(): s.refresh()
    def prev_month(self):
        self.month -= 1
        if self.month == 0: self.month, self.year = 12, self.year - 1
        self.refresh_all()
    def next_month(self):
        self.month += 1
        if self.month == 13: self.month, self.year = 1, self.year + 1
        self.refresh_all()
    def open_nav(self):
        items = [{"text": n, "viewclass": "OneLineListItem",
                  "on_release": (lambda k=k: (self.go(k), m.dismiss()))}
                 for k, n in [("home","Ana Sayfa"),("schedule","Çizelge"),
                              ("teachers","Öğretmenler"),("leaves","İzin"),
                              ("holidays","Tatiller"),("report","Rapor"),
                              ("settings","Ayarlar")]]
        m = MDDropdownMenu(caller=self.screens["home"].children[0].children[-1], items=items, width_mult=4)
        m.open()

    def edit_duty(self, d):
        if isinstance(d, str): d = datetime.strptime(d, "%Y-%m-%d").date()
        r = self.db.get_duty(d.isoformat())
        content = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None, height="420dp", padding="10dp")
        date_f = MDTextField(hint_text="Tarih (YYYY-AA-GG)", text=d.isoformat())
        t1 = MDTextField(hint_text="Belletiçi 1", text=r["teacher1"] if r else "")
        t2 = MDTextField(hint_text="Belletiçi 2", text=r["teacher2"] if r else "")
        t3 = MDTextField(hint_text="Belletiçi 3", text=r["teacher3"] if r else "")
        bk = MDTextField(hint_text="Yedek", text=r["backup"] if r else "")
        hr = MDTextField(hint_text="Saat", text=str(r["hours"] if r else DH), input_filter="int")
        for w in (date_f,t1,t2,t3,bk,hr): content.add_widget(w)
        def save(*a):
            try:
                dd = datetime.strptime(date_f.text.strip(), "%Y-%m-%d").date()
                self.db.save_duty(dd.isoformat(), t1.text.strip().upper(),
                    t2.text.strip().upper(), t3.text.strip().upper(),
                    bk.text.strip().upper(), int(hr.text or DH), 1, "")
                toast("Kaydedildi"); dlg.dismiss(); self.refresh_all()
            except Exception as e: toast(f"Hata: {e}")
        def dele(*a):
            self.db.del_duty(d.isoformat()); toast("Silindi"); dlg.dismiss(); self.refresh_all()
        btns = [MDFlatButton(text="Kapat", on_release=lambda x: dlg.dismiss())]
        if r: btns.append(MDFlatButton(text="Sil", on_release=dele))
        btns.append(MDFillFlatButton(text="Kaydet", on_release=save))
        dlg = MDDialog(title=f"Nöbet — {d.strftime('%d.%m.%Y')}", type="custom", content_cls=content, buttons=btns)
        dlg.open()

    def auto_distribute(self, *a):
        teachers = self.db.teacher_names()
        if len(teachers) < 3: return toast("En az 3 öğretmen gerekli")
        counts = {n: self.db.stats(self.year, self.month).get(n, {"total":0})["total"] for n in teachers}
        added = 0
        for d in range(1, calendar.monthrange(self.year, self.month)[1] + 1):
            dt = date(self.year, self.month, d); ds = dt.isoformat()
            ex = self.db.get_duty(ds)
            if ex and any((ex["teacher1"],ex["teacher2"],ex["teacher3"])): continue
            if self.db.is_holiday(ds): continue
            pool = [n for n in teachers if not self.db.is_on_leave(n, ds)] or teachers
            pool.sort(key=lambda n: (counts[n], n))
            ch = pool[:3]
            self.db.save_duty(ds, *ch, h=DH, mn=0, note="Otomatik")
            for n in ch: counts[n] += 1
            added += 1
        toast(f"{added} gün dağıtıldı"); self.refresh_all()

    def add_teacher_dialog(self, *a):
        content = MDBoxLayout(orientation="vertical", padding="10dp", size_hint_y=None, height="90dp")
        tf = MDTextField(hint_text="Adı Soyadı"); content.add_widget(tf)
        def save(*a):
            ok = self.db.add_teacher(tf.text)
            toast("Eklendi" if ok else "Zaten var")
            dlg.dismiss(); self.refresh_all()
        dlg = MDDialog(title="Yeni Öğretmen", type="custom", content_cls=content,
            buttons=[MDFlatButton(text="İptal", on_release=lambda x: dlg.dismiss()),
                     MDFillFlatButton(text="Ekle", on_release=save)])
        dlg.open()

    def teacher_menu(self, n):
        d = MDDialog(title=n, text="Bu öğretmen pasifleştirilsin mi?",
            buttons=[MDFlatButton(text="Kapat", on_release=lambda x: d.dismiss()),
                     MDFillFlatButton(text="Pasifleştir",
                        on_release=lambda x: (self.db.del_teacher(n), d.dismiss(), self.refresh_all()))])
        d.open()

    def add_leave_dialog(self, *a):
        content = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None, height="320dp", padding="10dp")
        ts = self.db.teacher_names()
        t = MDTextField(hint_text="Öğretmen", text=ts[0] if ts else "")
        s = MDTextField(hint_text="Başlangıç (YYYY-AA-GG)", text=date.today().isoformat())
        e = MDTextField(hint_text="Bitiş (YYYY-AA-GG)", text=date.today().isoformat())
        ty = MDTextField(hint_text="Tür", text="İZİN")
        for w in (t,s,e,ty): content.add_widget(w)
        def save(*a):
            try:
                self.db.add_leave(t.text.strip().upper(), s.text.strip(), e.text.strip(), ty.text.strip().upper())
                toast("Kaydedildi"); dlg.dismiss(); self.refresh_all()
            except Exception as ex: toast(f"Hata: {ex}")
        dlg = MDDialog(title="Yeni İzin", type="custom", content_cls=content,
            buttons=[MDFlatButton(text="İptal", on_release=lambda x: dlg.dismiss()),
                     MDFillFlatButton(text="Kaydet", on_release=save)])
        dlg.open()

    def del_leave_dialog(self, i):
        d = MDDialog(title="Sil", text="Bu izin silinsin mi?",
            buttons=[MDFlatButton(text="İptal", on_release=lambda x: d.dismiss()),
                     MDFillFlatButton(text="Sil", on_release=lambda x: (self.db.del_leave(i), d.dismiss(), self.refresh_all()))])
        d.open()

    def add_holiday_dialog(self, *a):
        content = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None, height="180dp", padding="10dp")
        dt = MDTextField(hint_text="Tarih (YYYY-AA-GG)", text=date.today().isoformat())
        nm = MDTextField(hint_text="Açıklama")
        content.add_widget(dt); content.add_widget(nm)
        def save(*a):
            try:
                self.db.add_holiday(dt.text.strip(), nm.text.strip())
                toast("Kaydedildi"); dlg.dismiss(); self.refresh_all()
            except Exception as ex: toast(f"Hata: {ex}")
        dlg = MDDialog(title="Yeni Tatil", type="custom", content_cls=content,
            buttons=[MDFlatButton(text="İptal", on_release=lambda x: dlg.dismiss()),
                     MDFillFlatButton(text="Kaydet", on_release=save)])
        dlg.open()

    def del_holiday_dialog(self, d):
        dlg = MDDialog(title="Sil", text=f"{d} silinsin mi?",
            buttons=[MDFlatButton(text="İptal", on_release=lambda x: dlg.dismiss()),
                     MDFillFlatButton(text="Sil", on_release=lambda x: (self.db.del_holiday(d), dlg.dismiss(), self.refresh_all()))])
        dlg.open()


if __name__ == "__main__":
    PansiyonApp().run()
