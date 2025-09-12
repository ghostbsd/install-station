import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os
from install_station.system_calls import (
    keyboard_dictionary,
    keyboard_models,
    change_keyboard,
    set_keyboard
)
from install_station.data import InstallationData, tmp, get_text

# Ensure temp directory exists
if not os.path.exists(tmp):
    os.makedirs(tmp)

layout = f'{tmp}layout'
variant = f'{tmp}variant'
KBFile = f'{tmp}keyboard'

kb_dictionary = keyboard_dictionary()
kbm_dictionary = keyboard_models()

cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/local/lib/install-station/ghostbsd-style.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(
    screen,
    cssProvider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


class PlaceHolderEntry(Gtk.Entry):
    """
    GTK Entry widget with placeholder text functionality.
    
    This class extends Gtk.Entry to provide placeholder text that disappears
    when the widget gains focus and returns when focus is lost if empty.
    """

    def __init__(self, *args, **kwds) -> None:
        Gtk.Entry.__init__(self, *args, **kwds)
        self.placeholder = get_text('Type here to test your keyboard')
        self.set_text(self.placeholder)
        self._default = True
        self.connect('focus-in-event', self._focus_in_event)
        self.connect('focus-out-event', self._focus_out_event)

    def _focus_in_event(self, _widget: Gtk.Widget, _event) -> None:
        if self._default:
            self.set_text('')

    def _focus_out_event(self, _widget: Gtk.Widget, _event) -> None:
        if Gtk.Entry.get_text(self) == '':
            self.set_text(self.placeholder)
            self._default = True
        else:
            self._default = False

    def get_text(self) -> str:
        if self._default:
            return ''
        return Gtk.Entry.get_text(self)


class Keyboard:
    """
    Utility class for the keyboard configuration screen following the utility class pattern.
    
    This class provides a GTK+ interface for keyboard layout and model selection including:
    - Keyboard layout selection from available system layouts
    - Keyboard model selection from available models
    - Real-time keyboard testing with preview text entry
    - Integration with InstallationData for persistent configuration
    
    The class follows a utility pattern with class methods and variables for state management,
    designed to integrate with the Interface controller for navigation flow.
    """
    # Class variables instead of instance variables
    kb_layout: str | None = None
    kb_variant: str | None = None
    kb_model: str | None = None
    vbox1: Gtk.Box | None = None
    treeView: Gtk.TreeView | None = None
    test_entry: PlaceHolderEntry | None = None

    @classmethod
    def layout_columns(cls, treeview: Gtk.TreeView) -> None:
        """
        Configure the keyboard layout treeview with appropriate columns.
        
        Creates a single column with a "Keyboard Layout" header for displaying
        available keyboard layouts in the tree view.
        
        Args:
            treeview: TreeView widget to configure with layout column
        """
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        column_header = Gtk.Label(label=f'<b>{get_text("Keyboard Layout")}</b>')
        column_header.set_use_markup(True)
        column_header.show()
        column.set_widget(column_header)
        column.set_sort_column_id(0)
        treeview.append_column(column)

    @classmethod
    def variant_columns(cls, treeview: Gtk.TreeView) -> None:
        """
        Configure the keyboard model treeview with appropriate columns.
        
        Creates a single column with a "Keyboard Models" header for displaying
        available keyboard models in the tree view.
        
        Args:
            treeview: TreeView widget to configure with model column
        """
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        column_header = Gtk.Label(label=f'<b>{get_text("Keyboard Models")}</b>')
        column_header.set_use_markup(True)
        column_header.show()
        column.set_widget(column_header)
        column.set_sort_column_id(0)
        treeview.append_column(column)

    @classmethod
    def layout_selection(cls, tree_selection: Gtk.TreeSelection) -> None:
        """
        Handle keyboard layout selection from the treeview.
        
        Extracts the selected layout from the tree view and updates both
        class variables and InstallationData with the layout information.
        Also applies the keyboard layout change immediately for testing.
        
        Args:
            tree_selection: TreeSelection widget containing the user's layout choice
        """
        model, treeiter = tree_selection.get_selected()
        if treeiter is not None:
            value = model[treeiter][0]
            kb_lv = kb_dictionary[value]
            cls.kb_layout = kb_lv['layout']
            cls.kb_variant = kb_lv['variant']
            # Save to InstallationData
            InstallationData.keyboard_layout = value
            InstallationData.keyboard_layout_code = cls.kb_layout
            InstallationData.keyboard_variant = cls.kb_variant
            change_keyboard(cls.kb_layout, cls.kb_variant)
            print(f"Keyboard layout selected: {value} ({cls.kb_layout}/{cls.kb_variant})")

    @classmethod
    def model_selection(cls, tree_selection: Gtk.TreeSelection) -> None:
        """
        Handle keyboard model selection from the treeview.
        
        Extracts the selected model from the tree view and updates both
        class variables and InstallationData with the model information.
        Also applies the keyboard model change immediately for testing.
        
        Args:
            tree_selection: TreeSelection widget containing the user's model choice
        """
        model, treeiter = tree_selection.get_selected()
        if treeiter is not None:
            value = model[treeiter][0]
            cls.kb_model = kbm_dictionary[value]
            # Save to InstallationData
            InstallationData.keyboard_model = value
            InstallationData.keyboard_model_code = cls.kb_model
            if cls.kb_layout and cls.kb_variant:
                change_keyboard(cls.kb_layout, cls.kb_variant, cls.kb_model)
            print(f"Keyboard model selected: {value} ({cls.kb_model})")

    @classmethod
    def save_selection(cls) -> None:
        """
        Save the current keyboard selection.
        
        This method saves keyboard configuration to both InstallationData 
        (for the installer) and temporary files (for compatibility).
        """
        # Data is now saved in InstallationData automatically
        # Keep file writing for compatibility
        if cls.kb_layout and cls.kb_variant and cls.kb_model:
            with open(KBFile, 'w') as file:
                file.write(f"{cls.kb_layout}\\n")
                file.write(f"{cls.kb_variant}\\n")
                file.write(f"{cls.kb_model}\\n")

    @classmethod
    def save_keyboard(cls) -> None:
        """
        Apply the keyboard configuration to the system.
        
        This method applies the selected keyboard layout, variant, and model
        to the current system for immediate use.
        """
        if cls.kb_layout and cls.kb_variant and cls.kb_model:
            set_keyboard(cls.kb_layout, cls.kb_variant, cls.kb_model)

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the keyboard configuration UI following the utility class pattern.
        
        Creates the main interface including:
        - Keyboard layout selection tree view on the left side
        - Keyboard model selection tree view on the right side  
        - Test entry field at the bottom for keyboard testing
        - Grid-based layout with proper spacing and margins
        
        This method is called automatically by get_model() when the interface is first accessed.
        """
        cls.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=0)
        cls.vbox1.show()
        
        main_grid = Gtk.Grid()
        cls.vbox1.pack_start(main_grid, True, True, 0)
        
        # Create two scrolled windows side by side for layout and model selection
        # Left side - Keyboard layouts
        sw_layouts = Gtk.ScrolledWindow()
        sw_layouts.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw_layouts.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        layout_store = Gtk.TreeStore(str)
        layout_store.append(None, [get_text('English (US)')])
        layout_store.append(None, [get_text('English (Canada)')])
        layout_store.append(None, [get_text('French (Canada)')])
        for line in sorted(kb_dictionary):
            layout_store.append(None, [line.rstrip()])
            
        cls.treeView = Gtk.TreeView()
        cls.treeView.set_model(layout_store)
        cls.treeView.set_rules_hint(True)
        cls.layout_columns(cls.treeView)
        layout_selection = cls.treeView.get_selection()
        layout_selection.set_mode(Gtk.SelectionMode.SINGLE)
        layout_selection.connect("changed", cls.layout_selection)
        sw_layouts.add(cls.treeView)
        sw_layouts.show()
        
        # Right side - Keyboard models
        sw_models = Gtk.ScrolledWindow()
        sw_models.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw_models.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        model_store = Gtk.TreeStore(str)
        for line in sorted(kbm_dictionary):
            model_store.append(None, [line.rstrip()])
            
        model_treeview = Gtk.TreeView()
        model_treeview.set_model(model_store)
        model_treeview.set_rules_hint(True)
        cls.variant_columns(model_treeview)
        model_selection = model_treeview.get_selection()
        model_selection.set_mode(Gtk.SelectionMode.SINGLE)
        model_selection.connect("changed", cls.model_selection)
        sw_models.add(model_treeview)
        sw_models.show()
        
        # Bottom - Test entry
        cls.test_entry = PlaceHolderEntry()
        
        # Layout everything in grid
        main_grid.set_row_spacing(5)
        main_grid.set_column_spacing(10)
        main_grid.set_column_homogeneous(True)
        main_grid.set_row_homogeneous(True)
        main_grid.set_margin_left(10)
        main_grid.set_margin_right(10)
        main_grid.set_margin_top(10)
        main_grid.set_margin_bottom(10)
        
        main_grid.attach(sw_layouts, 0, 0, 1, 8)
        main_grid.attach(sw_models, 1, 0, 1, 8)
        main_grid.attach(cls.test_entry, 0, 9, 2, 1)
        main_grid.show()
        # Set default selection
        cls.treeView.set_cursor(0)

    @classmethod
    def get_model(cls) -> Gtk.Box:
        """
        Return the GTK widget model for the keyboard configuration interface.
        
        Returns the main container widget that was created during initialization.
        
        Returns:
            Gtk.Box: The main container widget for the keyboard configuration interface
        """
        if cls.vbox1 is None:
            cls.initialize()
        return cls.vbox1

    @classmethod
    def get_keyboard_info(cls) -> dict[str, str | None]:
        """
        Get the current keyboard configuration information.
        
        Returns:
            dict: Dictionary containing keyboard layout, variant, and model information
        """
        return {
            'layout': InstallationData.keyboard_layout or cls.kb_layout,
            'layout_code': InstallationData.keyboard_layout_code or cls.kb_layout,
            'variant': InstallationData.keyboard_variant or cls.kb_variant,
            'model': InstallationData.keyboard_model or cls.kb_model,
            'model_code': InstallationData.keyboard_model_code or cls.kb_model
        }
