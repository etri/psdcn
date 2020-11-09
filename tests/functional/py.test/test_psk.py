"""
psk_cmd tests
"""

import pytest
import sys
sys.path.append("../../..")

from ndn.app import NDNApp
from psdcnv2.psk.pskinfo import *
from psdcnv2.psk.pskcmd import PSKCmd

class TestPskCmd:
    @staticmethod
    def test_psk_pubadv_cmd():
        prefix = "/rn"
        dataname = "/test/a/b/c"
        name = "/rn/PA/test/a/b/c"

        app = NDNApp()
        psk = PSKCmd(app)

        pubadvinfo = PubAdvInfo('broker', '/etri/bld7/room385/temp', False, 0)
        irinfo = IRInfo('1234', '/etri/bld7/room385/temp', "prod1234", 0.01, 
                        '2020-01-01', '2020-12-31',  'keyword', 'origin', 'region', 'desc')
        rninfo = RNInfo('RN-001')
                    
        command, i_param, a_param = psk.make_pubadv_cmd(prefix, dataname, pubadvinfo, irinfo, rninfo)

        assert name == command


    @staticmethod
    def test_psk_pubunadv_cmd():
        prefix = "/rn"
        dataname = "/test/a/b/c"
        name = "/rn/PU/test/a/b/c"

        app = NDNApp()
        psk = PSKCmd(app)

        pubadvinfo = PubAdvInfo('broker', '/etri/bld7/room385/temp', False, 0)
                    
        command, i_param, a_param = psk.make_pubunadv_cmd(prefix, dataname, pubadvinfo)

        assert name == command


    @staticmethod
    def test_psk_pubdata_cmd():
        prefix = "/rn"
        dataname = "/test/a/b/c"
        seq = 10
        name = "/rn/PD/test/a/b/c/10"

        app = NDNApp()
        psk = PSKCmd(app)

        pubdatainfo = PubDataInfo("test data", 1, 10)
                    
        command, i_param, a_param = psk.make_pubdata_cmd(prefix, dataname, seq, pubdatainfo)

        assert name == command


    @staticmethod
    def test_psk_subtopic_cmd():
        prefix = "/rn"
        dataname = "/test/a/b/c"
        name = "/rn/ST/test/a/b/c"

        app = NDNApp()
        psk = PSKCmd(app)

        subinfo = SubInfo()
                    
        command, i_param, a_param = psk.make_subtopic_cmd(prefix, dataname, subinfo)

        assert name == command


    @staticmethod
    def test_psk_submani_cmd():
        prefix = "/rn"
        dataname = "/test/a/b/c"
        name = "/rn/SM/test/a/b/c"

        app = NDNApp()
        psk = PSKCmd(app)

        command, i_param, a_param = psk.make_submani_cmd(prefix, dataname)

        assert name == command


    @staticmethod
    def test_psk_subdata_cmd():
        prefix = "/rn"
        dataname = "/test/a/b/c"
        seq = 10
        name = "/rn/SD/test/a/b/c/10"

        app = NDNApp()
        psk = PSKCmd(app)

        command, i_param, a_param = psk.make_subdata_cmd(prefix, dataname, seq)

        assert name == command


    @staticmethod
    def test_psk_irreg_cmd():
        prefix = "/ir"
        dataname = "/test/a/b/c"
        raw_packet = bytearray(100)
        name = "/ir/MR/test/a/b/c"

        app = NDNApp()
        psk = PSKCmd(app)

        command, i_param, a_param = psk.make_irreg_cmd(prefix, dataname, raw_packet)

        assert name == command


    @staticmethod
    def test_psk_irdel_cmd():
        prefix = "/ir"
        dataname = "/test/a/b/c"
        raw_packet = bytearray(100)
        name = "/ir/MD/test/a/b/c"

        app = NDNApp()
        psk = PSKCmd(app)

        command, i_param, a_param = psk.make_irdel_cmd(prefix, dataname, raw_packet)

        assert name == command

