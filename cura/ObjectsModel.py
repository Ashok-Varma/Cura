from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Preferences import Preferences
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


##  Keep track of all objects in the project
class ObjectsModel(ListModel):
    def __init__(self):
        super().__init__()

        Application.getInstance().getController().getScene().sceneChanged.connect(self._update)
        Preferences.getInstance().preferenceChanged.connect(self._update)

        self._build_plate_number = -1

        self._stacks_have_errors = None  # type:Optional[bool]

    def setActiveBuildPlate(self, nr):
        self._build_plate_number = nr
        self._update()

    def _update(self, *args):
        nodes = []
        filter_current_build_plate = Preferences.getInstance().getValue("view/filter_current_build_plate")
        active_build_plate_number = self._build_plate_number
        group_nr = 1
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if not isinstance(node, SceneNode):
                continue
            if (not node.getMeshData() and not node.callDecoration("getLayerData")) and not node.callDecoration("isGroup"):
                continue
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
            if not node.callDecoration("isSliceable") and not node.callDecoration("isGroup"):
                continue
            node_build_plate_number = node.callDecoration("getBuildPlateNumber")
            if filter_current_build_plate and node_build_plate_number != active_build_plate_number:
                continue

            if not node.callDecoration("isGroup"):
                name = node.getName()
            else:
                name = catalog.i18nc("@label", "Group #{group_nr}").format(group_nr = str(group_nr))
                group_nr += 1

            if hasattr(node, "isOutsideBuildArea"):
                is_outside_build_area = node.isOutsideBuildArea()
            else:
                is_outside_build_area = False

            nodes.append({
                "name": name,
                "isSelected": Selection.isSelected(node),
                "isOutsideBuildArea": is_outside_build_area,
                "buildPlateNumber": node_build_plate_number,
                "node": node
            })
        nodes = sorted(nodes, key=lambda n: n["name"])
        self.setItems(nodes)

        self.itemsChanged.emit()

    @staticmethod
    def createObjectsModel():
        return ObjectsModel()

    ##  Check if none of the model's stacks contain error states
    #   The setting applied for the settings per model
    def stacksHaveErrors(self) -> bool:
        return bool(self._stacks_have_errors)

    def setStacksHaveErrors(self, value):
        self._stacks_have_errors = value