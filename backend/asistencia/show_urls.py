from django.urls import get_resolver

def show_urls():
    urls = get_resolver().url_patterns
    for url in urls:
        print(url)

show_urls()