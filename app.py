import os
import uuid
import razorpay
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, flash, jsonify, session, url_for
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from urllib.parse import urlparse, urljoin
from authlib.integrations.flask_client import OAuth

load_dotenv()  # ← loads .env file

# ================================
# FLASK APP
# ================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


# ================================
# MAIL CONFIG
# ================================
app.config["MAIL_SERVER"]   = "smtp.gmail.com"
app.config["MAIL_PORT"]     = 587
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USERNAME"] = "thewebstudio.io@gmail.com"
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")

mail       = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)


# ================================
# SUPABASE CONNECTION
# ================================
SUPABASE_URL = "https://yuuvbsctwcrzubblkjlq.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

razorpay_client = razorpay.Client(auth=(
    os.environ.get("RAZORPAY_KEY_ID"),
    os.environ.get("RAZORPAY_KEY_SECRET")
))


# ================================
# GOOGLE OAUTH
# BUG WAS HERE: os.environ.get() needs a KEY NAME string,
# NOT the actual credential value as the argument
# ================================
oauth  = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),         # ← reads GOOGLE_CLIENT_ID from .env
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"), # ← reads GOOGLE_CLIENT_SECRET from .env
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# ================================
# SECURITY HELPER
# ================================
def is_safe_url(target):
    ref_url  = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


# # ================================
# # HELPER — PROJECT IMAGES
# # ================================
# def attach_project_images(projects):
#     images_res = supabase.table("project_images").select("project_id,image_url").execute()
#     image_map  = {}
#     for img in images_res.data:
#         pid = img["project_id"]
#         if pid not in image_map:
#             image_map[pid] = []
#         image_map[pid].append(img["image_url"])
#     for project in projects:
#         project_images       = image_map.get(project["id"], [])
#         project["images"]    = project_images
#         project["thumbnail"] = project_images[0] if project_images else None
#     return projects
# ================================
# HELPER — now uses JOIN via view
# ================================
def attach_project_images(projects):
    """Legacy helper kept for compatibility — use get_projects_with_images() for new code."""
    images_res = supabase.table("project_images").select("project_id,image_url").execute()
    image_map  = {}
    for img in images_res.data:
        pid = img["project_id"]
        if pid not in image_map:
            image_map[pid] = []
        image_map[pid].append(img["image_url"])
    for project in projects:
        project_images       = image_map.get(project["id"], [])
        project["images"]    = project_images
        project["thumbnail"] = project_images[0] if project_images else None
    return projects


def get_projects_with_images(limit=None, category=None, division=None):
    """
    Uses JOIN-based view — single DB round trip instead of 2.
    Returns projects with images[] and thumbnail already attached.
    """
    query = supabase.table("projects_with_images").select("*").order("created_at", desc=True)
    if category and category != "all":
        query = query.eq("category", category)
    if division and division != "all":
        query = query.eq("division", division)
    if limit:
        query = query.limit(limit)

    response = query.execute()
    projects = response.data

    # Normalize: images comes as JSON array from the view
    for project in projects:
        imgs = project.get("images") or []
        project["images"]    = imgs
        project["thumbnail"] = imgs[0] if imgs else None

    return projects


# ================= USER ROUTES ================= #

@app.route("/")
def index():
    projects = get_projects_with_images(limit=4)
    return render_template("index.html", projects=projects)


@app.route("/project/<project_id>")
def project_detail(project_id):
    if "user_id" not in session and not session.get("admin"):
        return redirect(url_for("login_page", next=request.url))
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        project  = response.data
        if not project:
            return render_template("404.html")
        images_response = supabase.table("project_images").select("image_url").eq("project_id", project_id).order("id").execute()
        return render_template("project_detail.html", project=project, images=images_response.data)
    except Exception as e:
        print("DETAIL ERROR:", e)
        return render_template("404.html")


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog-preview')
def blog_preview():
    return render_template('blog-preview.html')

@app.route('/blog-details')
def blog_details():
    return render_template('blog-details.html')

@app.route('/blog-details-1')
def blog_details_1():
    return render_template('blog-details-1.html')

@app.route('/blog-details-2')
def blog_details_2():
    return render_template('blog-details-2.html')

@app.route('/blog-details-3')
def blog_details_3():
    return render_template('blog-details-3.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route("/project")
def project():
    try:
        category = request.args.get("category")
        division = request.args.get("division")
        projects = get_projects_with_images(category=category, division=division)
        return render_template("project.html", projects=projects)
    except Exception as e:
        print("PROJECT LIST ERROR:", e)
        return render_template("404.html")

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/testimonial')
def testimonial():
    return render_template('testimonial.html')

@app.route('/404')
def error_page():
    return render_template('404.html')


# ================= ADMIN ROUTES ================= #

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get("admin"):
        flash("Admin access required", "error")
        return redirect(url_for("login_page"))
    response       = supabase.table("projects").select("id", count="exact", head=True).execute()
    total_projects = response.count if response.count else 0
    return render_template("admin/dashboard.html", total_projects=total_projects)

@app.route('/admin/blogs-dashboard')
def admin_blogs_dashboard():
    return render_template('admin/blogs-dashboard.html')

@app.route('/admin/create-blog')
def admin_create_blog():
    return render_template('admin/create-blogs.html')

@app.route('/admin/edit-blog')
def admin_edit_blog():
    return render_template('admin/edit-blogs.html')

@app.route('/admin/view-blogs')
def admin_view_blogs():
    return render_template('admin/view-blogs.html')

@app.route('/admin/messages')
def admin_messages():
    return render_template('admin/message-view.html')

@app.route('/admin/contact')
def admin_contact():
    return render_template('admin/admin-contact.html')


# ==========================================================
# ADD / UPDATE PROJECT
# ==========================================================
@app.route("/admin/add-project", methods=["POST"])
def add_project():
    try:
        files = request.files.getlist("image_file")

        has_price     = request.form.get("has_price") == "true"
        base_price    = request.form.get("base_price") if has_price else 0
        base_currency = request.form.get("base_currency") if has_price else "INR"
        division      = request.form.get("division", "A")

        #  EXISTING IMAGES (coming from hidden inputs)
        existing_images = request.form.getlist("existing_images")

        new_image_urls = []

        #  Upload NEW images
        for file in files:
            if file and file.filename != "":
                ext = file.filename.split('.')[-1]
                file_name = f"{uuid.uuid4()}.{ext}"

                file_bytes = file.read()

                supabase.storage.from_("project-images").upload(
                    file_name,
                    file_bytes,
                    {"content-type": file.content_type}
                )

                image_url = supabase.storage.from_("project-images").get_public_url(file_name)
                new_image_urls.append({"url": image_url})

        #  MERGE old + new images
        final_images = []

        # keep old
        for img in existing_images:
            final_images.append({"url": img})

        # add new
        for img in new_image_urls:
            final_images.append(img)

        # if empty → None
        p_images = final_images if final_images else None

        #  CALL SQL FUNCTION
        result = supabase.rpc("upsert_project", {
            "p_project_id": request.form.get("project_id") or None,
            "p_title": request.form.get("title"),
            "p_description": request.form.get("description"),
            "p_category": request.form.get("category"),
            "p_division": division,
            "p_has_price": has_price,
            "p_base_price": base_price,
            "p_base_currency": base_currency,
            "p_preview_link": request.form.get("preview_link"),
            "p_github_link": request.form.get("github_link"),
            "p_images": p_images
        }).execute()

        return jsonify({
            "success": True,
            "project_id": result.data
        })

    except Exception as e:
        print("UPLOAD ERROR:", str(e))
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# @app.route("/admin/projectback")
# def project_back():
#     projects = get_projects_with_images()
#     return render_template("admin/projectback.html", projects=projects)


@app.route("/admin/projectback")
def project_back():
    return render_template("admin/projectback.html")

@app.route("/admin/projects")
def all_projects():                  
    if not session.get("admin"):
        return redirect(url_for("login_page"))
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 10))
    category  = request.args.get("category") or None
    division  = request.args.get("division") or None
    offset    = (page - 1) * per_page
    try:
        result = supabase.rpc("get_projects_paginated", {
            "p_limit":    per_page,
            "p_offset":   offset,
            "p_category": category,
            "p_division": division
        }).execute()
        rows        = result.data
        total_count = rows[0]["total_count"] if rows else 0
        total_pages = (total_count + per_page - 1) // per_page
        for row in rows:
            imgs = row.get("images") or []
            row["thumbnail"] = imgs[0] if imgs else None
        return render_template(
            "admin/projects.html",
            projects    = rows,
            page        = page,
            per_page    = per_page,
            total_pages = total_pages,
            total_count = total_count
        )
    except Exception as e:
        print("PAGINATED ERROR:", e)
        return render_template("admin/projects.html", projects=[])

@app.route("/admin/delete-project/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    supabase.table("project_images").delete().eq("project_id", project_id).execute()
    supabase.table("projects").delete().eq("id", project_id).execute()
    return jsonify({"success": True})


@app.route("/admin/delete-image", methods=["POST"])
def delete_image():
    data      = request.json
    image_url = data.get("image_url")
    supabase.table("project_images").delete().eq("image_url", image_url).execute()
    return jsonify({"success": True})


# ================================
# REGISTER PAGE
# ================================
@app.route("/register")
def register_page():
    return render_template("register.html")


# ================================
# REGISTER USER — FIXED: added provider, better error display
# ================================
@app.route("/register", methods=["POST"])
def register_user():
    username = request.form.get("username", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not username or not email or not password:
        flash("All fields are required", "error")
        return redirect(url_for("register_page"))

    if len(password) < 6:
        flash("Password must be at least 6 characters", "error")
        return redirect(url_for("register_page"))

    hashed_password = generate_password_hash(password)

    try:
        existing_user = supabase.table("users") \
            .select("id") \
            .or_(f"email.eq.{email},username.eq.{username}") \
            .execute()

        if existing_user.data:
            flash("Username or email already exists", "error")
            return redirect(url_for("register_page"))

        # FIXED: include "provider" column — was missing before, caused DB insert to fail
        supabase.table("users").insert({
            "username": username,
            "email":    email,
            "password": hashed_password,
            "provider": "local"
        }).execute()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login_page"))

    except Exception as e:
        print("REGISTER ERROR:", e)
        flash(f"Registration failed: {str(e)}", "error")
        return redirect(url_for("register_page"))


# ================================
# LOGIN PAGE
# ================================
@app.route("/login")
def login_page():
    next_url = request.args.get("next", "")
    return render_template("login.html", next_url=next_url)


# ================================
# LOGIN FUNCTION
# ================================
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    next_url = data.get("next", "").strip()

    # --- ADMIN ---
    if username == "admin" and password == "pccoe":
        session["admin"]    = True
        session["username"] = "admin"
        return jsonify({"redirect": url_for("index")}), 200

    # --- NORMAL USER ---
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()

        if not response.data:
            return jsonify({"message": "User not found"}), 401

        user = response.data[0]

        # Google-only users should use Google login
        if user.get("provider") == "google":
            return jsonify({"message": "This account uses Google login. Click 'Continue with Google'."}), 401

        if check_password_hash(user["password"], password):
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            redirect_to = next_url if (next_url and is_safe_url(next_url)) else url_for("index")
            return jsonify({"redirect": redirect_to}), 200

        return jsonify({"message": "Invalid password"}), 401

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"message": "Login failed. Try again."}), 500


# ================================
# LOGOUT
# ================================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))


# ================================
# FORGOT PASSWORD
# ================================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user  = supabase.table("users").select("id, provider").eq("email", email).execute()

        if not user.data:
            flash("Email not registered", "error")
            return redirect(url_for("forgot_password"))

        if user.data[0].get("provider") == "google":
            flash("This account uses Google login. Please sign in with Google.", "warning")
            return redirect(url_for("login_page"))

        token      = serializer.dumps(email, salt="password-reset")
        reset_link = url_for("reset_password", token=token, _external=True)

        msg = Message(
            "Password Reset — WebRyx",
            sender="thewebstudio.io@gmail.com",
            recipients=[email]
        )
        msg.body = f"""Hi,

You requested a password reset for your WebRyx account.

Click the link below to reset your password (valid for 10 minutes):

{reset_link}

If you did not request this, you can safely ignore this email.

— The WebRyx Team
"""
        mail.send(msg)
        flash("Reset link sent to your email", "success")
        return redirect(url_for("login_page"))

    return render_template("forgot_password.html")


# ================================
# RESET PASSWORD
# ================================
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset", max_age=600)
    except Exception:
        flash("Reset link expired or invalid", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        hashed   = generate_password_hash(password)
        supabase.table("users").update({"password": hashed}).eq("email", email).execute()
        flash("Password updated successfully! Please login.", "success")
        return redirect(url_for("login_page"))

    return render_template("reset_password.html")


# ================================
# GOOGLE OAUTH — Step 1: Redirect
# ================================
@app.route("/login/google")
def google_login():
    next_url              = request.args.get("next", "")
    session["oauth_next"] = next_url
    redirect_uri          = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


# ================================
# GOOGLE OAUTH — Step 2: Callback — FIXED: added provider field
# ================================
@app.route("/login/google/callback")
def google_callback():
    try:
        token        = google.authorize_access_token()
        userinfo     = token.get("userinfo") or google.userinfo()
        google_email = userinfo.get("email")
        google_name  = userinfo.get("name", "")
        google_sub   = userinfo.get("sub")

        if not google_email:
            flash("Google login failed: no email returned.", "error")
            return redirect(url_for("login_page"))

        existing = supabase.table("users").select("*").eq("email", google_email).execute()

        if existing.data:
            user = existing.data[0]
        else:
            result = supabase.table("users").insert({
                "username":  google_name or google_email.split("@")[0],
                "email":     google_email,
                "password":  generate_password_hash(google_sub),
                "provider":  "google",
                "google_id": google_sub,
            }).execute()
            user = result.data[0]

        session["user_id"]  = user["id"]
        session["username"] = user["username"]

        next_url    = session.pop("oauth_next", "")
        redirect_to = next_url if (next_url and is_safe_url(next_url)) else url_for("index")
        return redirect(redirect_to)

    except Exception as e:
        print("GOOGLE OAUTH ERROR:", e)
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for("login_page"))


# ================================
# ADMIN USERS
# ================================
@app.route("/admin/users")
def admin_users():
    if not session.get("admin"):
        flash("Admin access required", "error")
        return redirect(url_for("login_page"))
    try:
        response = supabase.table("users").select("id, username, email, created_at, provider").order("id", desc=True).execute()
        users    = response.data
    except Exception as e:
        print("ADMIN USERS ERROR:", e)
        users = []
    return render_template("admin/users.html", users=users)

@app.route("/create-order", methods=["POST"])
def create_order():
    try:
        data = request.get_json()

        amount = int(float(data["amount"]) * 100)  # ₹ → paise

        order = razorpay_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        return jsonify(order)

    except Exception as e:
        print("ORDER ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ================= RUN APP ================= #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
