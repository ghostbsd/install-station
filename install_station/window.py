import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Window:
    window = Gtk.Window()

    @classmethod
    def connect(cls, signal, callback):
        return cls.window.connect(signal, callback)
    
    @classmethod
    def set_border_width(cls, width):
        return cls.window.set_border_width(width)
    
    @classmethod
    def set_default_size(cls, width, height):
        return cls.window.set_default_size(width, height)
    
    @classmethod
    def set_size_request(cls, width, height):
        return cls.window.set_size_request(width, height)
    
    @classmethod
    def set_title(cls, title):
        return cls.window.set_title(title)
    
    @classmethod
    def set_icon_from_file(cls, filename):
        return cls.window.set_icon_from_file(filename)
    
    @classmethod
    def add(cls, widget):
        return cls.window.add(widget)
    
    @classmethod
    def show_all(cls):
        return cls.window.show_all()

    @classmethod
    def hide(cls):
        """Hide the window."""
        return cls.window.hide()
    
    @classmethod
    def __getattr__(cls, name):
        """Fallback for any methods not explicitly defined."""
        return getattr(cls.window, name)
