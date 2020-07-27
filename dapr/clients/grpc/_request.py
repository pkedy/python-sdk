# -*- coding: utf-8 -*-

"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT License.
"""

from typing import Dict, Optional, Union

from google.protobuf.any_pb2 import Any as GrpcAny
from google.protobuf.message import Message as GrpcMessage

from dapr.clients.base import DEFAULT_JSON_CONTENT_TYPE
from dapr.clients.grpc._helpers import (
    MetadataDict,
    MetadataTuple,
    tuple_to_dict,
    to_bytes,
    to_str,
    unpack
)


class DaprRequest:
    def __init__(self, metadata: MetadataTuple = ()):
        self.metadata = metadata  # type: ignore

    @property
    def metadata(self) -> MetadataDict:
        """Returns headers tuple as a dict."""
        return self.get_metadata(as_dict=True)  # type: ignore

    @metadata.setter
    def metadata(self, val) -> None:
        if not isinstance(val, tuple):
            raise ValueError('val is not tuple')
        self._metadata = val

    def get_metadata(self, as_dict: bool = False) -> Union[MetadataDict, MetadataTuple]:
        if as_dict:
            return tuple_to_dict(self._metadata)
        return self._metadata


class InvokeServiceRequest(DaprRequest):
    """A request data representation for invoke_service API.

    This stores the request data with the proper serialization. This seralizes
    data to :obj:`google.protobuf.any_pb2.Any` if data is the type of protocol
    buffer message.

    Attributes:
        data (str, bytes, GrpcAny, GrpcMessage, optional): the serialized data
            for invoke_service request.
        content_type (str, optional): the content type of data which is valid
            only for bytes array data.
    """

    HTTP_METHODS = [
        'GET',
        'HEAD',
        'POST',
        'PUT',
        'DELETE',
        'CONNECT',
        'OPTIONS',
        'TRACE'
    ]

    def __init__(
            self,
            data: Union[str, bytes, GrpcAny, GrpcMessage, None] = None,
            content_type: Optional[str] = None):
        """Inits InvokeServiceRequestData with data and content_type.

        Args:
            data (bytes, str, or :obj:`google.protobuf.message.Message`): the data
                which is used for invoke_service request.
            content_type (str): the content_type of data when the data is bytes.
                The default content type is application/json.

        Raises:
            ValueError: data is not bytes or :obj:`google.protobuf.message.Message`.
        """
        super(InvokeServiceRequest, self).__init__(())

        self._content_type = content_type
        self._http_verb = None
        self._http_querystring: Dict[str, str] = {}

        self.set_data(data)

        # Set content_type to application/json type if content_type
        # is not given and date is bytes or str type.
        if not self.is_proto() and not content_type:
            self.content_type = DEFAULT_JSON_CONTENT_TYPE

    @property
    def http_verb(self) -> Optional[str]:
        return self._http_verb

    @http_verb.setter
    def http_verb(self, val: Optional[str]) -> None:
        if val not in self.HTTP_METHODS:
            raise ValueError(f'{val} is the invalid HTTP verb.')
        self._http_verb = val

    @property
    def http_querystring(self) -> Dict[str, str]:
        return self._http_querystring

    def is_http(self) -> bool:
        return hasattr(self, '_http_verb') and not (not self._http_verb)

    @property
    def proto(self) -> GrpcAny:
        return self._data

    def is_proto(self) -> bool:
        return hasattr(self, '_data') and self._data.type_url != ''

    def pack(self, val: Union[GrpcAny, GrpcMessage]) -> None:
        if isinstance(val, GrpcAny):
            self._data = val
        elif isinstance(val, GrpcMessage):
            self._data = GrpcAny()
            self._data.Pack(val)
        else:
            raise ValueError('invalid data type')
        self._content_type = None

    def unpack(self, message: GrpcMessage) -> None:
        """Unpack the serialized protocol buffer message.

        Args:
            message (:obj:`google.protobuf.message.Message`): the protocol buffer message object
                to which the response data is deserialized.

        Raises:
            ValueError: message is not protocol buffer message object or message's type is not
                matched with the response data type
        """
        unpack(self.proto, message)

    @property
    def data(self) -> bytes:
        if self.is_proto():
            raise ValueError('data is protocol buffer message object.')
        return self._data.value

    @data.setter
    def data(self, val: Union[str, bytes]) -> None:
        self.set_data(to_bytes(val))

    def set_data(self, val: Union[str, bytes, GrpcAny, GrpcMessage, None]) -> None:
        if val is None:
            self._data = GrpcAny()
        if isinstance(val, (bytes, str)):
            self._data = GrpcAny(value=to_bytes(val))
        elif isinstance(val, (GrpcAny, GrpcMessage)):
            self.pack(val)
        else:
            raise ValueError(f'invalid data type {type(val)}')

    def text(self) -> str:
        return to_str(self.data)

    @property
    def content_type(self) -> Optional[str]:
        return self._content_type

    @content_type.setter
    def content_type(self, val: Optional[str]) -> None:
        self._content_type = val


class BindingRequest(DaprRequest):
    """A request data representation for invoke_binding API.

    This stores the request data and metadata with the proper serialization.
    This seralizes data to bytes and metadata to a dictionary of key value pairs.

    Attributes:
        data (bytes): the data which is used for invoke_binding request.
        metadata (Dict[str, str]): the metadata sent to the binding.
    """
    def __init__(
            self,
            data: Union[str, bytes],
            binding_metadata: Dict[str, str] = {}):
        """Inits BindingRequest with data and metadata if given.

        Args:
            data (bytes, str): the data which is used for invoke_binding request.
            binding_metadata (tuple, optional): the metadata to be sent to the binding.

        Raises:
            ValueError: data is not bytes or str.
        """
        super(BindingRequest, self).__init__(())
        self.data = data   # type: ignore
        self._binding_metadata = binding_metadata

    @property
    def data(self) -> bytes:
        return self._data

    @data.setter
    def data(self, val: Union[str, bytes]) -> None:
        self._data = to_bytes(val)

    def text(self) -> str:
        return to_str(self.data)

    @property
    def binding_metadata(self):
        return self._binding_metadata
