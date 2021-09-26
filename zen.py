import importlib
import this
from django.core.management import execute_from_command_line
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path, re_path
from random import choice
from pathlib import Path
from settings import BASE_DIR

text = ''.join(this.d.get(c, c) for c in this.s)
title, _, *quotes = text.splitlines()


def get_favicon(request):
    image_data = open(BASE_DIR/"favicon.png", "rb").read()
    return HttpResponse(image_data)


def get_module(mod_name):
    try:
        module = importlib.import_module(mod_name)
    except ModuleNotFoundError:
        return
    return module


def get_attribute(module, att_name):
    try:
        attribute = getattr(module, att_name)
    except AttributeError:
        return
    return attribute

def get_homepage(request):
    context = {'title': title, 'message': choice(quotes)}
    return render(request, 'homepage.html', context)

def get_mod_page(request, mod_name):
    module = get_module(mod_name)
    if module is None:
        return HttpResponse(f"No module named '{mod_name}'", status=404)
    attributes = [func for func in dir(module) if not func.startswith('_')]
    context = {'title': mod_name, 'mod': mod_name, 'attributes': attributes}
    return render(request, 'modpage.html', context)


def get_att_page(request, mod_name, att_name):
    module = get_module(mod_name)
    if module is None:
        return HttpResponse(f"No module named '{mod_name}'", status=404)
    attribute = get_attribute(module, att_name)
    if attribute is None:
        return HttpResponse(f"Module '{mod_name}' has no attribute '{att_name}'", status=404)
    return HttpResponse(attribute.__doc__, content_type='text/plain')


urlpatterns = [
    path('', get_homepage),
    re_path(r'^favicon\.ico$', get_favicon),
    path('doc/<mod_name>', get_mod_page),
    path('doc/<mod_name>/<att_name>', get_att_page),
]

if __name__ == '__main__':
    execute_from_command_line()
