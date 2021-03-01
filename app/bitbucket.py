from collections import defaultdict
import httpx, asyncio

from .exceptions import APIQueryFailure, UnknownOrganization

HTTPX_AUTH = None

### API ###
async def get_bitbucket_workspace_profile(workspace, timeout=2):
    """
    Gets the profile information available from the workspace `workspace`, with
    a timeout of `timeout` seconds.

    Returns a dict of the profile data.
    """
    async with httpx.AsyncClient() as client:
        data = {"href": f"https://bitbucket.org/{workspace}"}

        # Gather workspace info then repositories
        await asyncio.gather(
            enrich_bitbucket_workspace_info(client, data, workspace, timeout=timeout),
            enrich_bitbucket_repositories(client, data, workspace, timeout=timeout),
        )

        # Merge languages
        if "repositories" in data:
            data["languages"] = merge_bitbucket_languages(data["repositories"])

            await enrich_bitbucket_watchers(
                client, data, data["repositories"], timeout=timeout
            )
        else:
            data["languages"] = {}
            data["followers"] = 0

        # Bitbucket doesn't have topics as near as I can tell
        data["topics"] = {}

    return data


async def enrich_bitbucket_workspace_info(client, data, workspace, timeout=2):
    """
    Updates organization profile information directly into the data dictionary.
    """
    r = await client.get(
        f"https://bitbucket.org/!api/2.0/workspaces/{workspace}",
        timeout=2,
        auth=HTTPX_AUTH,
    )
    if r.status_code == 404:
        raise UnknownOrganization(workspace)
    if r.status_code != httpx.codes.OK:
        raise APIQueryFailure(r.status_code, r.text)

    data.update(r.json())


async def enrich_bitbucket_repositories(client, data, workspace, timeout=2):
    """
    Adds a 'repositories' item to the data dictionary with information about
    the workspaces's repos.
    """
    r = await client.get(
        f"https://bitbucket.org/!api/2.0/repositories/{workspace}/",
        timeout=timeout,
        auth=HTTPX_AUTH,
    )
    if r.status_code == httpx.codes.OK:
        repo_data = r.json()
        data["public_repos"] = repo_data["size"]
        data["repositories"] = repo_data["values"]


async def enrich_bitbucket_watchers(client, data, repos, timeout=2):
    """
    Sums the amount of watchers from each repository.
    """
    requests = [
        client.get(
            r["links"]["watchers"]["href"] + "?pagelen=0",
            timeout=timeout,
            auth=HTTPX_AUTH,
        )
        for r in repos
    ]
    results = await asyncio.gather(*requests)
    data["followers"] = sum(r.json()["size"] for r in results)


def merge_bitbucket_languages(repos):
    """
    Takes a list of repo data, and returns a mapping of:
        Language -> Number of Repos with Language
    """
    results = defaultdict(lambda: 0)
    for r in repos:
        results[r["language"].lower()] += 1
    return results
