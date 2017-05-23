if __name__ == "__main__":
    import sys
    sys.path.append('../plugin/python/')
import unittest2 as unittest
import vdebug.dbgp
import xml.etree.ElementTree as ET

class ContextPropertyDefaultTest(unittest.TestCase):
    def __get_context_property(self,xml_string):
        xml = ET.fromstring(xml_string)
        firstnode = xml[0]
        return vdebug.dbgp.ContextProperty(firstnode)

    def test_single_property(self):
        prop = self.__get_context_property(\
            """<?xml version="1.0" encoding="iso-8859-1"?>
<response xmlns="urn:debugger_protocol_v1"
xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
command="context_get" transaction_id="3"
context="0"><property name="$argc" fullname="$argc"
address="39795424"
type="int"><![CDATA[4]]></property></response>""")

        self.assertEqual(prop.display_name,'$argc')
        self.assertEqual(prop.value,'4')
        self.assertEqual(prop.type,'int')
        self.assertEqual(prop.depth,0)
        self.assertIsNone(prop.size)
        self.assertFalse(prop.has_children)

    def test_undefined_property(self):
        prop = self.__get_context_property(\
            """<?xml version="1.0" encoding="iso-8859-1"?>
<response xmlns="urn:debugger_protocol_v1"
xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
command="context_get" transaction_id="3"
context="0"><property name="$uid"
fullname="$uid" type="uninitialized"></property></response>""")

        self.assertEqual(prop.display_name,'$uid')
        self.assertEqual(prop.value,'')
        self.assertEqual(prop.type,'uninitialized')
        self.assertEqual(prop.depth,0)
        self.assertIsNone(prop.size)
        self.assertFalse(prop.has_children)

    def test_child_properties(self):
        prop = self.__get_context_property(\
            """<?xml version="1.0" encoding="iso-8859-1"?>
<response xmlns="urn:debugger_protocol_v1"
xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
command="context_get" transaction_id="3"
context="0"><property name="$argv"
fullname="$argv" address="39794056" type="array"
children="1" numchildren="4" page="0"
pagesize="32"><property name="0" fullname="$argv[0]"
address="39794368" type="string" size="19"
encoding="base64"><![CDATA[L3Vzci9sb2NhbC9iaW4vY2FrZQ==]]></property><property
name="1" fullname="$argv[1]" address="39794640"
type="string" size="8"
encoding="base64"><![CDATA[VGRkLnRlc3Q=]]></property><property
name="2" fullname="$argv[2]" address="39794904"
type="string" size="8"
encoding="base64"><![CDATA[LS1zdGRlcnI=]]></property><property
name="3" fullname="$argv[3]" address="39795168"
type="string" size="3"
encoding="base64"><![CDATA[QWxs]]></property></property></response>""")

        self.assertEqual(prop.display_name,'$argv')
        self.assertEqual(prop.value,'')
        self.assertEqual(prop.type,'array')
        self.assertEqual(prop.depth,0)
        self.assertTrue(prop.has_children)
        self.assertEqual(prop.child_count(),4)

class ContextPropertyAltTest(unittest.TestCase):
    def __get_context_property(self,xml_string):
        xml = ET.fromstring(xml_string)
        firstnode = xml[0]
        return vdebug.dbgp.ContextProperty(firstnode)

    def test_single_property(self):
        prop = self.__get_context_property(\
            """<?xml version="1.0" encoding="iso-8859-1"?>
<response xmlns="urn:debugger_protocol_v1"
xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
command="context_get" transaction_id="3"
context="0"><property  type="int" children="0" size="0"><value><![CDATA[1]]></value><name encoding="base64"><![CDATA[bXl2YXI=
]]></name><fullname encoding="base64"><![CDATA[bXl2YXI=
]]></fullname></property></response>""")

        self.assertEqual(prop.display_name,'myvar')
        self.assertEqual(prop.value,'1')
        self.assertEqual(prop.type,'int')
        self.assertEqual(prop.depth,0)
        self.assertFalse(prop.has_children)

    def test_child_properties(self):
        prop = self.__get_context_property(\
            """<?xml version="1.0" encoding="utf-8"?>
<response xmlns="urn:debugger_protocol_v1" command="contex_get" context="0" transaction_id="13"><property  pagesize="10" numchildren="3" children="1" type="list" page="0" size="3"><property  type="int" children="0" size="0"><value><![CDATA[1]]></value><name encoding="base64"><![CDATA[WzBd
]]></name><fullname encoding="base64"><![CDATA[bXlsaXN0WzBd
]]></fullname></property><property  type="int" children="0" size="0"><value><![CDATA[2]]></value><name encoding="base64"><![CDATA[WzFd
]]></name><fullname encoding="base64"><![CDATA[bXlsaXN0WzFd
]]></fullname></property><property  type="int" children="0" size="0"><value><![CDATA[3]]></value><name encoding="base64"><![CDATA[WzJd
]]></name><fullname encoding="base64"><![CDATA[bXlsaXN0WzJd
]]></fullname></property><name encoding="base64"><![CDATA[bXlsaXN0
]]></name><fullname encoding="base64"><![CDATA[bXlsaXN0
]]></fullname></property></response>""")

        self.assertEqual(prop.display_name,'mylist')
        self.assertEqual(prop.value,'')
        self.assertEqual(prop.type,'list')
        self.assertEqual(prop.depth,0)
        self.assertTrue(prop.has_children)
        self.assertEqual(prop.child_count(),3)

    def test_string(self):
        prop = self.__get_context_property(\
            """<?xml version="1.0" encoding="utf-8"?>
<response xmlns="urn:debugger_protocol_v1" command="contex_get" context="0" transaction_id="13"><property  type="str" children="0" size="5"><value encoding="base64"><![CDATA[d29ybGQ=
]]></value><name encoding="base64"><![CDATA[b2JqX3Zhcg==
]]></name><fullname encoding="base64"><![CDATA[b2JqLm9ial92YXI=
]]></fullname></property></response>""")

        self.assertEqual(prop.display_name,'obj.obj_var')
        self.assertEqual(prop.value,'`world`')
        self.assertEqual(prop.type,'str')
        self.assertFalse(prop.has_children)

