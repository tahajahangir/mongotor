# coding: utf-8
# <mongotor - An asynchronous driver and toolkit for accessing MongoDB with Tornado>
# Copyright (C) <2012>  Marcel Nicolay <marcel.nicolay@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import logging
import six
from tornado import gen
from mongotor.client import Client
from mongotor.orm.field import Field
from mongotor.orm.signal import (pre_save, post_save,
    pre_remove, post_remove, pre_update, post_update)
from mongotor.orm.manager import Manager
from mongotor.database import Database


logger = logging.getLogger(__name__)
__lazy_classes__ = {}


class CollectionMetaClass(type):

    def __new__(cls, name, bases, attrs):
        if not attrs.get('__collection__'):
            attrs['__collection__'] = re.sub(
                r'\B([A-Z]+)', r'_\1', name).lower()
        global __lazy_classes__

        fields_name_to_attr = attrs['_fields_name_to_attr'] = {}
        # Add the document's fields to the _data
        for attr_name, attr_value in six.iteritems(attrs):
            if isinstance(attr_value, Field):
                if attr_value.name is None:
                    attr_value.name = attr_name
                else:
                    fields_name_to_attr[attr_value.name] = attr_name

        new_class = super(CollectionMetaClass, cls).__new__(cls, name,
            bases, attrs)

        __lazy_classes__[name] = new_class

        new_class.objects = Manager(collection=new_class)

        return new_class


@six.add_metaclass(CollectionMetaClass)
class Collection(object):
    """Collection is the base class

    This class map a mongo collection into a python class.
    You only need to write a class and starts to use the orm advantages.

    For example, a simple users collection can be mapping
    using:

    >>> from mongotor.orm import collection, field
    >>> class Users(collection.Collection):
    >>>     __collection__ = 'users'
    >>>     name = field.StringField()

    If you do not specify `__collection__` attribute, it is
    auto-generated from class name. Camel case is converted
    to snake case. For example: CamelCase -> camel_case.
    """
    _fields_name_to_attr = {}  # maps field database name to field attr name
                               # will be filled in metaclass

    def __new__(cls, class_name=None, *args, **kwargs):
        if class_name:
            global __lazy_classes__
            return __lazy_classes__.get(class_name)

        return super(Collection, cls).__new__(cls, *args, **kwargs)

    def __init__(self):
        self._data = {}
        self._dirty = set()

    def as_dict(self, fields=None):
        items = {}
        fields = fields or []
        iteritems = six.iteritems(self.__class__.__dict__)
        if fields:
            iteritems = ((k,v) for k,v in iteritems if k in fields)

        for attr_name, attr_type in iteritems:
            if isinstance(attr_type, Field):
                attr_value = getattr(self, attr_name)
                if attr_value is not None:
                    items[attr_type.name] = attr_value

        # Gets the fields from base classes when fields are None so we only
        # get the dirty fields when we only want to update those.
        if not fields:
            for cls in self.__class__.__mro__:
                for attr_name, attr_type in six.iteritems(cls.__dict__):
                    if isinstance(attr_type, Field):
                        attr_value = getattr(self, attr_name)
                        if attr_value is not None:
                            items[attr_type.name] = attr_value

        return items

    @property
    def dirty_fields(self):
        return list(self._dirty)

    def clean_fields(self):
        self._dirty = set()

    @classmethod
    def create(cls, dictionary, cleaned=False):
        """Create a new instance of collection from a dictionary

        For example, creating a new instance from a mapped collection
        Users:

        >>> user = Users.create({'name': 'should be name'})
        >>> assert user.name == 'should be name'
        """
        instance = cls()
        for (key, value) in six.iteritems(dictionary):
            try:
                setattr(instance, cls._fields_name_to_attr.get(key, key), value)
            except TypeError as e:
                logger.warn(e)

        if cleaned:
            instance.clean_fields()

        return instance

    def get_client(self):
        return Client(Database(), self.__collection__)

    @gen.coroutine
    def save(self, safe=True, check_keys=True):
        """Save a document

        >>> user = Users()
        >>> user.name = 'should be name'
        >>> user.save()

        :Parameters:
          - `safe` (optional): safe insert operation
          - `check_keys` (optional): check if keys start with '$' or
            contain '.', raising :class:`~pymongo.errors.InvalidName`
            in either case
        - `callback` : method which will be called when save is finished
        """
        pre_save.send(instance=self)

        client = self.get_client()
        response, error = yield gen.Task(client.insert, self.as_dict(),
            safe=safe, check_keys=check_keys)

        self.clean_fields()

        post_save.send(instance=self)

        raise gen.Return((response, error))

    @gen.coroutine
    def remove(self, safe=True):
        """Remove a document

        :Parameters:
        - `safe` (optional): safe remove operation
        - `callback` : method which will be called when remove is finished
        """
        pre_remove.send(instance=self)

        client = self.get_client()
        response, error = yield gen.Task(client.remove, self._id, safe=safe)

        post_remove.send(instance=self)

        raise gen.Return((response, error))

    @gen.coroutine
    def update(self, document=None, upsert=False, safe=True, multi=False, force=False):
        """Update a document

        :Parameters:
        - `safe` (optional): safe update operation
        - `callback` : method which will be called when update is finished
        - `force`: if True will overide full document
        """
        if not document and not self.dirty_fields:
            raise gen.Return(tuple())

        pre_update.send(instance=self)

        if not document:
            if force:
                document = self.as_dict()
            else:
                document = {"$set": self.as_dict(self.dirty_fields)}

        client = self.get_client()
        spec = {'_id': self._id}

        response, error = yield gen.Task(client.update, spec, document,
            upsert=upsert, safe=safe, multi=multi)

        self.clean_fields()

        post_update.send(instance=self)

        raise gen.Return((response, error))
