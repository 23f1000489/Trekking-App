from flask import Flask, render_template, redirect, url_for, request, flash
from flask import current_app as app
from .models import *
from .database import db
from datetime import datetime
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods = ['GET','POST'])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email = email).first()
        staff = Staff.query.filter_by(email = email).first()
        if user:
            if user.email == email:
                if user.password == password or check_password_hash(user.password, password):
                    if user.status == 'Approved':
                        return redirect(f"/user_dashboard/{user.id}")
                    elif user.status == 'approved' and user.email == "admin@user.com":
                        return redirect('/admin_dashboard')
                    else:
                        return redirect('/access_denied')
                else:
                    return redirect('/incorrect_credentials')
            else:
                return redirect('/incorrect_credentials')
        elif staff:
            if staff.email == email:
                if check_password_hash(staff.password, password):
                    if staff.status == 'Rejected':
                        return redirect('/access_denied')
                    else:
                        return redirect(f"/staff_dashboard/{staff.id}")
                else:
                    return redirect('/incorrect_credentials')
            else:
                return redirect('/incorrect_credentials')
        else:
            return redirect('/incorrect_credentials')
    return render_template("login.html")

@app.route("/register", methods = ['GET','POST'])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        role = request.form.get("role")
        password = generate_password_hash(request.form.get("password"))
        user = User.query.filter_by(email = email, phone = phone).first()
        staff = Staff.query.filter_by(email = email, phone = phone).first()
        if user or staff:
            return redirect('/login')
        elif role == 'trekker':
            new_user = User(name = name, email = email, phone = phone, password = password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(f"/user_dashboard/{new_user.id}")
        else :
            new_staff = Staff(name = name, email = email, phone = phone, password = password)
            db.session.add(new_staff)
            db.session.commit()
            return redirect('/permission')
    return render_template("register.html")

@app.route("/incorrect_credentials")
def incorrect_credentials():
    return render_template("incorrect_credentials.html")

@app.route("/permission")
def permission():
    return render_template("permission.html")

@app.route("/access_denied")
def access_denied():
    return render_template("access_denied.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    this_user = User.query.filter_by(email ='admin@user.com').first()
    bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    total_treks = len(Trek.query.all())
    total_users = len(User.query.filter_by(status = "Approved").all())
    total_staffs = len(Staff.query.all())
    total_bookings = len(Booking.query.all())
    return render_template("admin_dashboard.html",this_user = this_user,bookings = bookings,total_treks = total_treks, total_users = total_users, total_staffs = total_staffs, total_bookings = total_bookings)


@app.route("/admin_trek")
def admin_trek():
    treks = Trek.query.filter(or_(Trek.status == "Open", Trek.status == "Started", Trek.status == "Completed")).all()
    return render_template("admin_trek.html",treks = treks)

@app.route("/admin_trek_history")
def admin_trek_history():
    treks = Trek.query.filter(or_(Trek.status == "Cancelled", Trek.status == "Completed")).order_by(Trek.end_date.desc()).all()
    trek_participants = {}

    for trek in treks:
        count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        trek_participants[trek.id] = count
    return render_template("admin_trek_history.html",treks = treks, trek_participants = trek_participants)

@app.route("/admin_edit_trek/<int:trek_id>", methods = ['GET','POST'])
def admin_edit_trek(trek_id):
    trek = Trek.query.filter_by(id = trek_id).first()
    staffs = Staff.query.filter_by(status = 'Approved').all()
    if request.method == "POST":
        old_staff_id = trek.assigned_staff_id
        trek.trek_name = request.form.get("trek_name")
        trek.location = request.form.get("location")
        trek.difficulty = request.form.get("difficulty")
        trek.duration = request.form.get("duration")
        trek.available_slots = request.form.get("available_slots")
        trek.assigned_staff_id = request.form.get("assigned_staff_id")
        trek.start_date = datetime.strptime(request.form["start_date"], '%Y-%m-%d').date()
        trek.end_date = datetime.strptime(request.form["end_date"], '%Y-%m-%d').date()
        trek.status = request.form.get("status")
        trek.description = request.form.get("description")
        old_staff = Staff.query.filter_by(id = old_staff_id).first()
        
        if old_staff and old_staff.id != int(trek.assigned_staff_id):
            old_staff.status = "Approved"

        new_staff = Staff.query.filter_by(id=trek.assigned_staff_id).first()

        if new_staff:
            new_staff.status = "Assigned"
        db.session.commit()
        return redirect("/admin_trek")
    return render_template("admin_edit_trek.html",trek = trek, staffs = staffs)

@app.route("/delete_trek/<int:trek_id>")
def delete_trek(trek_id):
    trek = Trek.query.filter_by(id = trek_id).first()
    staff = Staff.query.filter_by(id = trek.assigned_staff_id).first()
    bookings = Booking.query.filter_by(trek_id = trek_id).all()
    if trek:
        if staff:
            staff.status = 'Approved'
        trek.status = 'Cancelled'
        for booking in bookings:
            booking.status = 'Cancelled'
        db.session.commit()
    return redirect("/admin_trek")


@app.route("/search_admin_trek")
def search_admin_trek():
    search_word = request.args.get('search')
    treks = Trek.query.filter(or_(Trek.trek_name.ilike(f"%{search_word}%"), Trek.id == search_word)).all()
    return render_template("search_admin_trek.html",treks = treks)

@app.route("/admin_new_trek", methods = ['GET','POST'])
def admin_new_trek():
    staffs = Staff.query.filter_by(status = 'Approved').all()
    if request.method == "POST":
        trek_name = request.form.get("trek_name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        duration = request.form.get("duration")
        available_slots = request.form.get("available_slots")
        assigned_staff_id = request.form.get("assigned_staff_id")
        start_date = datetime.strptime(request.form["start_date"], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form["end_date"], '%Y-%m-%d').date()
        status = request.form.get("status")
        description = request.form.get("description")
        trek = Trek.query.filter_by(trek_name = trek_name, start_date=start_date).first()
        if trek:
            flash("Trek already created!")
        else:
            selected_staff = Staff.query.filter_by(id=assigned_staff_id).first()
            if selected_staff:
                selected_staff.status = "Assigned"
            new_trek = Trek(trek_name = trek_name, location = location, difficulty = difficulty, duration = duration, available_slots = available_slots,
                            assigned_staff_id = assigned_staff_id, start_date = start_date, end_date = end_date, status = status, description = description)
            db.session.add(new_trek)
            db.session.commit()
        return redirect("/admin_trek")    
    return render_template("admin_new_trek.html",staffs = staffs)


@app.route("/admin_staff_active")
def admin_staff_active():
    active_staff = Staff.query.filter(or_(Staff.status == "Approved", Staff.status == "Assigned")).all()
    return render_template("admin_staff_active.html", active_staff = active_staff)

@app.route("/admin_staff_assigned")
def admin_staff_assigned():
    assigned_staff = Staff.query.filter_by(status = 'Assigned').all()
    return render_template("admin_staff_assigned.html", assigned_staff = assigned_staff)

@app.route("/admin_staff_available")
def admin_staff_available():
    available_staff = Staff.query.filter_by(status = 'Approved').all()
    treks = Trek.query.filter_by(status = 'Open').all()
    return render_template("admin_staff_available.html", available_staff = available_staff , treks = treks)

@app.route("/admin_staff_assign/<int:staff_id>", methods = ['GET','POST'])
def admin_staff_assign(staff_id):
    if request.method == "POST":
        trek_id = request.form.get("trek_id")
        
        if not trek_id:
            return redirect("/admin_staff_available")
        
        trek = Trek.query.filter_by(id = trek_id, status = "Open").first()
            
        if trek:
            old_staff = Staff.query.filter_by(id = trek.assigned_staff_id).first()
        
            if old_staff and old_staff.id != int(staff_id):
                    old_staff.status = "Approved"

        trek.assigned_staff_id = staff_id

        new_staff = Staff.query.filter_by(id=staff_id).first()

        if new_staff:
            new_staff.status = "Assigned"
        db.session.commit()
        return redirect("/admin_staff_available")
    

@app.route("/admin_staff_pending")
def admin_staff_pending():
    pending_staff = Staff.query.filter_by(status = 'Pending').all()
    return render_template("admin_staff_pending.html", pending_staff = pending_staff)

@app.route("/admin_staff_blacklisted")
def admin_staff_blacklisted():
    blacklisted_staff = Staff.query.filter_by(status = 'Rejected').all()
    return render_template("admin_staff_blacklisted.html", blacklisted_staff = blacklisted_staff)

@app.route("/search_admin_staff")
def search_admin_staff():
    search_word = request.args.get('search')
    staffs = Staff.query.filter(or_(Staff.name.ilike(f"%{search_word}%"), Staff.id == search_word)).all()
    return render_template("search_admin_staff.html",staffs = staffs)

@app.route("/admin_staff_approve/<int:staff_id>")
def admin_staff_approve(staff_id):
    staff = Staff.query.filter_by(id = staff_id ).first()
    if staff:
        staff.status = 'Approved'
        db.session.commit()
    return redirect('/admin_staff_active')

@app.route("/admin_staff_reject/<int:staff_id>")
def admin_staff_reject(staff_id):
    staff = Staff.query.filter_by(id = staff_id ).first()
    if staff:
        staff.status = 'Rejected'
        db.session.commit()
    return redirect('/admin_staff_blacklisted')

@app.route("/admin_users_active")
def admin_users_active():
    active_user = User.query.filter_by( status = 'Approved').all()
    return render_template("admin_users_active.html", active_user = active_user)

@app.route("/admin_users_blacklisted")
def admin_users_blacklisted():
    blacklisted_user = User.query.filter_by(status = 'Rejected').all()
    return render_template("admin_users_blacklisted.html", blacklisted_user = blacklisted_user)

@app.route("/admin_user_approve/<int:user_id>")
def admin_user_approve(user_id):
    user = User.query.filter_by(id = user_id ).first()
    if user:
        user.status = 'Approved'
        db.session.commit()
    return redirect('/admin_users_active')

@app.route("/admin_user_reject/<int:user_id>")
def admin_user_reject(user_id):
    user = User.query.filter_by(id = user_id ).first()
    if user:
        user.status = 'Rejected'
        db.session.commit()
    return redirect('/admin_users_blacklisted')

@app.route("/search_admin_users")
def search_admin_users():
    search_word = request.args.get('search')
    users = User.query.filter(or_(User.name.ilike(f"%{search_word}%"), User.id == search_word)).all()
    return render_template("search_admin_user.html",users = users)

@app.route("/admin_bookings")
def admin_bookings():
    bookings = Booking.query.filter(Booking.status == "Booked").all()
    return render_template("admin_bookings.html", bookings = bookings)

@app.route("/admin_booking_history")
def admin_booking_history():
    bookings = Booking.query.filter(or_(Booking.status == "Completed", Booking.status == "Cancelled")).all()
    return render_template("admin_booking_history.html", bookings = bookings)

@app.route("/admin_remove/<int:booking_id>")
def admin_remove(booking_id):
    booking = Booking.query.filter_by(id = booking_id ).first()
    if booking:
        booking.status = 'Cancelled'
        db.session.commit()
    return redirect('/admin_bookings')

@app.route("/search_admin_bookings")
def search_admin_bookings():
    search_word = request.args.get('search')
    query = Booking.query.join(User)
    bookings = query.filter(or_(User.name.ilike(f"%{search_word}%"), Booking.id == search_word)).all()
    return render_template("search_admin_bookings.html",bookings = bookings)

#Admin Dashboard
#Staff Dashboard


@app.route("/staff_dashboard/<int:staff_id>")
def staff_dashboard(staff_id):
    this_staff = Staff.query.filter_by(id = staff_id).first()
    assigned_trek = Trek.query.filter_by(assigned_staff_id = staff_id).all()
    total_trek = len(Trek.query.filter_by(assigned_staff_id = staff_id).all())
    open_trek = len(Trek.query.filter_by(assigned_staff_id = staff_id, status = 'Open').all())
    total_bookings = len(Booking.query.join(Trek).filter(Trek.assigned_staff_id == staff_id, Booking.status == 'Booked').all())
    trek_participants = {}

    for trek in assigned_trek:
        count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        trek_participants[trek.id] = count
    return render_template("staff_dashboard.html" ,this_staff = this_staff, assigned_trek = assigned_trek, total_trek = total_trek, open_trek = open_trek,total_bookings = total_bookings, trek_participants = trek_participants)

@app.route("/staff_trek/<int:staff_id>")
def staff_trek(staff_id):
    this_staff = Staff.query.filter_by(id = staff_id).first()
    assigned_trek = Trek.query.filter_by(assigned_staff_id = staff_id).all()
    trek_participants = {}

    for trek in assigned_trek:
        count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        trek_participants[trek.id] = count

    
    return render_template("staff_trek.html", this_staff = this_staff, assigned_trek = assigned_trek, trek_participants = trek_participants)

@app.route("/staff_update_slots/<int:staff_id>/<int:trek_id>", methods=["GET", "POST"])
def staff_update_slots(staff_id,trek_id):
    this_staff = Staff.query.filter_by(id = staff_id).first()
    assigned_trek = Trek.query.filter_by(assigned_staff_id = staff_id, id = trek_id).first()
    if request.method == "POST":
        assigned_trek.available_slots = request.form.get("available_slots")
        db.session.commit()
        return redirect(f"/staff_trek/{staff_id}")
    return render_template("staff_update_slots.html", this_staff = this_staff, assigned_trek = assigned_trek)


@app.route("/staff_participants/<int:staff_id>")
def staff_participants(staff_id):
    this_staff = Staff.query.filter_by(id = staff_id).first()
    trek = Trek.query.filter_by(assigned_staff_id = staff_id).first()
    if trek:
        bookings = Booking.query.filter_by(trek_id = trek.id, status = 'Booked').all()
    return render_template("staff_participants.html", this_staff = this_staff, bookings = bookings)

@app.route("/staff_remove_participant/<int:staff_id>/<int:trek_id>/<int:user_id>")
def staff_remove_participant(staff_id, trek_id,user_id):
    bookings = Booking.query.filter( Booking.trek_id == trek_id, Booking.user_id == user_id ).first()
    trek = Trek.query.filter_by(id = trek_id).first()
    if bookings and bookings.status == "Booked":
        bookings.status = "Cancelled"
        trek.available_slots = trek.available_slots + 1
        db.session.commit()
        return redirect(f'/staff_participants/{staff_id}')

@app.route("/staff_profile/<int:staff_id>")
def staff_profile(staff_id):
    this_staff = Staff.query.filter_by(id = staff_id).first()
    return render_template("staff_profile.html", this_staff = this_staff)

@app.route("/staff_edit_profile/<int:staff_id>", methods=["GET", "POST"])
def staff_edit_profile(staff_id):
    this_staff = Staff.query.filter_by(id = staff_id).first()
    if request.method == "POST":
        this_staff.name = request.form.get("name")
        this_staff.email = request.form.get("email")
        this_staff.phone = request.form.get("phone")
        this_staff.password = request.form.get("password")
        db.session.commit()
        return redirect(f"/staff_profile/{staff_id}")
    return render_template("staff_edit_profile.html", this_staff = this_staff)

@app.route("/trek_started/<int:staff_id>/<int:trek_id>")
def trek_started(staff_id, trek_id):
    trek = Trek.query.filter_by(assigned_staff_id = staff_id, id = trek_id ).first()
    if trek:
        trek.status = 'Started'
        db.session.commit()
    return redirect(f'/staff_trek/{staff_id}')

@app.route("/trek_completed/<int:staff_id>/<int:trek_id>")
def trek_completed(staff_id, trek_id):
    trek = Trek.query.filter_by(assigned_staff_id = staff_id, id = trek_id ).first()
    staff = Staff.query.filter_by(id = staff_id ).first()
    bookings = Booking.query.filter_by(trek_id = trek_id).all()
    if trek:
        trek.status = 'Completed'
        if staff:
            staff.status = 'Available'
        for booking in bookings:
            booking.status = 'Completed'
        db.session.commit()
    return redirect(f'/staff_trek/{staff_id}')

#Staff Dashboard
#User Dashboard

@app.route("/user_dashboard/<int:user_id>", methods = ['GET','POST'])
def user_dashboard(user_id):
    this_user = User.query.filter_by(id = user_id, status = "Approved").first()
    all_treks = Trek.query.filter_by(status = 'Open').all()
    my_treks = Booking.query.filter_by(user_id = user_id).all()
    return render_template("user_dashboard.html", this_user = this_user, all_treks = all_treks, my_treks = my_treks)

@app.route("/user_dashboard_filter/<int:user_id>", methods = ['GET','POST'])
def user_dashboard_filter(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    my_treks = Booking.query.filter_by(user_id = user_id).all()
    if request.method == "POST":
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        if difficulty != 'All' and location != 'All':
            all_treks = Trek.query.filter_by(difficulty = difficulty, location = location).all()
        elif difficulty:
            if difficulty == 'All':
                all_treks = Trek.query.filter_by(status = 'Open').all()
            else:
                all_treks = Trek.query.filter_by(difficulty = difficulty).all()
        elif location :
            if location == 'All':
                all_treks = Trek.query.filter_by(status = 'Open').all()
            else:
                all_treks = Trek.query.filter_by(location = location).all()
        else:
            all_treks = Trek.query.filter_by(status = 'Open').all()
    return render_template("user_dashboard.html", this_user = this_user, all_treks = all_treks, my_treks = my_treks)

@app.route("/search_user_trek/<int:user_id>", methods = ['GET','POST'])
def search_user_trek(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    search_word = request.args.get('search')
    all_treks = Trek.query.filter(or_(Trek.trek_name.ilike(f"%{search_word}%"), Trek.id == search_word)).all()
    return render_template("search_user_trek.html",this_user = this_user,all_treks = all_treks)


@app.route("/search_user_filter/<int:user_id>", methods = ['GET','POST'])
def search_user_filter(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    if request.method == "POST":
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        if difficulty != 'All' and location != 'All':
            all_treks = Trek.query.filter_by(difficulty = difficulty, location = location).all()
        elif difficulty:
            if difficulty == 'All':
                all_treks = Trek.query.filter_by(status = 'Open').all()
            else:
                all_treks = Trek.query.filter_by(difficulty = difficulty).all()
        elif location :
            if location == 'All':
                all_treks = Trek.query.filter_by(status = 'Open').all()
            else:
                all_treks = Trek.query.filter_by(location = location).all()
        else:
            all_treks = Trek.query.filter_by(status = 'Open').all()
    return render_template("user_trek.html", this_user = this_user, all_treks = all_treks)

@app.route("/user_trek/<int:user_id>", methods = ['GET','POST'])
def user_trek(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    all_treks = Trek.query.filter_by(status = 'Open').all()
    return render_template("user_trek.html", this_user = this_user, all_treks = all_treks)

@app.route("/user_trek_filter/<int:user_id>", methods = ['GET','POST'])
def user_trek_filter(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    if request.method == "POST":
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        if difficulty != 'All' and location != 'All':
            all_treks = Trek.query.filter_by(difficulty = difficulty, location = location).all()
        if difficulty:
            if difficulty == 'All':
                all_treks = Trek.query.filter_by(status = 'Open').all()
            else:
                all_treks = Trek.query.filter_by(difficulty = difficulty).all()
        if location :
            if location == 'All':
                all_treks = Trek.query.filter_by(status = 'Open').all()
            else:
                all_treks = Trek.query.filter_by(location = location).all()
        if difficulty != 'All' and location != 'All':
            all_treks = Trek.query.filter_by(difficulty = difficulty, location = location).all()
        else:
            all_treks = Trek.query.filter_by(status = 'Open').all()
    return render_template("user_trek.html", this_user = this_user, all_treks = all_treks)

@app.route("/user_bookings/<int:user_id>")
def user_bookings(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    my_treks = Booking.query.filter_by(user_id = user_id, status="Booked").all()
    return render_template("user_bookings.html",this_user = this_user, my_treks = my_treks)

@app.route("/user_history/<int:user_id>")
def user_history(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    my_treks = Booking.query.filter_by(user_id = user_id).all()
    return render_template("user_history.html", this_user = this_user, my_treks = my_treks)

@app.route("/user_profile/<int:user_id>")
def user_profile(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    return render_template("user_profile.html", this_user = this_user)

@app.route("/user_edit_profile/<int:user_id>", methods = ['GET','POST'])
def user_edit_profile(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    if request.method == "POST":
        this_user.name = request.form.get("name")
        this_user.email = request.form.get("email")
        this_user.phone = request.form.get("phone")
        this_user.password = request.form.get("password")
        db.session.commit()
        return redirect(f"/user_profile/{user_id}")
    return render_template("user_edit_profile.html", this_user = this_user)

@app.route("/user_trek_details/<int:user_id>/<int:trek_id>")
def user_trek_details(user_id,trek_id):
    this_user = User.query.filter_by(id = user_id).first()
    trek = Trek.query.filter_by(id = trek_id).first()
    return render_template("user_trek_details.html", this_user = this_user,trek = trek)

@app.route("/user_trek_booking/<int:user_id>/<int:trek_id>")
def user_trek_bookings(user_id, trek_id):
    bookings = Booking.query.filter_by(user_id = user_id, trek_id = trek_id ).first()
    trek = Trek.query.filter_by(id = trek_id).first()
    if bookings:
        if bookings.status == 'Booked' or bookings.status == 'Completed':
            return redirect(f'/user_bookings/{user_id}')
        elif bookings.status == 'Cancelled':
                bookings.status = 'Booked'
                db.session.commit()
    else:
        if trek.available_slots > 0 and trek.status == 'Open':
            new_booking = Booking(user_id=user_id, trek_id=trek_id, status="Booked")
            db.session.add(new_booking)
            trek.available_slots = trek.available_slots - 1
            db.session.commit()
    return redirect(f'/user_bookings/{user_id}')

@app.route("/user_trek_cancel/<int:user_id>/<int:trek_id>")
def user_trek_cancel(user_id, trek_id):
    bookings = Booking.query.filter_by(user_id = user_id, trek_id = trek_id ).first()
    trek = Trek.query.filter_by(id = trek_id).first()
    if bookings and bookings.status == "Booked":
        bookings.status = "Cancelled"
        trek.available_slots = trek.available_slots + 1
        db.session.commit()
    return redirect(f'/user_dashboard/{user_id}')

@app.route("/logout")
def logout():
    return render_template("index.html")