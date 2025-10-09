def build_utm_url(base_url: str, utm_source: str, utm_medium: str, utm_campaign: str) -> str:
    """
    Формирует ссылку с добавленными UTM-параметрами.
    Если в базовой ссылке уже есть параметры, добавляет новые через '&'.
    """
    separator = '&' if '?' in base_url else '?'
    # Избежать двойного разделителя, если ссылка уже заканчивается на '?' или '&'
    if base_url.endswith('?') or base_url.endswith('&'):
        separator = ''
    utm_params = f"utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"
    return f"{base_url}{separator}{utm_params}"