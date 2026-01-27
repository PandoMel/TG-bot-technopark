"""Пакет routers - содержит все обработчики"""
from . import user
from . import admin
from . import events

__all__ = ['user', 'admin', 'events']
