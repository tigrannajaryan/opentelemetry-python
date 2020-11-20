# Copyright The OpenTelemetry Authors
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
# type: ignore

from os import environ
from unittest import TestCase
from unittest.mock import patch

from opentelemetry.configuration import Configuration
from opentelemetry.instrumentation.auto_instrumentation import components
from opentelemetry.sdk.resources import Resource


class Provider:
    def __init__(self, resource=None):
        self.processor = None
        self.resource = resource

    def add_span_processor(self, processor):
        self.processor = processor


class Processor:
    def __init__(self, exporter):
        self.exporter = exporter


class Exporter:
    def __init__(self, service_name):
        self.service_name = service_name

    def shutdown(self):
        pass


class OTLPExporter:
    pass


class TestTraceInit(TestCase):
    def setUp(self):
        super()
        self.get_provider_patcher = patch(
            "opentelemetry.instrumentation.auto_instrumentation.components.TracerProvider",
            Provider,
        )
        self.get_processor_patcher = patch(
            "opentelemetry.instrumentation.auto_instrumentation.components.BatchExportSpanProcessor",
            Processor,
        )
        self.set_provider_patcher = patch(
            "opentelemetry.trace.set_tracer_provider"
        )

        self.get_provider_mock = self.get_provider_patcher.start()
        self.get_processor_mock = self.get_processor_patcher.start()
        self.set_provider_mock = self.set_provider_patcher.start()

    def tearDown(self):
        super()
        self.get_provider_patcher.stop()
        self.get_processor_patcher.stop()
        self.set_provider_patcher.stop()

    # pylint: disable=protected-access
    def test_trace_init_default(self):
        environ["OTEL_SERVICE_NAME"] = "my-test-service"
        Configuration._reset()
        components.init_tracing({"zipkin": Exporter})

        self.assertEqual(self.set_provider_mock.call_count, 1)
        provider = self.set_provider_mock.call_args[0][0]
        self.assertIsInstance(provider, Provider)
        self.assertIsInstance(provider.processor, Processor)
        self.assertIsInstance(provider.processor.exporter, Exporter)
        self.assertEqual(
            provider.processor.exporter.service_name, "my-test-service"
        )

    def test_trace_init_otlp(self):
        environ["OTEL_SERVICE_NAME"] = "my-otlp-test-service"
        Configuration._reset()
        components.init_tracing({"otlp": OTLPExporter})

        self.assertEqual(self.set_provider_mock.call_count, 1)
        provider = self.set_provider_mock.call_args[0][0]
        self.assertIsInstance(provider, Provider)
        self.assertIsInstance(provider.processor, Processor)
        self.assertIsInstance(provider.processor.exporter, OTLPExporter)
        self.assertIsInstance(provider.resource, Resource)
        self.assertEqual(
            provider.resource.attributes.get("service.name"),
            "my-otlp-test-service",
        )
        del environ["OTEL_SERVICE_NAME"]
