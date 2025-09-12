"""
Window Module.

This module provides a singleton wrapper around GTK Window to provide
a consistent interface for the main application window.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Window:
    """
    Singleton wrapper for GTK Window.
    
    Provides a class-based interface to a single GTK Window instance
    that can be accessed throughout the application.
    """
    window: Gtk.Window = Gtk.Window()

    @classmethod
    def connect(cls, signal: str, callback) -> int:
        """Connect a signal handler to the window.
        
        Args:
            signal: Signal name to connect to
            callback: Callback function to invoke
            
        Returns:
            Connection ID
        """
        return cls.window.connect(signal, callback)
    
    @classmethod
    def set_border_width(cls, width: int) -> None:
        """Set the border width of the window.
        
        Args:
            width: Border width in pixels
        """
        return cls.window.set_border_width(width)
    
    @classmethod
    def set_default_size(cls, width: int, height: int) -> None:
        """Set the default size of the window.
        
        Args:
            width: Default width in pixels
            height: Default height in pixels
        """
        return cls.window.set_default_size(width, height)
    
    @classmethod
    def set_size_request(cls, width: int, height: int) -> None:
        """Set the size request of the window.
        
        Args:
            width: Requested width in pixels
            height: Requested height in pixels
        """
        return cls.window.set_size_request(width, height)
    
    @classmethod
    def set_title(cls, title: str) -> None:
        """Set the window title.
        
        Args:
            title: Window title text
        """
        return cls.window.set_title(title)
    
    @classmethod
    def set_icon_from_file(cls, filename: str) -> None:
        """Set the window icon from a file.
        
        Args:
            filename: Path to icon file
        """
        return cls.window.set_icon_from_file(filename)
    
    @classmethod
    def add(cls, widget: Gtk.Widget) -> None:
        """Add a widget to the window.
        
        Args:
            widget: Widget to add to the window
        """
        return cls.window.add(widget)
    
    @classmethod
    def show_all(cls) -> None:
        """Show the window and all its children."""
        return cls.window.show_all()

    @classmethod
    def hide(cls) -> None:
        """Hide the window."""
        return cls.window.hide()
    
    @classmethod
    def __getattr__(cls, name: str):
        """Fallback for any methods not explicitly defined."""
        return getattr(cls.window, name)
