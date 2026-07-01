from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def get_return_url(request, fallback_viewname="home"):
    """
    Pop the current page off the history stack and return the previous one.
    Falls back to fallback_viewname if there's no history.
    """
    history = request.session.get("nav_history", [])
    current = request.get_full_path()

    # Remove the current edit/detail page from history so the back
    # target is always the page *before* it
    if history and history[-1] == current:
        history = history[:-1]
        request.session["nav_history"] = history

    if history:
        candidate = history[-1]
        if url_has_allowed_host_and_scheme(
            candidate, allowed_hosts={request.get_host()}
        ):
            return candidate

    return reverse(fallback_viewname)


"""
USE this version once I am convinced the history stack is clean. Until
then, let the original code fail if the stack has invalid entries.

import requests
from django.urls import resolve, Resolver404

def get_return_url(request, fallback_viewname='home'):
    history = request.session.get('nav_history', [])
    current = request.get_full_path()

    if history and history[-1] == current:
        history = history[:-1]
        request.session['nav_history'] = history

    # Walk back through history looking for a resolvable URL
    while history:
        candidate = history[-1]
        if url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
            try:
                resolve(candidate.split('?')[0])  # strip query string before resolving
                return candidate
            except Resolver404:
                history.pop()
                request.session['nav_history'] = history
                continue
        history.pop()

    return reverse(fallback_viewname)
"""
