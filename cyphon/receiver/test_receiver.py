# -*- coding: utf-8 -*-
# Copyright 2017 Dunbar Security Solutions, Inc.
#
# This file is part of Cyphon Engine.
#
# Cyphon Engine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# Cyphon Engine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cyphon Engine. If not, see <http://www.gnu.org/licenses/>.
"""
Tests the receiver module.
"""

# standard library
from collections import OrderedDict
import json
import logging
from unittest.mock import Mock, patch

# third party
from django.test import TransactionTestCase
from testfixtures import LogCapture

# local
from receiver.receiver import process_msg, LOGGER
from tests.fixture_manager import get_fixtures

LOGGER.removeHandler('console')


class ProcessMsgTestCase(TransactionTestCase):
    """
    Tests the process_msg function.
    """

    fixtures = get_fixtures(['logchutes'])

    default_munger = 'default_log'

    mock_doc_obj = Mock()
    mock_method = Mock()
    mock_method.routing_key = 'logchutes'

    doc = {
        'message': 'foobar',
        '@uuid': '12345',
        'collection': 'elasticsearch.test_index.test_logs'
    }
    sorted_doc = OrderedDict(sorted(doc.items()))
    msg = bytes(json.dumps(sorted_doc), 'utf-8')
    decoded_msg = msg.decode('utf-8')

    def setUp(self):
        logging.disable(logging.ERROR)
        self.kwargs = {
            'channel': None,
            'method': self.mock_method,
            'properties': None,
            'body': self.msg
        }

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @patch('receiver.receiver.LogChute.objects.process')
    def test_process_msg_logchutes(self, mock_process):
        """
        Tests the process_msg function for LogChutes.
        """
        self.kwargs['method'].routing_key = 'logchutes'
        with patch('receiver.receiver._create_doc_obj',
                   return_value=self.mock_doc_obj) as mock_create:
            process_msg(**self.kwargs)
            mock_create.assert_called_once_with(self.decoded_msg)
            mock_process.assert_called_once_with(self.mock_doc_obj)

    @patch('receiver.receiver.DataChute.objects.process')
    def test_process_msg_datachutes(self, mock_process):
        """
        Tests the process_msg function for DataChutes.
        """
        self.kwargs['method'].routing_key = 'datachutes'
        with patch('receiver.receiver._create_doc_obj',
                   return_value=self.mock_doc_obj) as mock_create:
            process_msg(**self.kwargs)
            mock_create.assert_called_once_with(self.decoded_msg)
            mock_process.assert_called_once_with(self.mock_doc_obj)

    @patch('receiver.receiver.Watchdog.objects.process')
    def test_process_msg_watchdogs(self, mock_process):
        """
        Tests the process_msg function for Watchdogs.
        """
        self.kwargs['method'].routing_key = 'watchdogs'
        with patch('receiver.receiver._create_doc_obj',
                   return_value=self.mock_doc_obj) as mock_create:
            process_msg(**self.kwargs)
            mock_create.assert_called_once_with(self.decoded_msg)
            mock_process.assert_called_once_with(self.mock_doc_obj)

    @patch('receiver.receiver.Monitor.objects.process')
    def test_process_msg_monitors(self, mock_process):
        """
        Tests the process_msg function for Monitors.
        """
        self.kwargs['method'].routing_key = 'monitors'
        with patch('receiver.receiver._create_doc_obj',
                   return_value=self.mock_doc_obj) as mock_create:
            process_msg(**self.kwargs)
            mock_create.assert_called_once_with(self.decoded_msg)
            mock_process.assert_called_once_with(self.mock_doc_obj)

    def test_process_msg_exception(self):
        """
        Tests the process_msg function when an exception is raised.
        """
        logging.disable(logging.NOTSET)
        with patch('receiver.receiver.logging.getLogger', return_value=LOGGER):
            with patch('receiver.receiver.json.loads', side_effect=Exception('foo')):
                with LogCapture() as log_capture:
                    process_msg(**self.kwargs)
                    log_capture.check(
                        ('receiver',
                         'ERROR',
                         'An error occurred while processing the message \'{"@uuid": "12345", '
                         '"collection": "elasticsearch.test_index.test_logs", "message": '
                         '"foobar"}\':\n'
                         '  foo'),
                    )
