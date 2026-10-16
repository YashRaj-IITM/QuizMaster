def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_protected_routes_require_token(api):
    assert api.get("/api/admin/stats").status_code == 401
    assert api.get("/api/user/dashboard").status_code == 401
    assert api.get("/api/admin/stats", "abc").status_code == 401        # garbage token


def test_register_validation(api):
    assert api.register("s@x.com", password="123").status_code == 400
    assert api.register("nope").status_code == 400
    assert api.register("d@x.com", dob="2999-01-01").status_code == 400  # future date of birth
    assert api.post("/api/register", data="not json").status_code == 400


def test_register_and_duplicate_email(api):
    assert api.register("u1@x.com", qualification="B.Tech", dob="2002-05-10").status_code == 201
    assert api.register("U1@x.com").status_code == 409                  # case-insensitive


def test_login_payload_and_bad_credentials(api):
    api.register("u1@x.com")
    body = api.login("u1@x.com", "password1").get_json()
    assert body["success"] is True and body["is_admin"] is False and body["token"]
    assert api.login("u1@x.com", "wrong-password").status_code == 401
    assert api.login("x@y.com", "nope").status_code == 401


def test_admin_login_is_admin(api, app):
    body = api.login(app.config["ADMIN_EMAIL"], app.config["ADMIN_PASSWORD"]).get_json()
    assert body["is_admin"] is True


def test_me_endpoint(api, u1):
    assert api.get("/api/me", u1).get_json()["user"]["email"] == "u1@x.com"


def test_role_separation(api, admin, u1):
    assert api.get("/api/admin/subjects", u1).status_code == 403
    assert api.get("/api/user/dashboard", admin).status_code == 403


def test_logout_invalidates_token(api, u1):
    assert api.post("/api/logout", u1).status_code == 200
    assert api.get("/api/user/dashboard", u1).status_code == 401
