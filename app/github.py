from collections import defaultdict
import httpx, asyncio

from .exceptions import APIQueryFailure, UnknownOrganization

HTTPX_AUTH = None  # ("username", "token")


### API ###
async def get_github_org_profile(org, timeout=2):
    """
    Gets the profile information available from the organization `org`, with a
    timeout of `timeout` seconds.

    Returns a dict of the profile data.
    """
    async with httpx.AsyncClient() as client:
        data = {"href": f"https://github.com/{org}"}

        # Gather org info then repositories
        await asyncio.gather(
            enrich_github_org_information(client, data, org, timeout=timeout),
            enrich_github_repositories(client, data, org, timeout=timeout),
        )

        # Enrich the data with the languages found in the repos
        if "repositories" in data:
            await enrich_github_languages(
                client,
                data,
                [repo["languages_url"] for repo in data["repositories"]],
                timeout=timeout,
            )

            # Merge followers / watchers
            data["followers"] = merge_github_watchers(data["repositories"])

            # Merge topics
            data["topics"] = merge_github_topics(data["repositories"])

    return data


async def enrich_github_org_information(client, data, org, timeout=2):
    """
    Updates organization profile information directly into the data dictionary.
    """
    r = await client.get(
        f"https://api.github.com/orgs/{org}", timeout=2, auth=HTTPX_AUTH
    )
    if r.status_code == 404:
        raise UnknownOrganization(org)
    if r.status_code != httpx.codes.OK:
        raise APIQueryFailure(r.status_code, r.text)

    data.update(r.json())


async def enrich_github_repositories(client, data, org, timeout=2):
    """
    Adds a 'repositories' item to the data dictionary with information about
    the org's repos.
    """
    # Ask for the repos, specifically we are asking for a mercy-preview datatype
    # here to get topic information. Github abuses mimetypes for api versioning
    # and feature branching, this disappoints me.
    r = await client.get(
        f"https://api.github.com/orgs/{org}/repos",
        timeout=timeout,
        auth=HTTPX_AUTH,
        headers={"Accept": "application/vnd.github.mercy-preview+json"},
    )
    if r.status_code == httpx.codes.OK:
        data["repositories"] = r.json()


async def enrich_github_languages(client, data, urls, timeout=2):
    """
    Merges all the language information for each language url in the given `urls`

    Adds 'languages': mapping of Language Name -> # of Repos Using
    Adds 'language_locs': mapping of Language Name -> Lines of Code
    """
    language_locs = defaultdict(lambda: 0)  # Language Name -> Lines of Code
    language_count = defaultdict(lambda: 0)  # Language Name -> # of Repos Using
    requests = (client.get(url, timeout=timeout, auth=HTTPX_AUTH) for url in urls)
    responses = await asyncio.gather(*requests)
    for r in responses:
        if r.status_code != httpx.codes.OK:
            continue
        langs = r.json()
        for name, lines in langs.items():
            language_locs[name.lower()] += lines
            language_count[name.lower()] += 1
    data["language_locs"] = language_locs
    data["languages"] = language_count


def merge_github_topics(repos):
    """
    Takes a list of github repositories and provides a final count of topics as
    a mapping: Topic -> Count
    """
    results = defaultdict(lambda: 0)
    for r in repos:
        for topic in r["topics"]:
            results[topic] += 1
    return results


def merge_github_watchers(repos):
    """
    Just sum all the watchers of all the given list of `repos`
    """
    return sum(r["watchers"] for r in repos)
