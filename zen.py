import importlib
import string
import random
from django.core.management import execute_from_command_line
from django.db import connection, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import path, re_path
from settings import BASE_DIR

CREATE_URLS_TABLE = '''
CREATE TABLE IF NOT EXISTS urls (
url_key CHAR(5) PRIMARY KEY,
url TEXT
);
'''
INSERT_INTO_URLS = '''
INSERT INTO urls (url_key, url)
VALUES (%s, %s);
'''

SELECT_FROM_URLS = '''
SELECT url
FROM urls
WHERE url_key = %s;
'''


def create_table(create_query):
    with connection.cursor() as c:
        c.execute(create_query)


def get_favicon(request):
    image_data = open(BASE_DIR / "favicon.png", "rb").read()
    return HttpResponse(image_data)


def generate_random_key(length):
    if length > 0:
        letters = string.ascii_letters
        digits = string.digits
        random_key = ''.join(random.choice(letters + digits) for i in range(length))
        return random_key


def get_homepage(request):
    context = {}
    if request.method == 'POST':
        context['is_post_method'] = True
        url = request.POST['url']
        context['url'] = url
        is_url_valid = url.lower().startswith(('http:', 'https:', 'ftp:'))
        if is_url_valid:
            context['is_valid'] = is_url_valid
            while True:
                url_key = generate_random_key(5)
                with connection.cursor() as c:
                    try:
                        c.execute(INSERT_INTO_URLS, (url_key, url))
                        break
                    except IntegrityError as e:
                        if 'unique constraint' in e.args[0].lower():
                            print(f"Short-key {url_key} already exists in the db. Generating the new one.")
            context['url_key'] = url_key
    return render(request, 'homepage.html', context)


def perform_redirect(request, url_key):
    with connection.cursor() as c:
        c.execute(SELECT_FROM_URLS, [url_key])
        row = c.fetchone()
        url = row[0] if row else '/'
        return redirect(url)


def get_mod_page(request, mod_name):
    try:
        module = importlib.import_module(mod_name)
    except ModuleNotFoundError:
        return HttpResponse(f"No module named '{mod_name}'", status=404)
    attributes = [func for func in dir(module) if not func.startswith('_')]
    context = {'title': mod_name, 'mod': mod_name, 'attributes': attributes}
    return render(request, 'modpage.html', context)


def get_att_page(request, mod_name, att_name):
    try:
        module = importlib.import_module(mod_name)
    except ModuleNotFoundError:
        return HttpResponse(f"No module named '{mod_name}'", status=404)
    attribute = getattr(module, att_name, None)
    if attribute is None:
        return HttpResponse(f"Module '{mod_name}' has no attribute '{att_name}'", status=404)
    return HttpResponse(attribute.__doc__, content_type='text/plain')


urlpatterns = [
    path('', get_homepage),
    path('<url_key>', perform_redirect),
    re_path(r'^favicon\.ico$', get_favicon),
    path('doc/<mod_name>', get_mod_page),
    path('doc/<mod_name>/<att_name>', get_att_page),
]

create_table(CREATE_URLS_TABLE)

if __name__ == '__main__':
    execute_from_command_line()
