from flask import request, url_for


def page_url(page: int) -> str:
    args = request.args.to_dict(flat=True)
    args["page"] = page
    return url_for(request.endpoint, **args)
