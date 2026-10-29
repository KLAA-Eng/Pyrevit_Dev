# -*- coding: utf-8 -*-

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#====================================================================================================
from abc import ABCMeta, abstractmethod, abstractproperty
from GUI.forms import my_WPF



# ╔╗ ╔═╗╔═╗╔═╗  ╔═╗╦  ╔═╗╔═╗╔═╗
# ╠╩╗╠═╣╚═╗║╣   ║  ║  ╠═╣╚═╗╚═╗
# ╚═╝╩ ╩╚═╝╚═╝  ╚═╝╩═╝╩ ╩╚═╝╚═╝ BASE CLASS
#====================================================================================================

class BaseRenaming(my_WPF):
    """Shared view-renaming behavior; concrete commands own their window source."""
    @abstractmethod
    def start(self, title, version=None):
        raise NotImplementedError('Concrete rename commands must load their own XAML.')

    # ╔═╗╔╗ ╔═╗╔╦╗╦═╗╔═╗╔═╗╔╦╗
    # ╠═╣╠╩╗╚═╗ ║ ╠╦╝╠═╣║   ║
    # ╩ ╩╚═╝╚═╝ ╩ ╩╚═╩ ╩╚═╝ ╩ ABSTRACT PART
    # ====================================================================================================

    @abstractproperty
    def uidoc(self):
        """docs is passed this way so it will be updated in case user uses the end tool in multiple open projects."""
        pass

    @abstractproperty
    def doc(self):
        """docs is passed this way so it will be updated in case user uses the end tool in multiple open projects."""
        pass

    @abstractproperty
    def element_types(self):
        """Abstract property of a list of types that should be filtered from selection."""
        pass

    @abstractmethod
    def rename_elements(self):
        """This is an abstract method that will be replaced with a function that contains renaming logic for given elements."""
        pass

    def get_selected_elements(self):
        return [self.doc.GetElement(elem_id) for elem_id in self.uidoc.Selection.GetElementIds() if type(self.doc.GetElement(elem_id)) in self.element_types]

    # ╔═╗╦ ╦╦  ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╦╔═╗╔═╗
    # ║ ╦║ ║║  ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ║║╣ ╚═╗
    # ╚═╝╚═╝╩  ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╩╚═╝╚═╝ GUI PROPERTIES
    # ====================================================================================================

    @property
    def find(self):
        return self.input_find.Text

    @property
    def replace(self):
        return self.input_replace.Text

    @property
    def prefix(self):
        return self.input_prefix.Text

    @property
    def suffix(self):
        return self.input_suffix.Text

    # ╔═╗╦ ╦╦  ╔═╗╦  ╦╔═╗╔╗╔╔╦╗╔═╗
    # ║ ╦║ ║║  ║╣ ╚╗╔╝║╣ ║║║ ║ ╚═╗
    # ╚═╝╚═╝╩  ╚═╝ ╚╝ ╚═╝╝╚╝ ╩ ╚═╝ GUI EVENTS (BUTTONS)
    # ====================================================================================================
    def button_run(self, sender, e):
        """Button action: Rename view with given """
        self.rename_elements()
