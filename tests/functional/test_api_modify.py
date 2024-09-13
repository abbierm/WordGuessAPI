"""
This file (test_api_modify.py) tests the api routes that allow users to POST
changes to their account or Solver.
"""


def test_api_create_solve_id(test_client, api_lookups, get_lookup_token):
    """
    GIVEN a configured Flask app, a valid user with loaded data and a
        current user's api token,
    WHEN the api/create_solver_id/solver52 (POST) call is requested,
    THEN check if solver52 has an api id
    """
    auth = {'Authorization': f"Bearer {get_lookup_token}"}
    response = test_client.post(
        path='api/create_solver_id/solver52',
        headers=auth
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["solver_id"] is not None