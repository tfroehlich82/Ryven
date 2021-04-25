from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QRadioButton, QLabel, QCheckBox, QGridLayout, \
    QPushButton
import inspect

import ryvencore_qt as rc

from .EditSrcCodeInfoDialog import EditSrcCodeInfoDialog
from .CodeEditorWidget import CodeEditorWidget
from .SourceCodeUpdater import SrcCodeUpdater


class CodePreviewWidget(QWidget):
    def __init__(self, main_window, flow):
        super(CodePreviewWidget, self).__init__()

        flow.nodes_selection_changed.connect(self.set_selected_nodes)

        self.text_edit = CodeEditorWidget(main_window.theme)

        self.node = None
        self.buttons_obj_dict = {}
        self.active_class_index = -1
        self.edited_codes = {}


        secondary_layout = QHBoxLayout()


        # class radio buttons widget
        self.class_selection_layout = QGridLayout()

        secondary_layout.addLayout(self.class_selection_layout)
        self.class_selection_layout.setAlignment(Qt.AlignLeft)
        # secondary_layout.setAlignment(self.class_selection_layout, Qt.AlignLeft)


        # edit source code buttons
        # self.highlight_code_button = QPushButton('HL')
        # self.highlight_code_button.setEnabled(False)
        # self.highlight_code_button.clicked.connect(self.highlight_code_button_clicked)
        self.edit_code_button = QPushButton('edit')
        self.edit_code_button.setMaximumWidth(100)
        self.edit_code_button.clicked.connect(self.edit_code_button_clicked)
        self.override_code_button = QPushButton('override')
        self.override_code_button.setMaximumWidth(100)
        self.override_code_button.setEnabled(False)
        self.override_code_button.clicked.connect(self.override_code_button_clicked)
        self.reset_code_button = QPushButton('reset')
        self.reset_code_button.setMaximumWidth(206)
        self.reset_code_button.setEnabled(False)
        self.reset_code_button.clicked.connect(self.reset_code_button_clicked)

        edit_buttons_layout = QHBoxLayout()
        # edit_buttons_layout.addWidget(self.highlight_code_button)
        edit_buttons_layout.addWidget(self.edit_code_button)
        edit_buttons_layout.addWidget(self.override_code_button)
        edit_buttons_layout.addWidget(self.reset_code_button)
        # edit_buttons_layout.addWidget(self.highlight_code_button)

        secondary_layout.addLayout(edit_buttons_layout)
        edit_buttons_layout.setAlignment(Qt.AlignRight)

        main_layout = QVBoxLayout()
        main_layout.addLayout(secondary_layout)
        main_layout.addWidget(self.text_edit)
        self.setLayout(main_layout)

        self.set_node(None)

    def set_selected_nodes(self, nodes):
        if len(nodes) == 0:
            self.set_node(None)
        else:
            self.set_node(nodes[-1])

    def set_node(self, node):
        self.disable_editing()

        self.rebuild_class_selection(node)
        self.update_edit_status()

        self.node = node

        if node is None:  # no node selected
            self.text_edit.set_code('')
            self.edit_code_button.setEnabled(False)
            self.override_code_button.setEnabled(False)
            self.reset_code_button.setEnabled(False)
            # self.highlight_code_button.setEnabled(False)
            return
        self.edit_code_button.setEnabled(True)
        # self.highlight_code_button.setEnabled(True)

        self.update_code()

    def update_code(self):

        self.disable_editing()

        if self.active_class_index == -1 or self.node is None:
            return

        if self.get_current_code_obj() not in self.edited_codes:
            self.text_edit.disable_highlighting()
            self.text_edit.set_code(inspect.getsource(self.get_current_code_class()))
            self.reset_code_button.setEnabled(False)
        else:
            self.text_edit.disable_highlighting()
            self.text_edit.set_code(self.edited_codes[self.get_current_code_obj()])
            self.reset_code_button.setEnabled(True)

    def get_current_code_class(self):
        return self.get_current_code_obj().__class__

    def get_current_code_obj(self):
        return list(self.buttons_obj_dict.values())[self.active_class_index]

    def rebuild_class_selection(self, obj):
        # clear layout
        for i in range(self.class_selection_layout.count()):
            item = self.class_selection_layout.itemAt(0)
            widget = item.widget()
            widget.hide()
            self.class_selection_layout.removeItem(item)

        self.buttons_obj_dict = {}
        self.active_class_index = -1

        if isinstance(obj, rc.Node):
            # NI class
            node_class_RB = QRadioButton('Node')
            node_class_RB.toggled.connect(self.class_RB_toggled)
            self.buttons_obj_dict[node_class_RB] = obj
            self.class_selection_layout.addWidget(node_class_RB, 0, 0)

            # main_widget class
            if obj.item.main_widget is not None:
                main_widget_class_RB = QRadioButton('MainWidget')
                main_widget_class_RB.toggled.connect(self.class_RB_toggled)
                self.buttons_obj_dict[main_widget_class_RB] = obj.item.main_widget
                self.class_selection_layout.addWidget(main_widget_class_RB, 1, 0)

            # data input widgets
            count = 0
            for i in range(len(obj.inputs)):
                inp_widget = obj.input_widget(i)

                if inp_widget:
                    inp_widget_class_RB = QRadioButton('Input '+str(i))
                    inp_widget_class_RB.toggled.connect(self.class_RB_toggled)
                    self.buttons_obj_dict[inp_widget_class_RB] = inp_widget
                    self.class_selection_layout.addWidget(inp_widget_class_RB, 0, 1+count)
                    count += 1

            node_class_RB.setChecked(True)

    def update_edit_status(self):
        for o in list(self.buttons_obj_dict.keys()):
            if self.edited_codes.keys().__contains__(self.buttons_obj_dict[o]):
                # o.setStyleSheet('color: #3B9CD9;')
                f = o.font()
                f.setBold(True)
                o.setFont(f)
            else:
                # o.setStyleSheet('color: white;')
                f = o.font()
                f.setBold(False)
                o.setFont(f)

    def class_RB_toggled(self, checked):
        if checked:
            self.active_class_index = list(self.buttons_obj_dict.keys()).index(self.sender())
            self.update_code()

    def edit_code_button_clicked(self):
        if not EditSrcCodeInfoDialog.dont_show_again:
            info_dialog = EditSrcCodeInfoDialog(self)
            accepted = info_dialog.exec_()
            if not accepted:
                return
        self.enable_editing()

    def enable_editing(self):
        self.text_edit.enable_editing()
        self.override_code_button.setEnabled(True)

    def disable_editing(self):
        self.text_edit.disable_editing()
        self.override_code_button.setEnabled(False)

    def override_code_button_clicked(self):
        new_code = self.text_edit.get_code()
        SrcCodeUpdater.override_code(self.get_current_code_obj(), new_code)
        self.disable_editing()

        self.edited_codes[self.get_current_code_obj()] = new_code
        self.reset_code_button.setEnabled(True)
        self.update_edit_status()

    def reset_code_button_clicked(self):
        code = inspect.getsource(self.get_current_code_class())
        SrcCodeUpdater.override_code(self.get_current_code_obj(), code)
        del self.edited_codes[self.get_current_code_obj()]
        self.update_code()
        self.update_edit_status()

    # def highlight_code_button_clicked(self):
    #     self.text_edit.highlight_now()