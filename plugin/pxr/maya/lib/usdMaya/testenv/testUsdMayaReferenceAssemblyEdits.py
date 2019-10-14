#!/pxrpythonsubst
#
# Copyright 2017 Pixar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from pxr import UsdMaya

import mayaUsd.lib as mayaUsdLib

from pxr import Sdf

from maya import cmds
from maya import standalone

import os
import unittest


class testUsdMayaReferenceAssemblyEdits(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        standalone.initialize('usd')
        cmds.loadPlugin('pxrUsd')

    @classmethod
    def tearDownClass(cls):
        standalone.uninitialize()

    def setUp(self):
        cmds.file(new=True, force=True)

    @staticmethod
    def _CreateAssemblyNode(nodeName='TestAssemblyNode'):
        """
        Creates a model reference assembly node for testing.
        """
        ASSEMBLY_TYPE_NAME = 'pxrUsdReferenceAssembly'
        assetName = 'CubeModel'
        usdFile = os.path.abspath('%s.usda' % assetName)
        primPath = '/%s' % assetName

        assemblyNodeName = cmds.assembly(name=nodeName, type=ASSEMBLY_TYPE_NAME)
        cmds.setAttr('%s.filePath' % assemblyNodeName, usdFile, type='string')
        cmds.setAttr('%s.primPath' % assemblyNodeName, primPath, type='string')

        return assemblyNodeName

    def _GetAssemblyEdit(self, assemblyNodeName, editPath):
        """
        Gets the assembly edit on the USD prim at editPath for the Maya assembly
        node assemblyNodeName.
        It is assumed that there is only ever one edit per editPath, and no
        invalid edits.
        """
        (assemEdits, invalidEdits) = mayaUsdLib.EditUtil.GetEditsForAssembly(
            assemblyNodeName)
        self.assertEqual(len(assemEdits), 1)
        self.assertEqual(invalidEdits, [])

        self.assertIn(editPath, assemEdits)
        self.assertEqual(len(assemEdits[editPath]), 1)

        refEdit = assemEdits[editPath][0]
        return refEdit

    def _MakeAssemblyEdit(self, assemblyNodeName, editNodeName):
        """
        Creates an assembly edit on the Maya node editNodeName inside the Maya
        assembly assemblyNodeName.
        """
        editNode = 'NS_%s:%s' % (assemblyNodeName, editNodeName)
        editAttr = '%s.tx' % editNode
        cmds.setAttr(editAttr, 5.0)

        # Verify that the edit was made correctly.
        editPath = Sdf.Path('Geom/%s' % editNodeName)
        refEdit = self._GetAssemblyEdit(assemblyNodeName, editPath)

        expectedEditString = 'setAttr "NS_{nodeName}:Geom|NS_{nodeName}:Cube.translateX" 5'.format(
            nodeName=assemblyNodeName)
        self.assertEqual(refEdit.editString, expectedEditString)

    def testAssemblyEditsAfterRename(self):
        """
        Tests that assembly edits made prior to a rename are still present on
        the assembly after it has been renamed.
        """
        # Create the initial assembly and activate its 'Full' representation.
        assemblyNodeName = self._CreateAssemblyNode()
        cmds.assembly(assemblyNodeName, edit=True, active='Full')

        # Make an edit on a node inside the assembly.
        self._MakeAssemblyEdit(assemblyNodeName, 'Cube')

        # Now do the rename.
        cmds.rename(assemblyNodeName, 'FooBar')

        editPath = Sdf.Path('Geom/Cube')

        # Because the rename does not change the 'repNamespace' attribute on
        # the assembly, it should still be the same as it was before the rename.
        refEdit = self._GetAssemblyEdit('FooBar', editPath)
        expectedEditString = 'setAttr "NS_TestAssemblyNode:Geom|NS_TestAssemblyNode:Cube.translateX" 5'
        self.assertEqual(refEdit.editString, expectedEditString)

    # XXX: Maya's built-in duplicate() command does NOT copy assembly edits.
    #      Hopefully one day it will, and we can enable this test.
    # def testAssemblyEditsAfterDuplicate(self):
    #     """
    #     Tests that assembly edits made on an assembly node are preserved on the
    #     original node AND transferred to the duplicate node correctly when the
    #     original node is duplicated.
    #     """
    #     # Create the initial assembly and activate its 'Full' representation.
    #     assemblyNodeName = self._CreateAssemblyNode()
    #     cmds.assembly(assemblyNodeName, edit=True, active='Full')
    #
    #     # Make an edit on a node inside the assembly.
    #     self._MakeAssemblyEdit(assemblyNodeName, 'Cube')
    #
    #     # Now do the duplicate.
    #     cmds.duplicate(assemblyNodeName, name='DuplicateAssembly')
    #
    #     editPath = Sdf.Path('Geom/Cube')
    #
    #     # Verify the edit on the original assembly node.
    #     refEdit = self._GetAssemblyEdit(assemblyNodeName, editPath)
    #     expectedEditString = 'setAttr "NS_{nodeName}:Geom|NS_{nodeName}:Cube.translateX" 5'.format(
    #         nodeName=assemblyNodeName)
    #     self.assertEqual(refEdit.editString, expectedEditString)
    #
    #     # Verify the edit on the duplicate assembly node.
    #     refEdit = self._GetAssemblyEdit('DuplicateAssembly', editPath)
    #     expectedEditString = 'setAttr "NS_{nodeName}:Geom|NS_{nodeName}:Cube.translateX" 5'.format(
    #         nodeName='DuplicateAssembly')
    #     self.assertEqual(refEdit.editString, expectedEditString)


if __name__ == '__main__':
    unittest.main(verbosity=2)
