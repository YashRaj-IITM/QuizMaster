from flask import Blueprint, jsonify
from flask_security import (
    auth_required,
    current_user,
    hash_password,
    verify_and_update_password,
)

from extensions import db
from models import User, user_datastore
from utils import EMAIL_RE, ValidationError, error, json_body, parse_dob, text

auth_bp = Blueprint("auth_api", __name__, url_prefix="/api")


@auth_bp.post("/register")
def register():
    data = json_body()
    email = text(data.get("email"), "Email", required=True, max_len=150).lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("Enter a valid email address")
    password = data.get("password")
    if not isinstance(password, str) or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    full_name = text(data.get("full_name"), "Full name", min_len=2, max_len=150, required=True)
    qualification = text(data.get("qualification"), "Qualification", max_len=150)
    dob = parse_dob(data.get("dob"))
    if User.query.filter_by(email=email).first():
        return error("An account with this email already exists", 409)

    user_datastore.create_user(
        email=email,
        password=hash_password(password),
        full_name=full_name,
        qualification=qualification or None,
        dob=dob,
        roles=["user"],
        active=True,
    )
    db.session.commit()
    return jsonify({"success": True, "message": "Account created successfully! You can log in now."}), 201


@auth_bp.post("/login")
def login():
    data = json_body()
    email = text(data.get("email"), "Email").lower()
    password = data.get("password")
    user = User.query.filter_by(email=email).first()

    if not user or not isinstance(password, str) or not verify_and_update_password(password, user):
        return error("Invalid email or password", 401)
    if not user.active:
        return error("Your account has been deactivated", 403)

    db.session.commit()  # persists a rehashed password if Flask-Security upgraded it
    return jsonify(
        {
            "success": True,
            "token": user.get_auth_token(),
            "is_admin": user.is_admin,
            "full_name": user.full_name,
            "user": user.to_dict(),
        }
    ), 200


@auth_bp.post("/logout")
@auth_required("token")
def logout():
    # Rotating fs_uniquifier invalidates every token issued to this user
    user_datastore.set_uniquifier(current_user._get_current_object())
    db.session.commit()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@auth_bp.get("/me")
@auth_required("token")
def me():
    return jsonify({"user": current_user.to_dict()}), 200
