import logging, asyncio
from sanic import Sanic, response
from sanic.log import logger
from sanic.exceptions import abort

from .github import get_github_org_profile, APIQueryFailure, UnknownOrganization
from .bitbucket import get_bitbucket_workspace_profile

REPO_PROFILE_MIMETYPE = "application/vnd+divvydose.repo-profile+json"
REPO_PROFILE_MERGED_MIMETYPE = "application/vnd+divvydose.repo-profile-merged+json"

app = Sanic("repo_profiles_api")
logger.setLevel(logging.INFO)


### Supporting Functions ###
def slim_profile(profile_data):
    """
    Returns only the profile_data we care about.
    """
    return {
        "href": profile_data["href"],
        "name": profile_data["name"],
        "public_repos": profile_data["public_repos"],
        "followers": profile_data["followers"],
        "languages": profile_data.get("languages") or {},
        "topics": profile_data.get("topics") or {},
    }


def merge_profiles(a, b):
    if not b:
        return dict(a)
    if not a:
        return dict(b)
    return {
        "public_repos": a["public_repos"] + b["public_repos"],
        "followers": a["followers"] + b["followers"],
        "languages": merge_frequency_maps(a["languages"], b["languages"]),
        "topics": merge_frequency_maps(a["topics"], b["topics"]),
    }


def merge_frequency_maps(a, b):
    return {k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)}


### Routes ###
@app.route("/health-check", methods=["GET"])
def health_check(request):
    """
    Endpoint to health check API
    """
    logger.info("Health Check!")
    return response.text("All Good!")


@app.route("/github/<org>", methods=["GET"])
async def github(request, org):
    """
    Get information about a github organization.

    You may optionally
    """
    try:
        profile = await get_github_org_profile(org)
    except UnknownOrganization as e:
        abort(404, str(e))
    except APIQueryFailure as e:
        abort(500, str(e))
    if not request.args.get("extended"):
        profile = slim_profile(profile)
    return response.json(
        profile,
        headers={"Content-Type": REPO_PROFILE_MIMETYPE},
        escape_forward_slashes=False,
    )


@app.route("/bitbucket/<workspace>", methods=["GET"])
async def bitbucket(request, workspace):
    """
    Get information about a bitbucket workspace
    """
    try:
        profile = await get_bitbucket_workspace_profile(workspace)
    except UnknownOrganization as e:
        abort(404, str(e))
    except APIQueryFailure as e:
        abort(500, str(e))
    if not request.args.get("extended"):
        profile = slim_profile(profile)
    return response.json(
        profile,
        headers={"Content-Type": REPO_PROFILE_MIMETYPE},
        escape_forward_slashes=False,
    )


@app.route("/merged-profiles", methods=["GET"])
async def get_merged_profiles(request):
    """
    Gets the profiles requested
    """
    data = {}
    errors = {}
    queries = {
        "bitbucket": get_bitbucket_workspace_profile,
        "github": get_github_org_profile,
    }

    # Find queried items from query string args:
    query_keys = [k for k in queries.keys() if k in request.args]
    if not query_keys:
        abort(400, f"missing query string parameters: {sorted(list(queries.keys()))}")

    # Get the coroutines we will need based on the args given
    coroutines = [queries[k](request.args.get(k)) for k in query_keys]

    # Get our results, exceptions will be returned as the result of the async function
    results = await asyncio.gather(*coroutines, return_exceptions=True)

    # Put them into a map: key -> result
    results = dict(zip(query_keys, results))

    # Here we will store our merged results
    merged = {}

    # Grab the results
    for key, result in results.items():
        if isinstance(result, UnknownOrganization):
            abort(404, f"No entry for {key} service: {request.args.get(key)!r}")
        if isinstance(result, APIQueryFailure):
            data[key] = None
            errors[key] = {"status_code": result.status_code, "message": str(result)}
        else:
            result = slim_profile(result)
            data[key] = result
            merged = merge_profiles(merged, result)

    if errors:
        data["__errors__"] = errors

    data["__merged__"] = merged

    return response.json(
        data,
        headers={"Content-Type": REPO_PROFILE_MERGED_MIMETYPE},
        escape_forward_slashes=False,
    )
