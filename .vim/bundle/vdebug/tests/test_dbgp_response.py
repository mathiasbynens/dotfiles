import sys
if __name__ == "__main__":
    sys.path.append('../plugin/python/')
import unittest2 as unittest
import vdebug.dbgp
import xml
from mock import Mock

class ResponseTest(unittest.TestCase): 
    """Test the response class in the vdebug.dbgp module."""

    def test_get_cmd(self):
        """Test that the get_cmd() method returns the command"""
        cmd = "status"
        res = vdebug.dbgp.Response("",cmd,"",Mock())
        assert res.get_cmd() == cmd

    def test_get_cmd_args(self):
        """Test that the get_cmd_args() method return command arguments"""
        cmd_args = "-a abcd"
        res = vdebug.dbgp.Response("","",cmd_args,Mock())
        assert res.get_cmd_args() == cmd_args

    def test_as_string(self):
        """Test that the as_string() method returns the
        raw response string"""
        response = "<?xml..."
        res = vdebug.dbgp.Response(response,"","",Mock())
        assert res.as_string() == response

    def test_as_xml_is_element(self):
        if sys.version_info < (2, 7):
            return
        """Test that the as_xml() method returns an XML
        element"""
        response = """<?xml version="1.0" encoding="iso-8859-1"?>
            <response xmlns="urn:debugger_protocol_v1"
            xmlns:xdebug="http://xdebug.org/dbgp/xdebug" 
            command="status" transaction_id="1" status="starting" 
            reason="ok"></response>"""
        res = vdebug.dbgp.Response(response,"","",Mock())
        self.assertIsInstance(res.as_xml(),xml.etree.ElementTree.Element)

    def test_error_tag_raises_exception(self):
        response = """<?xml version="1.0" encoding="iso-8859-1"?>
            <response xmlns="urn:debugger_protocol_v1" 
            xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
            command="stack_get" transaction_id="4"><error
            code="5"><message><![CDATA[command is not available]]>
            </message></error></response>"""
        re = "command is not available"
        self.assertRaisesRegexp(vdebug.dbgp.DBGPError,re,vdebug.dbgp.Response,response,"","",Mock())

class StatusResponseTest(unittest.TestCase): 
    """Test the behaviour of the StatusResponse class."""
    def test_string_is_status_text(self):
        response = """<?xml version="1.0" encoding="iso-8859-1"?>
            <response xmlns="urn:debugger_protocol_v1"
            xmlns:xdebug="http://xdebug.org/dbgp/xdebug" 
            command="status" transaction_id="1" status="starting" 
            reason="ok"></response>"""
        res = vdebug.dbgp.StatusResponse(response,"","",Mock())
        assert str(res) == "starting"

class FeatureResponseTest(unittest.TestCase): 
    """Test the behaviour of the FeatureResponse class."""
    def test_feature_is_supported(self):
        response = """<?xml version="1.0" encoding="iso-8859-1"?>
            <response xmlns="urn:debugger_protocol_v1" 
            xmlns:xdebug="http://xdebug.org/dbgp/xdebug" 
            command="feature_get" transaction_id="2" 
            feature_name="max_depth" supported="1"><![CDATA[1]]></response>"""
        res = vdebug.dbgp.FeatureGetResponse(response,"","",Mock())
        assert res.is_supported() == 1

    def test_feature_is_not_supported(self):
        response = """<?xml version="1.0" encoding="iso-8859-1"?>
            <response xmlns="urn:debugger_protocol_v1" 
            xmlns:xdebug="http://xdebug.org/dbgp/xdebug" 
            command="feature_get" transaction_id="2" 
            feature_name="max_depth" supported="0"><![CDATA[0]]></response>"""
        res = vdebug.dbgp.FeatureGetResponse(response,"","",Mock())
        assert res.is_supported() == 0

class StackGetTest(unittest.TestCase): 
    """Test the behaviour of the StackGetResponse class."""
    def test_string_is_status_text(self):
        response = """<?xml version="1.0" encoding="iso-8859-1"?>
            <response xmlns="urn:debugger_protocol_v1" 
            xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
            command="stack_get" transaction_id="8">
                <stack where="{main}" level="0" type="file"
                filename="file:///usr/local/bin/cake" lineno="4">
                </stack>
            </response>"""
        res = vdebug.dbgp.StackGetResponse(response,"","",Mock())
        stack = res.get_stack()
        assert stack[0].get('filename') == "file:///usr/local/bin/cake"
        assert len(stack) == 1

class ContextGetTest(unittest.TestCase):
    response = """<?xml version="1.0" encoding="iso-8859-1"?>
<response xmlns="urn:debugger_protocol_v1"
xmlns:xdebug="http://xdebug.org/dbgp/xdebug"
command="context_get" transaction_id="3"
context="0"><property name="$argc" fullname="$argc"
address="39795424"
type="int"><![CDATA[4]]></property><property name="$argv"
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
encoding="base64"><![CDATA[QWxs]]></property></property><property
name="$cdstring" fullname="$cdstring"
type="uninitialized"></property><property name="$cdup"
fullname="$cdup" type="uninitialized"></property><property
name="$cwd" fullname="$cwd"
type="uninitialized"></property><property name="$dir"
fullname="$dir" type="uninitialized"></property><property
name="$dirs" fullname="$dirs"
type="uninitialized"></property><property name="$f"
fullname="$f" type="uninitialized"></property><property
name="$f_parts" fullname="$f_parts"
type="uninitialized"></property><property name="$f_user"
fullname="$f_user"
type="uninitialized"></property><property name="$i"
fullname="$i" type="uninitialized"></property><property
name="$idx" fullname="$idx"
type="uninitialized"></property><property name="$op"
fullname="$op" type="uninitialized"></property><property
name="$pass" fullname="$pass"
type="uninitialized"></property><property
name="$require_chown" fullname="$require_chown"
type="uninitialized"></property><property name="$retval"
fullname="$retval"
type="uninitialized"></property><property name="$tmp_files"
fullname="$tmp_files"
type="uninitialized"></property><property name="$uid"
fullname="$uid" type="uninitialized"></property><property
name="$user" fullname="$user"
type="uninitialized"></property></response>
"""

    def test_properties_are_objects(self):
        res = vdebug.dbgp.ContextGetResponse(self.response,"","",Mock())
        context = res.get_context()
        assert len(context) == 23
        self.assertIsInstance(context[0],vdebug.dbgp.ContextProperty)

    def test_int_property_attributes(self):
        res = vdebug.dbgp.ContextGetResponse(self.response,"","",Mock())
        context = res.get_context()
        prop = context[0]

        assert prop.display_name == "$argc"
        assert prop.type == "int"
        assert prop.value == "4"
        assert prop.has_children == False

    def test_array_property_attributes(self):
        res = vdebug.dbgp.ContextGetResponse(self.response,"","",Mock())
        context = res.get_context()
        prop = context[1]

        assert prop.display_name == "$argv"
        assert prop.type == "array"
        assert prop.value == ""
        assert prop.has_children == True
        assert prop.child_count() == 4

    def test_string_property_attributes(self):
        res = vdebug.dbgp.ContextGetResponse(self.response,"","",Mock())
        context = res.get_context()
        prop = context[2]

        assert prop.display_name == "$argv[0]"
        assert prop.type == "string"
        assert prop.value == "`/usr/local/bin/cake`"
        assert prop.has_children == False
        assert prop.size == "19"

class ContextGetAlternateTest(unittest.TestCase):
    response = """<?xml version="1.0" encoding="utf-8"?>
<response xmlns="urn:debugger_protocol_v1" command="context_get" context="0" transaction_id="15"><property  pagesize="10" numchildren="3" children="1" type="list" page="0" size="3"><name encoding="base64"><![CDATA[bXlsaXN0
]]></name><fullname encoding="base64"><![CDATA[bXlsaXN0
]]></fullname></property><property  type="int" children="0" size="0"><value><![CDATA[1]]></value><name encoding="base64"><![CDATA[bXl2YXI=
]]></name><fullname encoding="base64"><![CDATA[bXl2YXI=
]]></fullname></property><property  pagesize="10" numchildren="4" children="1" type="Example" page="0" size="0"><name encoding="base64"><![CDATA[b2Jq
]]></name><fullname encoding="base64"><![CDATA[b2Jq
]]></fullname></property></response>"""

    def test_properties_are_objects(self):
        res = vdebug.dbgp.ContextGetResponse(self.response,"","",Mock())
        context = res.get_context()
        assert len(context) == 3
        self.assertIsInstance(context[0],vdebug.dbgp.ContextProperty)

