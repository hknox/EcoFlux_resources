EXCLUDED_PATHS = {"/login/", "/logout/", "/admin/", "/media/", "/favicon.ico"}
AJAX_PATH_SEGMENTS = ("doi", "history")


class NavigationHistoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_track(request):
            history = request.session.get("nav_history", [])
            current = request.get_full_path()
            if not history or history[-1] != current:
                history.append(current)
                history = history[-20:]
            request.session["nav_history"] = history

        return self.get_response(request)

    def _should_track(self, request):
        if request.method != "GET":
            return False
        path_parts = set(request.path.strip("/").split("/"))
        if path_parts & set(AJAX_PATH_SEGMENTS):
            return False
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return False
        if any(request.path.startswith(p) for p in EXCLUDED_PATHS):
            return False

        return True
