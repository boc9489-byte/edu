from __future__ import annotations


def close_subject_as_live_cohort(db, subject):
    with db["cursor"]() as (_, cursor):
        cursor.execute(
            "UPDATE series SET sale_status = 'on_sale', delivery_mode = 'online_live' WHERE id = %s",
            (subject["series_id"],),
        )
        cursor.execute(
            """
            UPDATE series_cohort
            SET yn = 1,
                end_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY),
                max_student_count = current_student_count + 1
            WHERE id = %s
            """,
            (subject["cohort_id"],),
        )


def test_get_me(client, samples, user_headers):
    user = samples.user_with_student
    response = client.get("/api/v1/me", headers=user_headers(user["user_id"]))
    assert response.status_code == 200
    assert response.json()["data"]["userId"] == user["user_id"]


def test_get_student_profile(client, samples, user_headers):
    user = samples.user_with_student
    response = client.get(
        "/api/v1/me/student-profile",
        headers=user_headers(user["user_id"]),
    )
    assert response.status_code == 200
    assert response.json()["data"]["studentId"] == user["student_id"]


def test_get_learning_summary(client, samples, user_headers):
    user = samples.user_with_student
    response = client.get(
        "/api/v1/me/learning-summary",
        headers=user_headers(user["user_id"]),
    )
    assert response.status_code == 200
    assert "recentLearningRecords" in response.json()["data"]


def test_get_series_list(client):
    response = client.get("/api/v1/series", params={"pageNo": 1, "pageSize": 5})
    assert response.status_code == 200
    assert response.json()["data"]["total"] > 0


def test_get_series_list_with_keyword(client, samples, user_headers):
    series = samples.on_sale_series
    user = samples.user_with_student
    response = client.get(
        "/api/v1/series",
        params={"keyword": str(series["series_name"])[:6], "pageNo": 1, "pageSize": 5},
        headers=user_headers(user["user_id"]),
    )
    assert response.status_code == 200
    assert isinstance(response.json()["data"]["list"], list)


def test_get_series_detail(client, samples):
    row = samples.on_sale_series_with_cohort
    response = client.get(f"/api/v1/series/{row['series_id']}")
    assert response.status_code == 200
    assert response.json()["data"]["seriesId"] == row["series_id"]


def test_get_series_cohorts(client, samples):
    row = samples.on_sale_series_with_cohort
    response = client.get(f"/api/v1/series/{row['series_id']}/cohorts")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_get_cohort_detail(client, samples):
    row = samples.on_sale_series_with_cohort
    response = client.get(f"/api/v1/cohorts/{row['cohort_id']}")
    assert response.status_code == 200
    assert response.json()["data"]["cohortId"] == row["cohort_id"]


def test_get_series_cohorts_filters_closed_live_cohort(
    client, db, availability_subject
):
    close_subject_as_live_cohort(db, availability_subject)
    response = client.get(f"/api/v1/series/{availability_subject['series_id']}/cohorts")
    assert response.status_code == 200
    cohort_ids = [item["cohortId"] for item in response.json()["data"]]
    assert availability_subject["cohort_id"] not in cohort_ids


def test_get_closed_cohort_detail_still_visible(client, db, availability_subject):
    close_subject_as_live_cohort(db, availability_subject)
    response = client.get(f"/api/v1/cohorts/{availability_subject['cohort_id']}")
    assert response.status_code == 200
    assert response.json()["data"]["cohortId"] == availability_subject["cohort_id"]


def test_get_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
