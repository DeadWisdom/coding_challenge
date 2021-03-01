import pytest


def test_health_check(client):
    """
    Requesting the health check url should return 'All good!'
    """
    _, r = client.get("/health-check")
    assert "All Good!" in r.text


def test_github_profile(client):
    """
    The mailchimp url should return a profile with specific information.
    """
    _, r = client.get("/github/mailchimp")
    data = r.json

    assert data["name"] == "Mailchimp"
    assert data["public_repos"] > 0
    assert data["followers"] > 0
    assert "kotlin" in set(data["languages"])
    assert "email-marketing" in set(data["topics"])


def test_github_missing(client):
    """
    If the org is not on github, return a 404
    """
    _, r = client.get("/github/random-hash-e513ad1be5be8aec5887f151e3b3f7b8")
    assert r.status_code == 404


def test_bitbucket_profile(client):
    """
    The bitbucket mailchimp url should return a profile with specific information.
    """
    _, r = client.get("/bitbucket/mailchimp")
    data = r.json

    assert data["name"] == "Frederick Von Chimpenheimer IV"  # Cool name
    assert data["public_repos"] > 0
    assert data["followers"] > 0
    assert "dart" in set(data["languages"])
    assert not data["topics"]


def test_bitbucket_missing(client):
    """
    If the workspace is not on bitbucket, return a 404
    """
    _, r = client.get("/bitbucket/random-hash-e513ad1be5be8aec5887f151e3b3f7b8")
    assert r.status_code == 404


def test_merged(client):
    """
    If the org is not on github, return a 404
    """
    _, r = client.get("/merged-profiles?github=mailchimp&bitbucket=mailchimp")
    data = r.json

    bitbucket = data["bitbucket"]
    assert bitbucket["name"] == "Frederick Von Chimpenheimer IV"  # Cool name
    assert bitbucket["public_repos"] > 0
    assert bitbucket["followers"] > 0
    assert "dart" in set(bitbucket["languages"])
    assert not bitbucket["topics"]

    github = data["github"]
    assert github["name"] == "Mailchimp"
    assert github["public_repos"] > 0
    assert github["followers"] > 0
    assert "kotlin" in set(github["languages"])
    assert "email-marketing" in set(github["topics"])

    merged = data["__merged__"]
    assert merged["public_repos"] == bitbucket["public_repos"] + github["public_repos"]
    assert merged["followers"] == bitbucket["followers"] + github["followers"]
    assert set(merged["languages"]) == set(github["languages"]) | set(
        bitbucket["languages"]
    )
    assert merged["topics"] == github["topics"]
